from datetime import timezone, datetime as dt_datetime
from functools import reduce
from operator import or_
from urllib import request
from rest_framework import permissions
from django.db.models import Count, Q, Sum
from django.views.generic import ListView, DetailView
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views import View
from django.core.paginator import Paginator, EmptyPage
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from .models import (
        Subject, SubjectCategory, Chapter, StudyRecord,
        KnowledgePoint,
        SubjectPlanSummary,
        )
from .forms import ChapterForm, SubjectForm, ChapterForm_detail
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from .serializers import (
        ChapterSerializer, StudyRecordSerializer,
    )
from django.contrib.auth import get_user_model
from rest_framework import serializers
import json
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_POST
import logging





def get_tree_data(queryset):
    print(f"Building tree from {queryset.count()} nodes")

    # 构建节点映射
    nodes = {node.id: {
        'id': node.id,
        'title': node.title,
        'tree_id': node.tree_id,
        'created_at': node.created,
        'children': [],
        'brother_id':node.brother_id
    } for node in queryset}
    
    # 构建树结构
    for node in queryset:
        if node.parent_id and node.parent_id in nodes:
            nodes[node.parent_id]['children'].append(nodes[node.id])
    
    # 返回顶级节点
    root_nodes = [nodes[node.id] for node in queryset if not node.parent_id]
    if not root_nodes:
        # 如果没有根节点，返回所有节点
        root_nodes = list(nodes.values())
    
    print(f"Generated tree with {len(root_nodes)} root nodes")
    return root_nodes



# 记录视图
class StudyRecordListView(LoginRequiredMixin, APIView):
    def get(self, request):
        created_date_start = request.GET.get('created_date_start')
        created_date_end = request.GET.get('created_date_end')
        page_type = request.GET.get('page_type')
        learning_content = request.GET.get('learning_content')
        chapter_id = request.GET.get('chapter')
        
        queryset = StudyRecord.objects.filter(user=request.user)
        
        if created_date_start and created_date_end:
            queryset = queryset.filter(created_date__range=[created_date_start, created_date_end])
        if page_type:
            queryset = queryset.filter(page_type=page_type)
        if learning_content:
            queryset = queryset.filter(learning_content__icontains=learning_content)
        if chapter_id:
            queryset = queryset.filter(chapter_id=chapter_id)
            
        queryset = queryset.order_by('-created_date', '-start_time')
        
        paginator = Paginator(queryset, 10)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        subjects = Subject.objects.all()
        chapters = Chapter.objects.all()
        page_types = StudyRecord.PAGE_TYPE_CHOICES
        
        context = {
            'records': page_obj,
            'subjects': subjects,
            'chapters': chapters,
            'page_types': page_types,
            'show_full_filters': True,
            'is_paginated': True,
            'page_obj': page_obj
        }
        
        return render(request, 'courses/_study_records.html', context, 
                    content_type='text/html; fragment=true')

class BaseStudyRecordListView(StudyRecordListView):
    def get(self, request):
        created_date_start = request.GET.get('created_date_start')
        created_date_end = request.GET.get('created_date_end')
        page_type = request.GET.get('page_type')
        learning_content = request.GET.get('learning_content')
        chapter_id = request.GET.get('chapter')
        
        queryset = StudyRecord.objects.filter(user=request.user)
        
        if created_date_start and created_date_end:
            queryset = queryset.filter(created_date__range=[created_date_start, created_date_end])
        if page_type:
            queryset = queryset.filter(page_type=page_type)
        if learning_content:
            queryset = queryset.filter(learning_content__icontains=learning_content)
        if chapter_id:
            queryset = queryset.filter(chapter_id=chapter_id)
            
        queryset = queryset.order_by('-created_date', '-start_time')
        
        paginator = Paginator(queryset, 10)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        subjects = Subject.objects.all()
        chapters = Chapter.objects.all()
        page_types = StudyRecord.PAGE_TYPE_CHOICES
        
        context = {
            'records': page_obj,
            'subjects': subjects,
            'chapters': chapters,
            'page_types': page_types,
            'show_full_filters': True,
            'is_paginated': True,
            'page_obj': page_obj
        }
        
        return render(request, 'courses/study_record_base.html', context)

#学习视图 API
class StudyRecordsAPIView(APIView):
    def get(self, request):
        # 获取查询参数
        created_date_start = request.GET.get('created_date_start')
        created_date_end = request.GET.get('created_date_end')
        page_type = request.GET.get('page_type')
        content_search = (request.GET.get('content_search') or '').strip()
        if not content_search:
            content_search = (request.GET.get('learning_content') or '').strip()
        task_content = (request.GET.get('task_content') or '').strip()
        chapter_id = request.GET.get('chapter')
        subject_id = request.GET.get('subject')
        page = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', 10)
        
        # 获取当前用户的记录
        queryset = StudyRecord.objects.filter(user=request.user)
        
        # 应用过滤条件
        if created_date_start and created_date_end:
            queryset = queryset.filter(created_date__range=[created_date_start, created_date_end])
        if page_type:
            queryset = queryset.filter(page_type=page_type)
        if task_content:
            queryset = queryset.filter(
                Q(learning_content__icontains=task_content)
                | Q(description__icontains=task_content)
            )
        if not task_content and content_search:
            queryset = queryset.filter(
                Q(learning_content__icontains=content_search)
                | Q(description__icontains=content_search)
                | Q(chapter_name__icontains=content_search)
            )
        if subject_id:
            try:
                queryset = queryset.filter(chapter__subject_id=int(subject_id))
            except (TypeError, ValueError):
                pass
        if chapter_id:
            queryset = queryset.filter(chapter_id=chapter_id)
            
        # 排序和分页
        queryset = queryset.order_by('-created_date', '-start_time')
        total_count = queryset.count()
        records = queryset[(int(page)-1)*int(page_size):int(page)*int(page_size)]
        page_types = StudyRecord.PAGE_TYPE_CHOICES

        
        # 序列化数据
        serializer = StudyRecordSerializer(records, many=True)
        
        return Response({
            'data': serializer.data,
            'pagination': {
                'total': total_count,
                'page': int(page),
                'page_size': int(page_size),
                'page_count': (total_count + int(page_size) - 1) // int(page_size)
                }
            }
        )

class KnowledgePointListView(LoginRequiredMixin, ListView):
    model = KnowledgePoint
    template_name = 'courses/knowledgepoint_list.html'
    context_object_name = 'knowledge_points'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        chapter_id = self.request.GET.get('chapter')
        if chapter_id:
            queryset = queryset.filter(chapter_id=chapter_id)
        return queryset.select_related('chapter')

class KnowledgePointDetailView(LoginRequiredMixin, DetailView):
    model = KnowledgePoint
    template_name = 'courses/knowledgepoint_detail.html'
    context_object_name = 'knowledge_point'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 添加关联的chapter信息
        context['chapter'] = self.object.chapter
        return context



@login_required
def subjectListView(request):  # 处理GET请求
    """按科目分类分块展示：分类按显示权重降序。
    归属「是否显示=否」的分类的科目不在本页展示（入口隐藏）；「其他」仅含未分类科目。
    """
    # 列表中允许出现的科目：未分类，或分类为「显示」
    listed_q = Q(category__isnull=True) | Q(category__is_visible=True)

    unfinished_chapters_sq = Count(
        'chapters',
        filter=~Q(chapters__progress_status=Chapter.ProgressStatus.DONE),
    )

    def subjects_with_unfinished_qs(base_q):
        return (
            Subject.objects.filter(base_q)
            .select_related('category')
            .annotate(unfinished_tasks_count=unfinished_chapters_sq)
            .order_by('order', 'name')
        )

    visible_categories = SubjectCategory.objects.filter(is_visible=True).order_by(
        '-display_weight', 'id'
    )

    category_blocks = []
    for cat in visible_categories:
        subs = list(subjects_with_unfinished_qs(listed_q & Q(category=cat)))
        if subs:
            category_blocks.append({'title': cat.name, 'subjects': subs})

    other_subjects = list(
        subjects_with_unfinished_qs(Q(category__isnull=True))
    )
    if other_subjects:
        category_blocks.append({'title': '其他', 'subjects': other_subjects})

    queryset = Subject.objects.filter(listed_q)
    total_hours = queryset.aggregate(Sum('estimated_hours'))['estimated_hours__sum'] or 0
    total_actual_hours = queryset.aggregate(Sum('actual_study_hours'))['actual_study_hours__sum'] or 0
    subject_categories = SubjectCategory.objects.all().order_by('-display_weight', 'name')

    return render(
        request,
        'courses/subject_list.html',
        {
            'category_blocks': category_blocks,
            'total_subject_count': queryset.count(),
            'subject_categories': subject_categories,
            'total_hours': total_hours,
            'total_actual_hours': total_actual_hours,
        },
    )


@login_required
def subject_create(request):
    if request.method == 'POST':
        # 处理科目创建逻辑
        form = SubjectForm(request.POST, request.FILES)
        if form.is_valid():  # 触发验证
            subject = form.save()
            return JsonResponse({'status': 'success'})
        else:
            # 返回验证错误
            return JsonResponse({
                'status': 'error',
                'errors': form.errors.as_json()
            }, status=400)

logger = logging.getLogger(__name__)

@login_required
def subject_update(request,pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        form = SubjectForm(request.POST, request.FILES, instance=subject)
        if form.is_valid():
            form.save()
            return JsonResponse({'status': 'success'})
        return JsonResponse({'errors': form.errors}, status=400)
    
@login_required
def subject_delete(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        subject.delete()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': '无效的请求方法'}, status=400)


@login_required
def subject_data(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            return JsonResponse({'status': 'success'})
        return JsonResponse({'errors': form.errors}, status=400)
    return JsonResponse({
        'id': subject.id,
        'name': subject.name,
        'description': subject.description,
        'color': subject.color,
        'estimated_hours': subject.estimated_hours,
        'background_image': subject.background_image.url if subject.background_image else None,
        'category_id': subject.category_id,
    })
    
@login_required
@require_POST
def subject_refresh(request, pk):
    """
    子任务（Chapter）：本周计划/实际投入写入 estimated_hours、actual_hours，并重算 progress。
    项目（Subject）：写入本周合计（各子任务 + 未归属周历/记录）到 estimated_hours、actual_study_hours。
    累计已投 already_hours 仍仅由周日 management command 更新。
    """
    from .subject_weekly_stats import persist_subject_weekly_stats

    subject = get_object_or_404(Subject, pk=pk)
    stats = persist_subject_weekly_stats(request.user, subject)
    return JsonResponse(
        {
            "status": "success",
            "weekly_planned_hours": stats["planned_hours"],
            "weekly_actual_hours": stats["actual_hours"],
            "planned_unassigned_hours": stats["planned_unassigned_hours"],
            "actual_unassigned_hours": stats["actual_unassigned_hours"],
            "planned_by_chapter": stats["planned_by_chapter"],
            "actual_by_chapter": stats["actual_by_chapter"],
        }
    )

@login_required
def subject_detail(request, pk):
    subject = get_object_or_404(Subject.objects.select_related('category'), pk=pk)
    chapters_qs = subject.chapters.all().order_by('order')
    chapters_incomplete = chapters_qs.exclude(progress_status=Chapter.ProgressStatus.DONE)
    chapters_completed = chapters_qs.filter(progress_status=Chapter.ProgressStatus.DONE)
    subject_categories = SubjectCategory.objects.all().order_by('-display_weight', 'name')
    return render(request, 'courses/subject_detail.html', {
        'subject': subject,
        'chapters_incomplete': chapters_incomplete,
        'chapters_completed': chapters_completed,
        'subject_categories': subject_categories,
    })

@login_required
def chapter_detail(request, pk):
    chapter = get_object_or_404(Chapter, pk=pk)
    knowledge_points = KnowledgePoint.objects.filter(chapter=chapter)
    
    tree_data = get_tree_data(knowledge_points) if knowledge_points.exists() else []
    
    statuses = [c[0] for c in Chapter.ProgressStatus.choices]

    context = {
        "chapter": chapter,
        "subject": chapter.subject,
        "tree_data": tree_data,
        "comment_type": "chapter",
        "type_id": pk,
        "chapter_progress_statuses": statuses,
    }
    return render(request, "courses/chapter_detail.html", context)


@login_required
def chapter_create(request):
    if request.method == 'POST':
        form = ChapterForm(request.POST)
        if form.is_valid():
            chapter = form.save(commit=False)
            subject = request.POST.get('subject_id')
            if subject:
                chapter.subject_id = subject
                chapter.save()
                return JsonResponse({'status': 'success', 'id': chapter.id})
            return JsonResponse({'status': 'error', 'errors': {'subject_id': ['缺少关联科目ID']}}, status=400)
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)


@login_required
@require_POST
def chapter_update_progress_status(request, pk):
    """知识点页快速切换章节进度状态（仅更新 progress_status）。"""
    chapter = get_object_or_404(Chapter, pk=pk)
    raw = (request.POST.get("progress_status") or "").strip()
    valid = {c[0] for c in Chapter.ProgressStatus.choices}
    if raw not in valid:
        return JsonResponse({"status": "error", "message": "无效的进度状态"}, status=400)
    chapter.progress_status = raw
    chapter.save(update_fields=["progress_status"])
    return JsonResponse({"status": "success", "progress_status": raw})


@login_required
def chapter_update(request, pk):
    chapter = get_object_or_404(Chapter, pk=pk)

    if request.method == 'POST':
        form = ChapterForm_detail(request.POST, instance=chapter)
        if form.is_valid():
            # 获取未保存的模型实例
            chapter_instance = form.save(commit=False)
            
            # 统计知识点数量并更新到章节
            chapter_instance.knowledge_points_count = KnowledgePoint.objects.filter(chapter=chapter_instance).count()
            
            # 保存模型实例
            chapter_instance.save()

            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

@login_required
def chapter_delete(request, pk):
    chapter = get_object_or_404(Chapter, pk=pk)
    if request.method == 'POST':
        chapter.delete()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': '无效的请求方法'}, status=400)

@login_required
def subject_chapter_options(request):
    """提供科目和章节的级联选项数据"""
    subjects = Subject.objects.all().prefetch_related('chapters')
    options = []
    
    for subject in subjects:
        subject_data = {
            'value': str(subject.id),
            'label': subject.name,
            'children': []
        }
        
        for chapter in subject.chapters.all():
            subject_data['children'].append({
                'value': str(chapter.id),
                'label': chapter.title
            })
            
        options.append(subject_data)
    
    return JsonResponse(options, safe=False)

class ChapterDetailView(LoginRequiredMixin, DetailView):
    model = Chapter
    template_name = 'courses/chapter_detail.html'
    context_object_name = 'chapter'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        chapter = self.object
        context["form"] = ChapterForm(instance=chapter)
        knowledge_points = KnowledgePoint.objects.filter(chapter=chapter)
        context["tree_data"] = (
            get_tree_data(knowledge_points) if knowledge_points.exists() else []
        )
        context["subject"] = chapter.subject
        context["comment_type"] = "chapter"
        context["type_id"] = chapter.pk
        context["chapter_progress_statuses"] = [
            c[0] for c in Chapter.ProgressStatus.choices
        ]
        return context

# API视图
class ChapterListAPI(generics.ListAPIView):
    queryset = Chapter.objects.all()
    serializer_class = ChapterSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        subject_id = self.request.query_params.get('subject_id')
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
        return queryset

class StudyRecordCreateAPI(generics.CreateAPIView):
    queryset = StudyRecord.objects.all()
    serializer_class = StudyRecordSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        User = get_user_model()
        user = self.request.user
        user_id = self.request.data.get('user')
        if user_id is not None and str(user_id).strip() != '':
            if not self.request.user.is_staff:
                raise serializers.ValidationError(
                    {'user': '只有管理员可代其他用户创建记录'}
                )
            try:
                user = User.objects.get(pk=user_id)
            except (User.DoesNotExist, TypeError, ValueError):
                raise serializers.ValidationError({'user': '用户不存在'})
        if user and not user.is_active:
            raise serializers.ValidationError({'user': '用户账户未激活'})
        serializer.save(user=user)


class StudyRecordDetailAPI(generics.RetrieveUpdateDestroyAPIView):
    """当前用户单条学习记录的查看、修改、删除。"""

    serializer_class = StudyRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return StudyRecord.objects.filter(user=self.request.user)

class SubjectPlanSummaryListCreateAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, subject_pk):
        get_object_or_404(Subject, pk=subject_pk)
        q = (request.query_params.get('q') or '').strip()
        qs = SubjectPlanSummary.objects.filter(
            user=request.user, subject_id=subject_pk
        )
        if q:
            parts = [
                Q(title__icontains=q),
                Q(overview__icontains=q),
                Q(body__icontains=q),
            ]
            if len(q) >= 10 and q[4:5] == '-' and q[7:8] == '-':
                try:
                    d = dt_datetime.strptime(q[:10], '%Y-%m-%d').date()
                    parts.append(Q(created_at__date=d))
                except ValueError:
                    pass
            qs = qs.filter(reduce(or_, parts))
        rows = list(qs.order_by('-created_at')[:500])
        data = [
            {
                'id': s.id,
                'title': s.title,
                'overview': s.overview,
                'created_at': s.created_at.isoformat(),
                'updated_at': s.updated_at.isoformat(),
            }
            for s in rows
        ]
        return Response({'data': data})

    def post(self, request, subject_pk):
        get_object_or_404(Subject, pk=subject_pk)
        title = (request.data.get('title') or '').strip()
        if not title:
            return Response({'detail': '标题必填'}, status=status.HTTP_400_BAD_REQUEST)
        s = SubjectPlanSummary.objects.create(
            user=request.user,
            subject_id=subject_pk,
            title=title,
            overview=(request.data.get('overview') or '').strip(),
            body=request.data.get('body') or '',
        )
        return Response(
            {
                'id': s.id,
                'title': s.title,
                'overview': s.overview,
                'body': s.body,
                'created_at': s.created_at.isoformat(),
                'updated_at': s.updated_at.isoformat(),
            },
            status=status.HTTP_201_CREATED,
        )


class SubjectPlanSummaryDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(SubjectPlanSummary, pk=pk, user=self.request.user)

    def get(self, request, pk):
        s = self.get_object(pk)
        return Response(
            {
                'id': s.id,
                'subject': s.subject_id,
                'title': s.title,
                'overview': s.overview,
                'body': s.body,
                'created_at': s.created_at.isoformat(),
                'updated_at': s.updated_at.isoformat(),
            }
        )

    def patch(self, request, pk):
        s = self.get_object(pk)
        if 'title' in request.data:
            t = (request.data.get('title') or '').strip()
            if not t:
                return Response({'detail': '标题不能为空'}, status=status.HTTP_400_BAD_REQUEST)
            s.title = t
        if 'overview' in request.data:
            s.overview = (request.data.get('overview') or '').strip()
        if 'body' in request.data:
            s.body = request.data.get('body') or ''
        s.save()
        return Response(
            {
                'id': s.id,
                'subject': s.subject_id,
                'title': s.title,
                'overview': s.overview,
                'body': s.body,
                'created_at': s.created_at.isoformat(),
                'updated_at': s.updated_at.isoformat(),
            }
        )

    def delete(self, request, pk):
        s = self.get_object(pk)
        s.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@login_required
def subject_plan_review(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    from django.urls import reverse
    from urllib.parse import urlencode

    cal_q = urlencode({'embed': '1', 'plan_subject': str(subject.id)})
    calendar_iframe_src = f"{reverse('weekly_planner:calendar')}?{cal_q}"
    rec_path = reverse('courses:plan_review_records_embed', kwargs={'subject_pk': subject.id})
    records_iframe_src = f"{rec_path}?{urlencode({'embed': '1'})}"
    return render(
        request,
        'courses/subject_plan_review.html',
        {
            'subject': subject,
            'chapter': None,
            'show_summary_tab': True,
            'calendar_iframe_src': calendar_iframe_src,
            'records_iframe_src': records_iframe_src,
        },
    )


@login_required
def chapter_plan_review(request, pk):
    chapter = get_object_or_404(Chapter, pk=pk)
    from django.urls import reverse
    from urllib.parse import urlencode

    subject = chapter.subject
    cal_q = urlencode(
        {'embed': '1', 'plan_subject': str(subject.id), 'plan_chapter': str(chapter.id)}
    )
    calendar_iframe_src = f"{reverse('weekly_planner:calendar')}?{cal_q}"
    rec_path = reverse('courses:plan_review_records_embed', kwargs={'subject_pk': subject.id})
    records_iframe_src = f"{rec_path}?{urlencode({'embed': '1', 'chapter': str(chapter.id)})}"
    return render(
        request,
        'courses/subject_plan_review.html',
        {
            'subject': subject,
            'chapter': chapter,
            'show_summary_tab': False,
            'calendar_iframe_src': calendar_iframe_src,
            'records_iframe_src': records_iframe_src,
        },
    )


@login_required
def plan_review_records_embed(request, subject_pk):
    get_object_or_404(Subject, pk=subject_pk)
    chapter_raw = request.GET.get('chapter')
    chapter_id = None
    if chapter_raw not in (None, ''):
        try:
            chapter_id = int(chapter_raw)
        except (TypeError, ValueError):
            chapter_id = None
    return render(
        request,
        'courses/study_record_base.html',
        {
            'page_types': StudyRecord.PAGE_TYPE_CHOICES,
            'fixed_subject_id': int(subject_pk),
            'fixed_chapter_id': chapter_id,
            'hide_navbar': True,
        },
    )


@login_required
def subject_plan_summary_edit(request, subject_pk, summary_pk=None):
    subject = get_object_or_404(Subject, pk=subject_pk)
    summary = None
    if summary_pk is not None:
        summary = get_object_or_404(
            SubjectPlanSummary, pk=summary_pk, user=request.user, subject=subject
        )
    summary_body_json = json.dumps(summary.body or '') if summary else json.dumps('')
    return render(
        request,
        'courses/subject_plan_summary_edit.html',
        {
            'subject': subject,
            'summary': summary,
            'summary_body_json': summary_body_json,
        },
    )

