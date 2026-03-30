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
        queryset = Task.objects.filter(user=self.request.user)
        
        # 添加日期范围过滤
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if start_date and end_date:
                # 过滤在日期范围内的任务
                queryset = queryset.filter(
                    end_date__gte=start_date,
                    start_date__lte=end_date
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

                return Response({
                    'created': len(created_tasks),
                    'tasks': TaskBulkSerializer(created_tasks, many=True).data
                }, status=status.HTTP_201_CREATED)
        
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
    学科的API视图集
    """
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['order', 'name', 'created_at']
    ordering = ['order', 'name']

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
        return Chapter.objects.all()

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
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]  # 修改为认证用户可写，匿名用户只读
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