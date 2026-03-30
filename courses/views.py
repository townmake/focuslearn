from datetime import timezone
from urllib import request
from rest_framework import permissions
from django.db.models import Count, Q, Sum
from .serializers import VideoSerializer
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
        KnowledgePoint, Video, Comment, Exercise, ExerciseSet, ReviewSet,
        VideoComment, ExerciseSet, ExerciseSetCompletion, ExerciseAnswer, MethodSummary,
    )
from .forms import ChapterForm, SubjectForm, MethodSummaryForm,ChapterForm_detail
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.generic.edit import  DeleteView
from django.urls import reverse_lazy
from .serializers import (
        ChapterSerializer, StudyRecordSerializer, ExerciseSetSerializer, 
        ExerciseSetCompletionSerializer, ExerciseSetCreateSerializer, ExerciseSetCompletionCreateSerializer, MethodSummarySerializer,
        ExerciseSerializer,MethodSummaryCreateSerializer,MethodSummarySerializer
    )
from django.contrib.auth import get_user_model
from rest_framework import serializers
import json
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import logging





def exercise_set_result(request, exercise_set_id, completion_id):
    """显示练习集结果"""
    exercise_set = get_object_or_404(ExerciseSet, id=exercise_set_id)
    completion = get_object_or_404(ExerciseSetCompletion, id=completion_id)
    
    # 获取本次提交的答题记录
    answer_records = ExerciseAnswer.objects.filter(
        exercise_set_completion=completion,
        user=request.user
    ).order_by('exercise__order')
    
    # 准备结果数据
    results = []
    correct_count = 0
    
    # 按题目类型分组处理
    from collections import defaultdict
    grouped_records = defaultdict(list)
    for record in answer_records:
        grouped_records[record.exercise.parent_id or record.exercise.id].append(record)
    
    # 处理分组后的记录
    for parent_id, records in grouped_records.items():
        # 处理母题
        parent_record = records[0]
        parent_exercise = parent_record.exercise
        
        # 如果是完形填空/阅读理解
        if parent_exercise.question_type in ['cloze_test', 'reading_answer']:
            # 添加母题记录
            results.append({
                'exercise_id': parent_exercise.id,
                'title': parent_exercise.title or f"母题 #{parent_exercise.id}",
                'user_answer': '',
                'correct_answer': '',
                'is_correct': all(r.is_correct for r in records),
                'is_parent': True
            })
            
            # 添加子题记录
            sub_exercises = Exercise.objects.filter(parent_id=parent_exercise.id).order_by('order')
            for sub_ex in sub_exercises:
                sub_record = next((r for r in records if r.exercise_id == sub_ex.id), None)
                if sub_record:
                    results.append({
                        'exercise_id': sub_ex.id,
                        'title': f"子题 {sub_ex.order}",
                        'user_answer': sub_record.answer,
                        'correct_answer': sub_ex.answer,
                        'is_correct': sub_record.is_correct,
                        'is_child': True
                    })
                    if sub_record.is_correct:
                        correct_count += 1
        else:
            # 普通题目
            results.append({
                'exercise_id': parent_exercise.id,
                'title': parent_exercise.title or f"习题 #{parent_exercise.id}",
                'user_answer': parent_record.answer,
                'correct_answer': parent_exercise.answer,
                'is_correct': parent_record.is_correct
            })
            if parent_record.is_correct:
                correct_count += 1
    
    context = {
        'exercise_set': exercise_set,
        'results': results,
        'correct_count': correct_count,
        'accuracy': completion.score
    }
    
    return render(request, 'courses/exercise_result.html', context)


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
class StudyRecordListView(APIView):
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
            # 兼容旧参数名
            content_search = (request.GET.get('learning_content') or '').strip()
        chapter_id = request.GET.get('chapter')
        page = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', 10)
        
        # 获取当前用户的记录
        queryset = StudyRecord.objects.filter(user=request.user)
        
        # 应用过滤条件
        if created_date_start and created_date_end:
            queryset = queryset.filter(created_date__range=[created_date_start, created_date_end])
        if page_type:
            queryset = queryset.filter(page_type=page_type)
        if content_search:
            queryset = queryset.filter(
                Q(learning_content__icontains=content_search)
                | Q(description__icontains=content_search)
            )
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

class KnowledgePointListView(ListView):
    model = KnowledgePoint
    template_name = 'courses/knowledgepoint_list.html'
    context_object_name = 'knowledge_points'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        chapter_id = self.request.GET.get('chapter')
        if chapter_id:
            queryset = queryset.filter(chapter_id=chapter_id)
        return queryset.select_related('chapter')

class KnowledgePointDetailView(DetailView):
    model = KnowledgePoint
    template_name = 'courses/knowledgepoint_detail.html'
    context_object_name = 'knowledge_point'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 添加关联的chapter信息
        context['chapter'] = self.object.chapter
        # 添加关联的文档、视频和习题
        context['exercises'] = self.object.exercises.all()
        return context

    
def subjectListView(request):  # 处理GET请求
    """按科目分类分块展示：分类按显示权重降序。
    归属「是否显示=否」的分类的科目不在本页展示（入口隐藏）；「其他」仅含未分类科目。
    """
    # 列表中允许出现的科目：未分类，或分类为「显示」
    listed_q = Q(category__isnull=True) | Q(category__is_visible=True)

    visible_categories = SubjectCategory.objects.filter(is_visible=True).order_by(
        '-display_weight', 'id'
    )

    category_blocks = []
    for cat in visible_categories:
        subs = list(
            Subject.objects.filter(listed_q, category=cat)
            .select_related('category')
            .order_by('order', 'name')
        )
        if subs:
            category_blocks.append({'title': cat.name, 'subjects': subs})

    other_subjects = list(
        Subject.objects.filter(category__isnull=True)
        .select_related('category')
        .order_by('order', 'name')
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

def subject_update(request,pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        form = SubjectForm(request.POST, request.FILES, instance=subject)
        if form.is_valid():
            form.save()
            return JsonResponse({'status': 'success'})
        return JsonResponse({'errors': form.errors}, status=400)
    
def subject_delete(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        subject.delete()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': '无效的请求方法'}, status=400)


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

def subject_detail(request, pk):
    subject = get_object_or_404(Subject.objects.select_related('category'), pk=pk)
    chapters = subject.chapters.all().order_by('order')
    subject_categories = SubjectCategory.objects.all().order_by('-display_weight', 'name')
    return render(request, 'courses/subject_detail.html', {
        'subject': subject,
        'chapters': chapters,
        'subject_categories': subject_categories,
    })

def subject_methods(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    # chapters = subject.chapters.all().order_by('order')
    return render(request, 'courses/subject_method_summary.html', {
        'subject': subject
    })




def chapter_detail(request, pk):
    chapter = get_object_or_404(Chapter, pk=pk)
    knowledge_points = KnowledgePoint.objects.filter(chapter=chapter)
    
    tree_data = get_tree_data(knowledge_points) if knowledge_points.exists() else []
    
    context = {
        'chapter': chapter,
        'subject': chapter.subject,
        'tree_data': tree_data,
        'comment_type': 'chapter',  # 评论类型
        'type_id': pk  # 当前章节ID
    }
    return render(request, 'courses/chapter_detail.html', context)


@login_required
def daily_review_sets(request):
    """获取用户今日复习任务"""
    today = timezone.now().date()
    # 获取今日创建的复习集（按科目分组）
    review_sets = ReviewSet.objects.filter(
        created_at__date=today
    ).select_related('chapter__subject')
    
    # 按科目分组
    subjects_reviews = {}
    for review in review_sets:
        subject = review.chapter.subject if review.chapter else None
        if subject not in subjects_reviews:
            subjects_reviews[subject] = []
        subjects_reviews[subject].append(review)
    
    context = {
        'subjects_reviews': subjects_reviews,
        'title': '今日复习任务'
    }
    return render(request, 'courses/daily_reviews.html', context)
    


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

def chapter_delete(request, pk):
    chapter = get_object_or_404(Chapter, pk=pk)
    if request.method == 'POST':
        chapter.delete()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': '无效的请求方法'}, status=400)

def chapter_nextMethods(request, pk):
    chapter = get_object_or_404(Chapter, pk=pk)
    methods = MethodSummary.objects.filter(chapter=chapter).order_by('id')
    methods_data = [{'id': method.id, 'name': method.name} for method in methods]
    return JsonResponse({'methods': methods_data}, safe=False)


def chapter_nextChapter(request, pk):
    chapter = get_object_or_404(Chapter, pk=pk)
    next_chapter = Chapter.objects.filter(subject=chapter.subject, order__gt=chapter.order).first()
    if next_chapter:
        return JsonResponse({
            'status': 'success',
            'next_chapter_id': next_chapter.id,
            'message': '找到下一章节'
        })
    else:
        return JsonResponse({
            'status': 'error',
            'next_chapter_id': None,
            'message': '没有下一章节'
        }, status=404)

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

# 原有类视图
class MethodSummaryListView(generics.ListCreateAPIView):
    queryset = MethodSummary.objects.all()
    serializer_class = MethodSummarySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 获取查询参数
        name = self.request.query_params.get('name')
        created_at_start = self.request.query_params.get('created_at_start')
        created_at_end = self.request.query_params.get('created_at_end')
        chapter = self.request.query_params.get('chapter')
        
        # 应用过滤条件
        if chapter:
            queryset = queryset.filter(chapter=chapter)
        if name:
            queryset = queryset.filter(name__icontains=name)
        if created_at_start and created_at_end:
            queryset = queryset.filter(created_at__range=[created_at_start, created_at_end])

        return queryset

class MethodSummarySubjectListView(generics.ListCreateAPIView):
    queryset = MethodSummary.objects.all()
    serializer_class = MethodSummarySerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 获取查询参数
        name = self.request.query_params.get('name')
        created_at_start = self.request.query_params.get('created_at_start')
        created_at_end = self.request.query_params.get('created_at_end')
        subject_id = self.kwargs.get('subject_id') or self.request.query_params.get('subject_id')
        
        if subject_id:
            queryset = queryset.filter(chapter__subject_id=subject_id)
        else:
            return MethodSummary.objects.none()
            
        if name:
            queryset = queryset.filter(name__icontains=name)
        if created_at_start and created_at_end:
            queryset = queryset.filter(created_at__range=[created_at_start, created_at_end])

        # 添加annotated_exercise_count字段避免与模型属性冲突
        queryset = queryset.annotate(
            annotated_exercise_count=Count('exercises')
        )
        
        # 打印调试信息
        # print("MethodSummaryListViewSubject 返回数据示例:", queryset.first())
        # print("SQL查询:", str(queryset.query))
        
        # 添加默认按chapter.id排序
        queryset = queryset.order_by('chapter__id')
        return queryset


class MethodSummaryListCreateAPI(generics.ListCreateAPIView):
    serializer_class = MethodSummarySerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MethodSummaryCreateSerializer
        return MethodSummarySerializer


class MethodSummaryDetailView(DetailView):
    model = MethodSummary
    template_name = 'courses/method_summary_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        exercises = self.object.exercises.all()
        knowleges = self.object.knowledgePoint.all().order_by('id')
        context['method'] = {
            'id': self.object.id,
            'name': self.object.name,
            'created_at': self.object.created_at.strftime('%Y-%m-%d %H:%M'),
            'description': self.object.description,
            'note': self.object.note,
            'exercise_count': self.object.exercise_count,
            'chapter_id': self.object.chapter_id,
            'difficulty': self.object.difficulty_level,
            'importance': self.object.important_level
        }
        context['exercises'] = [{
            'id': ex.id,
            'title': ex.title,
            'question_type': ex.get_question_type_display(),
            'question': ex.content,
            'wrong_count': ex.wrong_count,
            'correct_count': ex.correct_count,
            'mastery_level': ex.mastery_level,
            'memory_level': ex.memory_level,
            'difficulty': ex.difficulty
        } for ex in exercises]
        context['knowledgepoints'] = [{
            'id': kp.id,
            'title': kp.title,
        } for kp in knowleges]
        return context


class MethodSummaryUpdateAPIView(APIView):
    def post(self, request, pk):
        try:
            method_summary = MethodSummary.objects.get(pk=pk)
            
            data = request.data
            # 创建表单实例
            form = MethodSummaryForm(data,instance=method_summary)          
            if form.is_valid():
                method_summary = form.save()
                # 序列化返回数据
                serializer = MethodSummarySerializer(method_summary)
                return Response({
                    'success': True,
                    'message': '更新成功',
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': '表单验证失败',
                    'errors': form.errors
                }, status=status.HTTP_400_BAD_REQUEST)   
            
        except MethodSummary.DoesNotExist:
            return Response({
                'success': False,
                'message': '对象不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        except json.JSONDecodeError:
            return Response({
                'success': False,
                'message': '无效的JSON格式'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'服务器错误: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MethodSummaryDeleteView(DeleteView):
    model = MethodSummary
    success_url = reverse_lazy('courses:method_list')
    template_name = 'courses/method_summary_confirm_delete.html'

    def dispatch(self, request, *args, **kwargs):
        if request.method == 'DELETE':
            return self.delete(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return JsonResponse({'status': 'success'})
    
class MethodSummaryAddDeleteView(View):
    def post(self, request, method_id):
        """
        添加 MethodSummary 与 Exercise 的关联关系
        """
        try:
            # 获取 MethodSummary 对象
            method_summary = get_object_or_404(MethodSummary, pk=method_id)
            
            # 从请求数据中获取exercise_ids
            exercise_ids = json.loads(request.body).get('exercise_ids', [])
            
            # 获取所有Exercise对象
            exercises = Exercise.objects.filter(id__in=exercise_ids)
            
            # 添加关联关系
            method_summary.exercises.add(*exercises)
            
            return JsonResponse({
                'success': True,
                'message': f'成功添加 {len(exercises)} 个习题到方法总结 {method_summary.id}',
                'added_count': len(exercises)
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'添加失败: {str(e)}'
            }, status=500)

    def delete(self, request, method_id, exercise_id):
        """
        删除 MethodSummary 与 Exercise 的关联关系
        """
        try:
            # 获取 MethodSummary 和 Exercise 对象
            method_summary = get_object_or_404(MethodSummary, pk=method_id)
            exercise = get_object_or_404(Exercise, pk=exercise_id)
            
            # 删除关联关系
            method_summary.exercises.remove(exercise)
            
            return JsonResponse({
                'success': True,
                'message': f'成功删除习题 {exercise.id} 与方法总结 {method_summary.id} 的关联'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'删除失败: {str(e)}'
            }, status=500)


# 关联知识点-重写方法
class MethodSummaryAddKPDeleteView(View):
    def post(self, request, method_id):
        """
        添加 MethodSummary 与 Exercise 的关联关系
        """
        try:
            # 获取 MethodSummary 对象
            method_summary = get_object_or_404(MethodSummary, pk=method_id)
            
            # 从请求数据中获取kpoint_ids
            kpoints_ids = json.loads(request.body).get('kpoints_ids', [])
            
            # 获取所有KnowledgePoint对象
            knowledgepoints = KnowledgePoint.objects.filter(id__in=kpoints_ids)
            
            # 添加关联关系
            method_summary.knowledgePoint.add(*knowledgepoints)
            
            return JsonResponse({
                'success': True,
                'message': f'成功添加 {len(knowledgepoints)} 个习题到方法总结 {method_summary.id}',
                'added_count': len(knowledgepoints)
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'添加失败: {str(e)}'
            }, status=500)

    def delete(self, request, method_id, knowledge_id):
        """
        删除 MethodSummary 与 Knowledgepoint 的关联关系
        """
        try:
            # 获取 MethodSummary 和 Knowledgepoint 对象
            method_summary = get_object_or_404(MethodSummary, pk=method_id)
            knowledgepoints = get_object_or_404(KnowledgePoint, pk=knowledge_id)
            
            # 删除关联关系
            method_summary.knowledgePoint.remove(knowledgepoints)
            
            return JsonResponse({
                'success': True,
                'message': f'成功删除习题 {knowledgepoints.id} 与方法总结 {method_summary.id} 的关联'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'删除失败: {str(e)}'
            }, status=500)

def method_exercises(request, pk):
    """获取方法关联的习题列表"""
    try:
        method = get_object_or_404(MethodSummary, pk=pk)
        exercises = method.exercises.all().order_by('id')
        
        # 序列化习题数据
        exercise_list = []
        for exercise in exercises:
            exercise_list.append({
                'id': exercise.id,
                'title': exercise.title,
                'question_type': exercise.question_type,
                'question_type_text': exercise.get_question_type_display(),
                'content': exercise.content,
                'answer': exercise.answer,
                'analysis': exercise.analysis,
                'difficulty': exercise.difficulty
            })
            
        return JsonResponse({
            'status': 'success',
            'exercises': exercise_list
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


class ChapterDetailView(DetailView):
    model = Chapter
    template_name = 'courses/chapter_detail.html'
    context_object_name = 'chapter'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ChapterForm(instance=self.object)
        return context

class ChapterExerciseView(DetailView):
    model = Chapter
    template_name = 'courses/chapter_exercise.html'
    context_object_name = 'chapter'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ChapterForm(instance=self.object)
        return context
    
import math

class ChapterBasicView(DetailView):
    model = Chapter
    template_name = 'courses/chapter_basic.html'
    context_object_name = 'chapter'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ChapterForm(instance=self.object)
        
        # 计算学习进度(累计学时/预计学时*100并向上取整)
        if self.object.estimated_hours > 0:
            progress = (self.object.actual_hours / self.object.estimated_hours) * 100
            context['chapter'].progress = math.ceil(progress)
        else:
            context['chapter'].progress = 0  # 如果没有预计学时，进度设为0
            
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
    permission_classes = []  # 移除认证要求

    def perform_create(self, serializer):
        user_id = self.request.data.get('user')
        try:
            User = get_user_model()
            user = User.objects.get(pk=user_id) if user_id else None
            if user and not user.is_active:
                raise serializers.ValidationError({'user': '用户账户未激活'})
            serializer.save(user=user)
        except User.DoesNotExist:
            raise serializers.ValidationError({'user': '用户不存在'})
        except Exception as e:
            raise serializers.ValidationError(str(e))


class StudyRecordDetailAPI(generics.RetrieveUpdateDestroyAPIView):
    """当前用户单条学习记录的查看、修改、删除。"""

    serializer_class = StudyRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return StudyRecord.objects.filter(user=self.request.user)

class VideoListCreateAPIView(generics.ListCreateAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        # 支持按标题过滤
        title = self.request.query_params.get('title')
        if title:
            queryset = queryset.filter(title__icontains=title)
        # 支持按章节过滤
        chapter_id = self.request.query_params.get('chapter_id')
        if chapter_id:
            queryset = queryset.filter(chapter_id=chapter_id)
        return queryset

    def perform_create(self, serializer):
        # 处理文件上传
        video_file = self.request.FILES.get('video_file')
        if video_file:
            # 保存文件到media目录
            file_path = f'videos/{video_file.name}'
            full_path = f'media/{file_path}'
            with open(full_path, 'wb+') as destination:
                for chunk in video_file.chunks():
                    destination.write(chunk)
            
            # 获取视频时长(秒)
            duration = self.get_video_duration(full_path)
            
            # 保存文件路径和时长到模型
            serializer.save(
                url=f'/media/{file_path}',
                duration=duration  # 直接保存秒数
            )
        else:
            serializer.save()

    def get_video_duration(self, file_path):
        """使用ffmpeg获取视频时长(秒)"""
        import subprocess
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', 
                 '-of', 'default=noprint_wrappers=1:nokey=1', file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            duration_seconds = float(result.stdout)
            print(f"获取视频时长成功: {duration_seconds}秒")
            return duration_seconds
        except Exception as e:
            print(f"获取视频时长失败: {e}")
            return 10  # 默认10秒

class VideoRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def perform_update(self, serializer):
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # 删除关联的文件
        if instance.url and instance.url.startswith('/media/'):
            import os
            file_path = instance.url.replace('/media/', '')
            abs_path = os.path.join('media', file_path)
            if os.path.exists(abs_path):
                os.remove(abs_path)
        self.perform_destroy(instance)
        return Response(status=204)

def video_detail(request, pk):
    """视频详情页视图"""
    video = get_object_or_404(Video, pk=pk)
    comments = Comment.objects.filter(type='videos', type_id=pk).order_by('-created_at')
    return render(request, 'courses/video_detail.html', {
        'video': video,
        'comments': comments,
        'comment_type': 'videos',
        'type_id': pk
    })

class VideoPlayerView(APIView):
    def get(self, request):
        file_path = request.GET.get('url')
        if not file_path:
            return Response({'error': 'Missing file path'}, status=400)
        
        try:
            # 验证文件路径是否在允许的目录下
            if not file_path.startswith('/media/'):
                return Response({'error': 'Invalid file path'}, status=403)
            
            # 获取视频对象
            video = Video.objects.filter(url=file_path).first()
            if not video:
                return Response({'error': 'Video not found'}, status=404)
            
            # 获取视频评论（包含关联的时间戳信息）
            # comments = video.video_comment_relations.select_related('comment').annotate(
            #     content=F('comment__content'),
            #     user_name=F('comment__user__username')
            # ).order_by('-is_pinned', '-created_at')
            
            # 返回HTML页面用于播放视频
            return render(request, 'courses/video_player.html', {
                'video_url': file_path,
                'video': video,
                # 'comments': comments
            })
        except Exception as e:
            return Response({'error': str(e)}, status=500)

class VideoCommentView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            video_id = request.data.get('video_id')
            content = request.data.get('content')
            current_time = request.data.get('current_time', 0)
            
            if not video_id or not content:
                return Response({'error': 'Missing required fields'}, status=400)
                
            video = Video.objects.get(id=video_id)
            
            # 创建评论
            comment = Comment.objects.create(
                user=request.user,
                content=content,
                chapter=video.chapter
            )
            
            # 关联视频评论
            VideoComment.objects.create(
                video=video,
                comment=comment,
                timestamp=current_time
            )
            
            return Response({
                'success': True,
                'comment': {
                    'id': comment.id,
                    'content': comment.content,
                    'created_at': comment.created_at,
                    'user': {
                        'username': comment.user.username
                    },
                    'timestamp': current_time
                }
            })
        except Video.DoesNotExist:
            return Response({'error': 'Video not found'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=500)

class VideoCommentActionView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, comment_id):
        try:
            action = request.data.get('action')
            comment = Comment.objects.get(id=comment_id)
            video_comment = VideoComment.objects.get(comment=comment)
            
            if action == 'like':
                video_comment.likes_count += 1
                video_comment.save()
            elif action == 'pin':
                video_comment.is_pinned = not video_comment.is_pinned
                video_comment.save()
            elif action == 'delete':
                if request.user == comment.user or request.user.is_staff:
                    comment.delete()
                else:
                    return Response({'error': 'Permission denied'}, status=403)
            else:
                return Response({'error': 'Invalid action'}, status=400)
            
            return Response({'success': True})
        except Comment.DoesNotExist:
            return Response({'error': 'Comment not found'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=500)

class ExerciseSetListCreateAPI(generics.ListCreateAPIView):
    queryset = ExerciseSet.objects.all()
    serializer_class = ExerciseSetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 获取查询参数
        name = self.request.query_params.get('name')
        created_at_start = self.request.query_params.get('created_at_start')
        created_at_end = self.request.query_params.get('created_at_end')
        completion_count = self.request.query_params.get('completion_count')
        chapter_id = self.request.query_params.get('chapter_id')
        
        # 应用过滤条件
        if chapter_id:
            queryset = queryset.filter(chapter_id=chapter_id)
        if name:
            queryset = queryset.filter(name__icontains=name)
        if created_at_start and created_at_end:
            queryset = queryset.filter(created_at__range=[created_at_start, created_at_end])
        if completion_count:
            if completion_count == '0':
                queryset = queryset.filter(completion_count=0)
            elif completion_count == '1':
                queryset = queryset.filter(completion_count=1)
            elif completion_count == '2':
                queryset = queryset.filter(completion_count=2)
            elif completion_count == '3':
                queryset = queryset.filter(completion_count=3)
            elif completion_count == '4':
                queryset = queryset.filter(completion_count__gte=4)

        return queryset.prefetch_related('exercises')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ExerciseSetCreateSerializer
        return ExerciseSetSerializer

class ExerciseSetDetailAPI(generics.RetrieveUpdateDestroyAPIView):
    queryset = ExerciseSet.objects.all()
    serializer_class = ExerciseSetSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return super().get_queryset().prefetch_related('exercises')

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        # 如果是API请求，返回JSON数据
        if request.accepted_renderer.format == 'json':
            return Response(serializer.data)
            
        # 否则返回HTML页面
        return render(request, 'courses/exercise_set_detail.html', {
            'exercise_set': instance
        })

class ExerciseSetExercisesAPI(generics.ListAPIView):
    serializer_class = ExerciseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        exercise_set_id = self.kwargs['exercise_set_id']
        exercise_set = get_object_or_404(ExerciseSet, id=exercise_set_id)
        return exercise_set.exercises.all().order_by('id')

class ExerciseSetCompletionListCreateAPI(generics.ListCreateAPIView):
    queryset = ExerciseSetCompletion.objects.all()
    serializer_class = ExerciseSetCompletionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        exercise_set_id = self.request.query_params.get('exercise_set_id')
        if exercise_set_id:
            queryset = queryset.filter(exercise_set_id=exercise_set_id)
        return queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ExerciseSetCompletionCreateSerializer
        return ExerciseSetCompletionSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


