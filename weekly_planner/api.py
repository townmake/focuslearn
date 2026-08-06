from datetime import datetime, date, timedelta
from rest_framework import viewsets, permissions, status, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils import dateparse
from .models import TaskList, Task, Subject, Chapter, DailySummary, Words
from .serializers import (  # 使用括号和逗号分隔
    TaskListSerializer, 
    TaskSerializer, 
    SubjectSerializer, 
    ChapterSerializer, 
    DailySummarySerializer, 
    TaskBulkSerializer,
    WordsSerializer
)
from django.db import transaction
from django.db.models import Q

from .task_reminder_service import (
    refresh_important_date_from_task_if_linked,
    sync_task_important_reminder,
)
from courses.models import StudyRecord


def _parse_iso_datetime_for_study_record(datetime_str):
    if not datetime_str:
        return None
    try:
        dt = dateparse.parse_datetime(str(datetime_str))
        if dt is None:
            return None
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt)
        return dt.replace(microsecond=0)
    except Exception:
        return None


def _request_sync_important_reminder(request):
    v = request.data.get("sync_important_reminder", False)
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.strip().lower() in ("true", "1", "yes", "on")
    return bool(v)


class IsOwner(permissions.BasePermission):
    """
    自定义权限，只允许对象的所有者访问
    """
    def has_object_permission(self, request, view, obj):
        # 检查对象的用户是否与请求用户相同
        return obj.user == request.user

# 任务列表的API，暂时没用到
class TaskListViewSet(viewsets.ModelViewSet):
    """
    任务列表的API视图集
    """
    serializer_class = TaskListSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return TaskList.objects.filter(user=self.request.user)


        

class TaskViewSet(viewsets.ModelViewSet):
    """
    任务的API视图集
    """
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    # def safe_convert(self, value, convert_func=str):
    #     """
    #     安全地转换数据类型
    #     :param value: 输入值
    #     :param convert_func: 转换函数，默认为str
    #     :return: 转换后的值或None
    #     """
    #     if value is None:
    #         return None
    #     try:
    #         # 如果已经是期望的类型，直接返回
    #         if isinstance(value, convert_func.__class__):
    #             return value
            
    #         # 尝试转换
    #         converted = convert_func(value)
    #         return converted.strip() if isinstance(converted, str) else converted
    #     except (ValueError, TypeError):
    #         print(f"无法转换值: {value}")
    #         return None
    # 获取任务列表的数据，可设定时间范围
    def get_queryset(self):
        queryset = Task.objects.filter(user=self.request.user).select_related("subject")

        subject_raw = self.request.query_params.get("subject")
        chapter_raw = self.request.query_params.get("chapter")
        subject_id = None
        chapter_id = None
        if subject_raw not in (None, ""):
            try:
                subject_id = int(subject_raw)
            except (TypeError, ValueError):
                subject_id = None
        if chapter_raw not in (None, ""):
            try:
                chapter_id = int(chapter_raw)
            except (TypeError, ValueError):
                chapter_id = None

        def _apply_subject_chapter(qs):
            if subject_id is not None:
                qs = qs.filter(subject_id=subject_id)
            if chapter_id is not None:
                qs = qs.filter(chapter_id=chapter_id)
            return qs

        unscheduled = self.request.query_params.get('unscheduled')
        if unscheduled in ('1', 'true', 'yes'):
            return _apply_subject_chapter(queryset).filter(
                is_unscheduled=True, is_completed=False
            ).order_by('-created_at')

        # 详情/更新/删除/自定义 action 需能访问待安排任务；列表排除待安排（由周历拉取）
        if getattr(self, 'action', None) != 'list':
            return _apply_subject_chapter(queryset)

        queryset = queryset.exclude(is_unscheduled=True)
        queryset = _apply_subject_chapter(queryset)

        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)

        if start_date and end_date:
            queryset = queryset.filter(
                end_date__gte=start_date,
                start_date__lte=end_date,
            )

        return queryset
    def _parse_date(self, date_str):
        """
        安全地解析日期字符串
        """
        try:
            # 尝试直接解析为日期对象
            if isinstance(date_str, date):
                return date_str
            
            # 尝试多种日期格式
            try:
                # ISO 格式
                return datetime.fromisoformat(date_str).date()
            except ValueError:
                try:
                    # 尝试其他常见格式
                    return datetime.strptime(date_str, "%Y-%m-%d").date()
                except ValueError:
                    # 如果仍然解析失败，返回当前日期
                    print(f"无法解析日期: {date_str}")
                    return timezone.now().date()
        except Exception as e:
            print(f"日期解析错误: {str(e)}")
            return timezone.now().date()
        

    def perform_create(self, serializer):
        # 验证科目和章节是否存在
        subject = get_object_or_404(
            Subject,
            id=self.request.data.get('subject')
        )
        chapter = get_object_or_404(
            Chapter,
            id=self.request.data.get('chapter'),
            subject=subject
        )
        
        # 创建主任务
        task = serializer.save(
            user=self.request.user,
            subject=subject,
            chapter=chapter
        )

        from courses.subject_heat import bump_heat_after_task_create
        bump_heat_after_task_create(task.subject_id)

        if task.is_unscheduled:
            sync_task_important_reminder(task, _request_sync_important_reminder(self.request))
            return

        # 处理重复任务的批量创建
        if (task.repeat_type == 'daily' or task.repeat_type == 'weekly'or task.repeat_type == 'monthly'):
            # 使用事务确保原子性
            with transaction.atomic():
                # 将自身设置为parent_series
                task.parent_series = task
                task.save()
                
                if task.repeat_type == 'daily':
                    day_durant=1
                elif task.repeat_type == 'monthly':
                    day_durant=30
                else:
                    day_durant=7
                    

                # 创建重复任务
                created_tasks = []
                instance_start = task.start_date + timedelta(days=day_durant) 
                instance_end = task.end_date + timedelta(days=day_durant)
                
                # 确保 creat_end_date 是 date 类型
                if task.repeat_ends:
                    # 额外的类型转换保护
                    creat_end_date = task.repeat_ends.date() if hasattr(task.repeat_ends, 'date') else task.repeat_ends
                else:
                    creat_end_date = timezone.now().date() + timedelta(days=60)
                
                while instance_start <= creat_end_date:
                    
                    repeated_task = Task(
                        user=task.user,
                        parent_series=task,  # 所有重复任务的parent_series都指向第一个任务
                        title=task.title,
                        description=task.description,
                        subject=task.subject,
                        chapter=task.chapter,
                        focus_level=task.focus_level,
                        energy_level=task.energy_level,
                        urgency_level=task.urgency_level,
                        importance_level=task.importance_level,
                        start_time=task.start_time,
                        end_time=task.end_time,
                        start_date=instance_start,
                        end_date=instance_end,
                        repeat_type=task.repeat_type,
                        repeat_ends=task.repeat_ends,
                        is_completed=task.is_completed
                    )
                    created_tasks.append(repeated_task)
                    
                    instance_start += timedelta(days=day_durant)
                    instance_end += timedelta(days=day_durant)
                
                # 批量创建任务
                Task.objects.bulk_create(created_tasks)

                sync_task_important_reminder(task, _request_sync_important_reminder(self.request))

                return Response({
                    'created': len(created_tasks),
                    'tasks': TaskBulkSerializer(created_tasks, many=True).data
                }, status=status.HTTP_201_CREATED)
        
        sync_task_important_reminder(task, _request_sync_important_reminder(self.request))

        # 如果不是重复任务，正常返回
        return Response(
            TaskSerializer(task).data, 
            status=status.HTTP_201_CREATED
        )
    

    def perform_update(self, serializer):
        # 获取当前任务实例
        instance = self.get_object()
        
        # 确定更新范围
        update_scope = self.request.data.get('update_scope', 'this')
        
        # 准备更新数据
        update_data = {
            key: value for key, value in serializer.validated_data.items() 
            if key not in ['parent_series', 'is_exception', 'start_date', 'end_date','original_date']
        }
        
        if update_scope == 'this':
            # 仅更新当前任务
            serializer.save()
        
        elif update_scope == 'future':
            # 使用事务确保原子性
            with transaction.atomic():
                # 保存当前任务
                current_task = serializer.save()
                
                # 找到同一系列的所有未来任务
                future_tasks = Task.objects.filter(
                    parent_series=instance.parent_series or instance,
                    start_date__gte=instance.start_date
                )
                
                # 准备批量更新的任务
                tasks_to_update = []
                for task in future_tasks:
                    for key, value in update_data.items():
                        setattr(task, key, value)
                    tasks_to_update.append(task)
                
                # 使用 bulk_update 提高性能
                if tasks_to_update:
                    Task.objects.bulk_update(tasks_to_update, list(update_data.keys()))
        
        elif update_scope == 'all':
            # 使用事务确保原子性
            with transaction.atomic():
                # 保存当前任务
                current_task = serializer.save()
                
                # 找到同一系列的所有任务
                series_tasks = Task.objects.filter(
                    parent_series=instance.parent_series or instance
                )
                
                # 准备批量更新的任务
                tasks_to_update = []
                for task in series_tasks:
                    for key, value in update_data.items():
                        setattr(task, key, value)
                    tasks_to_update.append(task)
                
                # 使用 bulk_update 提高性能
                if tasks_to_update:
                    Task.objects.bulk_update(tasks_to_update, list(update_data.keys()))
        
        sync_task_important_reminder(serializer.instance, _request_sync_important_reminder(self.request))

        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        # 从查询参数中获取删除范围
        delete_scope = request.query_params.get('delete_scope', 'this')

        instance = self.get_object()
        
        if instance.parent_series and delete_scope != 'this':
            # 处理重复任务的不同删除范围
            if delete_scope == 'future':
                # 删除当前及未来任务
                Task.objects.filter(
                    parent_series=instance.parent_series,
                    start_date__gte=instance.start_date
                ).delete()
            elif delete_scope == 'all':
                # 删除整个任务系列
                Task.objects.filter(parent_series=instance.parent_series).delete()
        else:
            # 默认只删除当前任务
            instance.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)


    #关闭和移动只对单任务生效，不重写批量操作
    @action(detail=True, methods=['post'])
    def toggle_complete(self, request, pk=None):
        """
        切换任务的完成状态
        """
        task = self.get_object()
        task.is_completed = not task.is_completed
        task.save()
        
        serializer = self.get_serializer(task)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def plan_execution_record(self, request, pk=None):
        """
        为周历计划写入一条学习记录；可选同时将计划标记为已完成。
        mark_complete=false：仅记「该时段实际做了什么」，不改变计划完成状态。
        mark_complete=true：写入记录并将 is_completed 设为 True。
        """
        task = self.get_object()
        mark_complete = request.data.get('mark_complete', False)
        if isinstance(mark_complete, str):
            mark_complete = mark_complete.strip().lower() in ('true', '1', 'yes', 'on')

        start_dt = _parse_iso_datetime_for_study_record(request.data.get('start_time'))
        end_dt = _parse_iso_datetime_for_study_record(request.data.get('end_time'))
        if not start_dt or not end_dt:
            return Response(
                {'error': '缺少或无效的开始/结束时间'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if end_dt <= start_dt:
            return Response(
                {'error': '结束时间必须晚于开始时间'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        duration_sec = int((end_dt - start_dt).total_seconds())
        if duration_sec <= 0:
            return Response({'error': '时长须大于 0'}, status=status.HTTP_400_BAD_REQUEST)

        chapter_id = request.data.get('chapter')
        chapter = None
        subject_name = (request.data.get('subject_name') or '').strip() or '—'
        chapter_name = (request.data.get('chapter_name') or '').strip() or '—'

        if chapter_id not in (None, '', 'null'):
            try:
                chapter = Chapter.objects.select_related('subject').get(pk=int(chapter_id))
            except (ValueError, TypeError, Chapter.DoesNotExist):
                return Response(
                    {'error': '无效的任务（子任务）'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if chapter.subject:
                subject_name = chapter.subject.name
            chapter_name = chapter.title

        learning_content = request.data.get('learning_content', '') or ''
        description = request.data.get('description', '') or ''

        page_type = request.data.get('page_type') or 'other'
        valid_pt = {c[0] for c in StudyRecord.PAGE_TYPE_CHOICES}
        if page_type not in valid_pt:
            page_type = 'other'

        with transaction.atomic():
            StudyRecord.objects.create(
                user=request.user,
                created_date=timezone.localtime(start_dt).date(),
                start_time=start_dt,
                end_time=end_dt,
                duration=duration_sec,
                page_type=page_type,
                chapter=chapter,
                subject_name=subject_name,
                chapter_name=chapter_name,
                learning_content=learning_content,
                description=description,
            )
            if mark_complete:
                Task.objects.filter(pk=task.pk, user=request.user).update(is_completed=True)

        task.refresh_from_db()
        serializer = self.get_serializer(task)
        return Response({'status': 'ok', 'mark_complete': bool(mark_complete), 'task': serializer.data})
        
    @action(detail=True, methods=['patch'])
    def move(self, request, pk=None):
        """
        移动任务（更新时间）
        """
        #获取传送过来的数据
        task = self.get_object()
        
        # 安全获取数据并转换为字符串
        def parse_datetime(datetime_str):
            """解析 ISO 时间，统一到 Django 当前时区（与 settings.TIME_ZONE / 序列化一致）。"""
            if not datetime_str:
                return None
            try:
                dt = dateparse.parse_datetime(str(datetime_str))
                if dt is None:
                    return None
                if timezone.is_naive(dt):
                    dt = timezone.make_aware(dt)
                local_dt = timezone.localtime(dt)
                t = local_dt.time().replace(microsecond=0)
                return {
                    'date': local_dt.date(),
                    'time': t,
                    'datetime': local_dt,
                }
            except Exception as e:
                print(f"日期时间解析错误: {datetime_str}, error={str(e)}")
                return None

        # 获取并解析开始和结束日期时间
        start_datetime = parse_datetime(request.data.get('start_date_time'))
        end_datetime = parse_datetime(request.data.get('end_date_time'))

        # 更新日期和时间
        if start_datetime:
            task.start_date = start_datetime['date']
            task.start_time = start_datetime['time']
        
        if end_datetime:
            task.end_date = end_datetime['date']
            task.end_time = end_datetime['time']
    
        
        try:
            task.save()
            refresh_important_date_from_task_if_linked(task)
            # 重新获取最新数据并序列化
            task.refresh_from_db()
            serializer = self.get_serializer(task)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class SubjectViewSet(viewsets.ModelViewSet):
    """
    学科的API视图集（默认仅返回开启中的项目）
    """
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['heat', 'order', 'name', 'created_at']
    ordering = ['-heat', 'order', 'name']

    def get_queryset(self):
        qs = Subject.objects.all()
        include_closed = self.request.query_params.get('include_closed')
        if include_closed not in ('1', 'true', 'yes'):
            qs = qs.filter(open_status=Subject.OpenStatus.OPEN)
        return qs

class ChapterViewSet(viewsets.ModelViewSet):
    """
    章节的API视图集
    """
    serializer_class = ChapterSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ['subject']
    ordering_fields = ['order', 'title', 'created_at']
    ordering = ['order', 'title']

    def get_queryset(self):
        base = Chapter.objects.all()
        # 仅列表接口排除「完成」，避免 retrieve 等单条访问被误伤
        if getattr(self, 'action', None) != 'list':
            return base
        include_pk = None
        raw = self.request.query_params.get('include_chapter')
        if raw not in (None, ''):
            try:
                include_pk = int(raw)
            except (TypeError, ValueError):
                include_pk = None
        q = ~Q(progress_status=Chapter.ProgressStatus.DONE)
        if include_pk is not None:
            q = q | Q(pk=include_pk)
        return base.filter(q).distinct()

class DailySummaryViewSet(viewsets.ModelViewSet):
    """
    每日总结的API视图集
    """
    serializer_class = DailySummarySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['date']

    def get_queryset(self):
        return DailySummary.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # 检查是否已存在当天的总结
        date = self.request.data.get('date')
        existing_summary = DailySummary.objects.filter(
            user=self.request.user,
            date=date
        ).first()

        if existing_summary:
            # 如果存在，更新它
            existing_summary.description = self.request.data.get('description')
            existing_summary.save()
            serializer = self.get_serializer(existing_summary)
            return Response(serializer.data)
        else:
            # 如果不存在，创建新的
            serializer.save(user=self.request.user)

class WordsViewSet(viewsets.ModelViewSet):
    """
    单词的API视图集
    """
    serializer_class = WordsSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend, filters.SearchFilter]
    ordering_fields = ['created_at', 'updated_at', 'level']
    ordering = ['-created_at']
    search_fields = ['word', 'translation']
    filterset_fields = ['level']

    def get_queryset(self):
        queryset = Words.objects.all()
        
        # 按日期过滤
        date = self.request.query_params.get('date', None)
        if date:
            queryset = queryset.filter(
                created_at__date=date
            )
            
        return queryset

    @action(detail=False, methods=['get'])
    def export(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        
        # 创建响应
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="words_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['单词', '含义', '例句', '等级', '创建时间', '更新时间'])
        
        for word in queryset:
            writer.writerow([
                word.word,
                word.translation,
                word.example_sentence or '',
                word.level,
                word.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                word.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
            
        return response

    def perform_create(self, serializer):
        serializer.save()