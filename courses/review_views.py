
from django.views.generic import ListView, CreateView, UpdateView, DetailView, View
from django.http import JsonResponse, HttpResponse
from django.db import IntegrityError
from .models import Exercise,Chapter,ReviewSet,ExerciseAnswer,ReviewSetCompletion
from .serializers import (
    ExerciseSerializer, ReviewSetSerializer, ExerciseAnswerSerializer,
    ReviewSetSerializer,ReviewSetCompletionSerializer,ExerciseAnswerSerializer,
    ReviewSetCreateSerializer,ReviewSetCompletionCreateSerializer
    )
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework import generics, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
import json
from rest_framework import permissions
from django.db.models import OuterRef, Subquery
from datetime import datetime
from django.utils import timezone as django_timezone
from django.db.models import F
from django.shortcuts import render, get_object_or_404
from django.urls import reverse, reverse_lazy

class ExerciseFilterView(APIView):
    """习题筛选视图"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # 获取查询参数
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        min_difficulty = request.query_params.get('min_difficulty')
        max_difficulty = request.query_params.get('max_difficulty')
        min_memory = request.query_params.get('min_memory')
        max_memory = request.query_params.get('max_memory')
        min_mastery = request.query_params.get('min_mastery')
        max_mastery = request.query_params.get('max_mastery')
        min_error_count = request.query_params.get('min_error_count')
        chapter_id = request.query_params.get('chapter')

        # 1. 构建基础查询条件
        base_filters = {}
        if chapter_id:
            base_filters['exercise__chapter_id'] = chapter_id
            
        if start_date and end_date:
            try:
                start_datetime = django_timezone.make_aware(datetime.strptime(start_date + ' 00:00:00', '%Y-%m-%d %H:%M:%S'))
                end_datetime = django_timezone.make_aware(datetime.strptime(end_date + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
                base_filters['created_at__range'] = [start_datetime, end_datetime]
            except ValueError:
                return Response(
                    {'error': '日期格式无效，请使用YYYY-MM-DD格式'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # 获取每个Exercise的最新ExerciseAnswer ID
        latest_answers = ExerciseAnswer.objects.filter(
            exercise=OuterRef('exercise'),
            **base_filters
        ).order_by('-created_at')
        
        # 2. 构建基础查询
        exercises = ExerciseAnswer.objects.annotate(
            latest_answer_id=Subquery(latest_answers.values('id')[:1])
        ).filter(
            id=F('latest_answer_id')
        ).select_related('exercise', 'exercise__chapter')
        
        # 3. 应用其他筛选条件

        if min_error_count:
            exercises = exercises.filter(exercise__wrong_count__gte=min_error_count)
        if min_difficulty:
            exercises = exercises.filter(difficulty__gte=min_difficulty)
        if max_difficulty:
            exercises = exercises.filter(difficulty__lte=max_difficulty)
        if min_memory:
            exercises = exercises.filter(memory_level__gte=min_memory)
        if max_memory:
            exercises = exercises.filter(memory_level__lte=max_memory)
        if min_mastery:
            exercises = exercises.filter(mastery_level__gte=min_mastery)
        if max_mastery:
            exercises = exercises.filter(mastery_level__lte=max_mastery)

        # 序列化结果
        serializer = ExerciseAnswerSerializer(exercises, many=True)
        return Response({
            'exercises': serializer.data,
            'debug': {
                'total_count': exercises.count(),
                'date_range': f"{start_datetime} to {end_datetime}" if start_date and end_date else None,
                'chapter_id': chapter_id,
                'min_error_count': min_error_count,
                'difficulty_range': f"{min_difficulty}-{max_difficulty}" if min_difficulty or max_difficulty else None,
                'memory_range': f"{min_memory}-{max_memory}" if min_memory or max_memory else None,
                'mastery_range': f"{min_mastery}-{max_mastery}" if min_mastery or max_mastery else None
            }
        })

class ReviewSetCreateView(APIView):
    """创建复习集视图"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        # 解析JSON请求体
        try:
            if not request.data:
                return Response(
                    {'error': '请求数据不能为空'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            try:
                data = request.data if isinstance(request.data, dict) else json.loads(request.data)
            except (json.JSONDecodeError, AttributeError) as e:
                return Response(
                    {
                        'error': '无效的JSON格式',
                        'detail': str(e),
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            name = data.get('name')
            chapter_id = data.get('chapter_id')
            exercise_ids = data.get('exercise_ids', [])
            
            # 验证exercise_ids是否为列表
            if not isinstance(exercise_ids, list):
                return Response(
                    {'error': 'exercise_ids必须是数组'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 确保所有ID都是整数
            try:
                exercise_ids = [int(x) for x in exercise_ids]
            except (ValueError, TypeError):
                return Response(
                    {'error': '习题ID必须为数字'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 校验非空
            if not exercise_ids:
                return Response(
                    {'error': '请选择至少一个习题'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                # 获取或创建章节
                chapter = None
                if chapter_id:
                    chapter = get_object_or_404(Chapter, pk=chapter_id)
                
                # 生成默认名称
                if not name:
                    now = datetime.now(timezone.utc)
                    name = now.strftime('%Y年%m月%d日计划复习')
                    
                    # 检查名称是否已存在
                    if ReviewSet.objects.filter(name=name).exists():
                        name = now.strftime('%Y年%m月%d日%H时%M分%S秒计划复习')
                
                # 创建复习集
                review_set = ReviewSet.objects.create(
                    name=name,
                    chapter=chapter
                )
                
                # 添加习题
                exercises = Exercise.objects.filter(id__in=exercise_ids)
                if exercises.count() != len(exercise_ids):
                    missing_ids = set(exercise_ids) - set(ex.id for ex in exercises)
                    return Response(
                        {
                            'error': '部分习题ID不存在',
                            'missing_ids': list(missing_ids)
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                review_set.exercises.add(*exercises)
                
                # 序列化返回
                try:
                    serializer = ReviewSetSerializer(review_set)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                except Exception as e:
                    return Response(
                        {'error': '序列化复习集失败', 'detail': str(e)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                
            except IntegrityError as e:
                return Response(
                    {'error': '创建复习集失败: 数据库完整性错误', 'detail': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response(
                {'error': '创建复习集失败', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
        
# 复习集视图类
class ReviewSetListCreateAPI(generics.ListCreateAPIView):
    queryset = ReviewSet.objects.all()
    serializer_class = ReviewSetSerializer
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
            return ReviewSetCreateSerializer
        return ReviewSetSerializer

class ReviewSetDetailAPI(generics.RetrieveUpdateDestroyAPIView):
    queryset = ReviewSet.objects.all()
    serializer_class = ReviewSetSerializer
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
        return render(request, 'courses/review_set_detail.html', {
            'review_set': instance
        })

class ReviewSetExercisesView(APIView):
    """获取复习集包含的习题列表"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, id):
        review_set = get_object_or_404(ReviewSet, pk=id)
        exercises = review_set.exercises.all()
        serializer = ExerciseSerializer(exercises, many=True)
        return Response(serializer.data)

class ReviewSetCompletionListCreateAPI(generics.ListCreateAPIView):
    queryset = ReviewSetCompletion.objects.all()
    serializer_class = ReviewSetCompletionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        review_set_id = self.request.query_params.get('review_set_id')
        if review_set_id:
            queryset = queryset.filter(review_set_id=review_set_id)
        return queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ReviewSetCompletionCreateSerializer
        return ReviewSetCompletionSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

def review_set_exercise_delete(request, review_set_id, exercise_id):
    review_set = get_object_or_404(ReviewSet, id=review_set_id)
    exercise = get_object_or_404(Exercise, id=exercise_id)
    
    # 从多对多关系中移除
    review_set.exercises.remove(exercise)
    
    return JsonResponse({
        'success': True,
        'message': '已从习题集中移除该习题',
        'remaining_count': review_set.exercises.count()
    })
    
def review_set_exercise_add(request, review_set_id):
    """向习题集中添加习题"""
    review_set = get_object_or_404(ReviewSet, id=review_set_id)
    
    if request.method == 'POST':
        try:
            # 从JSON请求体中获取数据
            data = json.loads(request.body)
            exercise_ids = data.get('exercise_ids', [])
            
            if not exercise_ids:
                return JsonResponse({
                    'success': False,
                    'message': '请提供要添加的习题ID'
                }, status=400)
                
            # 获取所有有效的习题
            exercises = Exercise.objects.filter(id__in=exercise_ids)
            if exercises.count() != len(exercise_ids):
                return JsonResponse({
                    'success': False,
                    'message': '部分习题ID无效'
                }, status=400)
                
            # 批量添加到习题集
            review_set.exercises.add(*exercises)
            
            return JsonResponse({
                'success': True,
                'message': f'成功添加 {len(exercise_ids)} 个习题到习题集',
                'new_count': review_set.exercises.count()
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'数据解析错误: {str(e)}'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'添加失败: {str(e)}'
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'message': '无效的请求方法'
    }, status=405)

class ReviewSetStartQuickAPI(generics.RetrieveAPIView):
    """开始答题，返回第一道习题"""
    serializer_class = ExerciseSerializer
    
    def get_object(self):
        review_set = get_object_or_404(ReviewSet, id=self.kwargs['review_set_id'])
        exercises = review_set.exercises.all().order_by('id')
        
        if not exercises.exists():
            return None
            
        first_exercise = exercises.first()
        
        # 如果是完形填空或阅读理解，返回主问题和所有子问题
        if first_exercise.question_type in ['cloze_test', 'reading_answer']:
            sub_questions = Exercise.objects.filter(parent_id=first_exercise.id).order_by('id')
            if not sub_questions.exists():
                return first_exercise
            return {
                'main_question': first_exercise,
                'sub_questions': sub_questions
            }
        return first_exercise

    def retrieve(self, request, *args, **kwargs):
        review_set = get_object_or_404(ReviewSet, id=self.kwargs['review_set_id'])
        review_set_id = self.kwargs['review_set_id']
        
        # 如果是API请求，返回JSON数据
        if request.accepted_renderer.format == 'json':
            exercise = self.get_object()
            if not exercise:
                return Response(
                    {'error': '练习集中没有习题'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
                
            if isinstance(exercise, dict):  # 处理完形填空/阅读理解
                serializer = self.get_serializer(exercise['main_question'])
                sub_serializer = self.get_serializer(exercise['sub_questions'], many=True)
                return Response({
                    'main_question': serializer.data,
                    'sub_questions': sub_serializer.data
                })
                
            serializer = self.get_serializer(exercise)
            return Response(serializer.data)
        
        # 否则返回答题页面
        exercise_count = review_set.exercises.count()
        if exercise_count == 0:
            return Response(
                {'error': '练习集中没有习题'}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        from django.shortcuts import render
        return render(request, 'courses/review_set_quiz_quick.html', {
            'review_set':review_set,
            'exercise_count': exercise_count,
            'review_set_id': review_set_id
        })

class ReviewSetNextAPI(generics.RetrieveAPIView):
    """获取下一道习题"""
    serializer_class = ExerciseSerializer
    
    def get_object(self):
        review_set = get_object_or_404(ReviewSet, id=self.kwargs['review_set_id'])
        current_exercise = get_object_or_404(Exercise, id=self.kwargs['current_exercise_id'])
        
        # 获取当前习题在练习集中的位置
        exercises = list(review_set.exercises.order_by('id'))
        try:
            current_index = exercises.index(current_exercise)
            next_exercise = exercises[current_index + 1]
            
            # 处理完形填空/阅读理解
            if next_exercise.question_type in ['cloze_test', 'reading_answer']:
                return {
                    'main_question': next_exercise,
                    'sub_questions': Exercise.objects.filter(parent_id=next_exercise.id).order_by('id')
                }
            return next_exercise
        except (ValueError, IndexError):
            return None  # 没有下一题了

    def retrieve(self, request, *args, **kwargs):
        exercise = self.get_object()
        if not exercise:
            return Response(
                {'message': '已经是最后一道题了'}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        if isinstance(exercise, dict):  # 处理完形填空/阅读理解
            serializer = self.get_serializer(exercise['main_question'])
            sub_serializer = self.get_serializer(exercise['sub_questions'], many=True)
            return Response({
                'main_question': serializer.data,
                'sub_questions': sub_serializer.data
            })
            
        serializer = self.get_serializer(exercise)
        return Response(serializer.data)

class ReviewSetSubmitAPI(generics.CreateAPIView):
    """提交练习集并创建完成记录"""
    serializer_class =ReviewSetCompletionSerializer

    def create(self, request, *args, **kwargs):
        try:
            review_set = get_object_or_404(ReviewSet, pk=kwargs['review_set_id'])
            user = request.user
            answers_data = request.data.get('answers', {})
            total_time = int(request.data.get('total_time', 0))

            answer_records = []
            correct_count = 0
            
            from django.db import transaction
            with transaction.atomic():
                # 1. 先创建临时练习集完成记录(correct_count=0)
                completion = ReviewSetCompletion.objects.create(
                    user=user,
                    review_set=review_set,
                    score=0,
                    correct_count=0,
                    total_count=review_set.exercises.count(),
                    time_spent=total_time
                )

                # 2. 创建所有习题答题记录并计算正确数量
                correct_count = 0
                for exercise in review_set.exercises.all():
                    exercise_id_str = str(exercise.id)  # 统一转换为字符串
                    answer_info = answers_data.get(exercise_id_str, {})
                    user_answer = answer_info.get('answer', '')
                    time_spent = answer_info.get('time_spent', 0)
                    difficulty = answer_info.get('difficulty', 0)
                    memory_level = answer_info.get('memory_level', 0)
                    mastery_level = answer_info.get('mastery_level', 0)
                    is_correct = answer_info.get('is_correct')
                    # 处理主习题
                    if(not is_correct and len(user_answer) > 0):
                        is_correct = str(user_answer) == str(exercise.answer)
                    if is_correct:
                        correct_count += 1
                    
                    answer_record = ExerciseAnswer.objects.create(
                        exercise=exercise,
                        user=user,
                        review_set_completion=completion,
                        answer=user_answer,
                        is_correct=is_correct,
                        time_spent=time_spent,
                        difficulty=difficulty,
                        memory_level=memory_level,
                        mastery_level=mastery_level,
                    )
                    answer_records.append({
                        'exercise_id': exercise.id,
                        'answer_id': answer_record.id,
                        'is_correct': is_correct
                    })
                    
                    # 处理子习题（完形填空/阅读理解）
                    if exercise.question_type in ['cloze_test', 'reading_answer']:
                        for sub_exercise in Exercise.objects.filter(parent_id=exercise.id):
                            sub_answer_info = user_answer.get(str(sub_exercise.id), {})
                            sub_answer = sub_answer_info.get('answer', '')
                            sub_time_spent = sub_answer_info.get('time_spent', 0)
                            
                            sub_is_correct = str(sub_answer) == str(sub_exercise.answer)
                            if sub_is_correct:
                                correct_count += 1
                            
                            sub_record = ExerciseAnswer.objects.create(
                                exercise=sub_exercise,
                                user=user,
                                review_set_completion=completion,
                                answer=sub_answer,
                                is_correct=sub_is_correct,
                                time_spent=sub_time_spent
                            )
                            answer_records.append({
                                'exercise_id': sub_exercise.id,
                                'answer_id': sub_record.id,
                                'is_correct': sub_is_correct
                            })

                # 3. 更新练习集完成记录的正确数量和分数
                completion.correct_count = correct_count
                completion.score = (correct_count / review_set.exercises.count()) * 100 if review_set.exercises.count() else 0
                completion.save()


            return Response({
                'redirect_url': reverse('courses:review-set-result', kwargs={
                    'review_set_id': review_set.id,
                    'completion_id': completion.id
                }),
                'completion_id': completion.id,
                'message': '提交成功'
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def calculate_score(self, data, review_set):
        correct = 0
        answers = data.get('answers', {})
        for exercise in review_set.exercises.all():
            if str(answers.get(str(exercise.id))) == str(exercise.answer):
                correct += 1
        return (correct / review_set.exercises.count()) * 100 if review_set.exercises.count() else 0
    """提交练习集并创建完成记录"""

def review_set_result(request, review_set_id, completion_id):
    """显示练习集结果"""
    review_set = get_object_or_404(ReviewSet, id=review_set_id)
    completion = get_object_or_404(ReviewSetCompletion, id=completion_id)
    
    # 获取本次提交的答题记录
    answer_records = ExerciseAnswer.objects.filter(
        review_set_completion=completion,
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
        'review_set': review_set,
        'results': results,
        'correct_count': correct_count,
        'accuracy': completion.score
    }
    
    return render(request, 'courses/review_result.html', context)
