
from rest_framework import serializers
from .models import (
    Chapter, StudyRecord, KnowledgePoint, ExerciseAnswer,Video, Document,
    ExerciseSet, ExerciseSetCompletion, Exercise, MethodSummary,
    ReviewSetCompletion, ReviewSet, ReviewSetCompletion,KnowledgePointAnnotation
)

from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class KnowledgePointAnnotationSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        default=serializers.CurrentUserDefault()
    )
    user_display = serializers.SerializerMethodField()
    knowledge_point_title = serializers.SerializerMethodField()

    class Meta:
        model = KnowledgePointAnnotation
        fields = [
            'id', 'knowledge_point', 'knowledge_point_title', 'user', 'user_display', 
            'content', 'created_at', 'updated_at', 'content_tag','quote'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_user_display(self, obj):
        return obj.user.username if obj.user else None

    def get_knowledge_point_title(self, obj):
        return obj.knowledge_point.title if obj.knowledge_point else None
    

class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = ['id', 'question_type', 'title', 'content', 'difficulty']

class MethodSummarySerializer(serializers.ModelSerializer):
    exercise_count = serializers.SerializerMethodField()
    exercises = ExerciseSerializer(many=True, read_only=True)
    chapter = serializers.IntegerField(source='chapter.id', read_only=True)
    chapter_title = serializers.SerializerMethodField()
    
    class Meta:
        model = MethodSummary
        fields = ['id','name', 'description','note','exercise_count','exercises', 'chapter','chapter_title','created_at','difficulty_level','important_level']
    
    def get_exercise_count(self, obj):
        return obj.exercises.count()
        
    def get_chapter_title(self, obj):
        # 优先使用模型中的chapter_title字段，如果不存在则从关联的chapter获取
        return obj.chapter_title or (obj.chapter.title if obj.chapter else None)
    
class MethodSummaryCreateSerializer(serializers.ModelSerializer):
    exercise_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        default=[]
    )
    
    class Meta:
        model = MethodSummary
        fields = ['name', 'chapter', 'exercise_ids','id']
    
    def validate_exercise_ids(self, value):
        # 允许空数组，表示不关联任何习题
        return value or []
    
    def create(self, validated_data):
        exercise_ids = validated_data.pop('exercise_ids', [])
        exercise_summary = MethodSummary.objects.create(**validated_data)
        
        # 如果有提供exercise_ids，则添加关联习题
        if exercise_ids:
            exercises = Exercise.objects.filter(id__in=exercise_ids)
            exercise_summary.exercises.add(*exercises)
        
        return exercise_summary

class ExerciseSetCompletionSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = ExerciseSetCompletion
        fields = [
            'id',
            'user',
            'user_name',
            'exercise_set',
            'score',
            'correct_count',
            'total_count',
            'time_spent',
            'completed_at'
        ]
        extra_kwargs = {
            'time_spent': {'required': True}
        }

class ExerciseSetSerializer(serializers.ModelSerializer):
    exercises = ExerciseSerializer(many=True, read_only=True)
    chapter_title = serializers.CharField(source='chapter.title', read_only=True)
    chapter_id = serializers.IntegerField(source='chapter.id', read_only=True)
    
    class Meta:
        model = ExerciseSet
        fields = ['id', 'name', 'chapter', 'chapter_id', 'chapter_title', 
                 'suggested_time', 'exercises', 'created_at', 'completion_count',
                 'last_completed_at']

class ExerciseSetCreateSerializer(serializers.ModelSerializer):
    exercise_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=True
    )
    
    class Meta:
        model = ExerciseSet
        fields = ['name', 'chapter', 'suggested_time', 'exercise_ids']
    
    def validate_exercise_ids(self, value):
        if not value:
            raise serializers.ValidationError("至少选择一个习题")
        return value
    
    def create(self, validated_data):
        exercise_ids = validated_data.pop('exercise_ids')
        exercise_set = ExerciseSet.objects.create(**validated_data)
        
        # 添加习题到练习集
        exercises = Exercise.objects.filter(id__in=exercise_ids)
        exercise_set.exercises.add(*exercises)
        
        return exercise_set

class ExerciseSetCompletionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseSetCompletion
        fields = ['exercise_set', 'time_spent', 'score', 'correct_count', 'total_count']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

# 复习集序列化器
class ReviewSetSerializer(serializers.ModelSerializer):
    exercises = ExerciseSerializer(many=True, required=False)
    chapter_title = serializers.CharField(source='chapter.title', read_only=True)
    chapter_id = serializers.IntegerField(source='chapter.id', read_only=True)
    
    class Meta:
        model = ReviewSet
        fields = ['id', 'name', 'chapter', 'chapter_id', 'chapter_title', 
                 'exercises', 'created_at', 'completion_count',
                 'last_completed_at']

class ReviewSetCreateSerializer(serializers.ModelSerializer):
    exercise_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=True
    )
    
    class Meta:
        model = ReviewSet
        fields = ['name', 'chapter', 'exercise_ids']
    
    def validate_exercise_ids(self, value):
        if not value:
            raise serializers.ValidationError("至少选择一个习题")
        return value
    
    def create(self, validated_data):
        exercise_ids = validated_data.pop('exercise_ids')
        review_set = ReviewSet.objects.create(**validated_data)
        
        # 添加习题到复习集
        exercises = Exercise.objects.filter(id__in=exercise_ids)
        review_set.exercises.add(*exercises)
        
        return review_set

class ReviewSetCompletionSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = ReviewSetCompletion
        fields = [
            'id',
            'user',
            'user_name',
            'review_set',
            'score',
            'correct_count',
            'total_count',
            'time_spent',
            'completed_at'
        ]
        extra_kwargs = {
            'time_spent': {'required': True}
        }

class ReviewSetCompletionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewSetCompletion
        fields = ['review_set', 'time_spent', 'score', 'correct_count', 'total_count']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ChapterSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    
    class Meta:
        model = Chapter
        fields = [
            'id',
            'title',
            'subject',
            'subject_name',
            'description',
            'order',
            'estimated_hours',
            'actual_hours',
            'progress'
        ]

# class VideoSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Video
#         fields = ['id', 'title', 'url', 'duration', 'chapter']
#         extra_kwargs = {
#             'chapter': {'required': False}
#         }

class StudyRecordSerializer(serializers.ModelSerializer):
    duration_display = serializers.CharField(read_only=True)
    
    class Meta:
        model = StudyRecord
        fields = [
            'user',
            'created_date',
            'start_time',
            'end_time',
            'duration',
            'duration_display',
            'page_type',
            'chapter',
            'subject_name',
            'chapter_name',
            'learning_content',
            'description'
        ]
        extra_kwargs = {
            'user': {'required': False}  # 从请求中自动获取
        }

class KnowledgePointSerializer(serializers.ModelSerializer):
    chapter_title = serializers.CharField(source='chapter.title', read_only=True)
    parent_title = serializers.CharField(source='parent.title', read_only=True)
    
    class Meta:
        model = KnowledgePoint
        fields = [
            'title',
            'description',
            'content',
            'difficulty',
            'memory_level',
            'mastery_level',
            'chapter',
            'chapter_title',
            'parent',
            'parent_title',
            'documents',
            'videos',
            'exercises',
            'created',
            'modified',
            'brother_id',
        ]
        extra_kwargs = {
            'parent': {'required': False},
            'documents': {'required': False},
            'videos': {'required': False},
            'exercises': {'required': False}
        }

class KnowledgePointSerializer_PUT(serializers.ModelSerializer):
    brother_id = serializers.IntegerField(required=False)
    
    class Meta:
        model = KnowledgePoint
        fields = [
            'title',
            'description',
            'brother_id'
        ]
    
    def update(self, instance, validated_data):
        brother_id = validated_data.pop('brother_id', None)
        if brother_id is not None:
            # 确保brother_id是正整数
            brother_id = max(1, int(brother_id))
    
            # 只更新当前知识点的brother_id
            instance.brother_id = brother_id
            instance.save()

        # 更新其他字段
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance


class VideoSerializer(serializers.ModelSerializer):
    chapter = serializers.PrimaryKeyRelatedField(
        queryset=Chapter.objects.all(),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Video
        fields = ['id', 'title', 'url', 'duration', 'chapter']
        extra_kwargs = {
            'title': {'required': True},
            'url': {'required': False},
            'duration': {'required': False}  # 移除duration必填验证
        }

class DocumentSerializer_post(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = ['id', 'title', 'file', 'file_url', 'chapter']
        extra_kwargs = {
            'file': {'write_only': True}
        }
        
    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None

class ExerciseSerializer(serializers.ModelSerializer):
    question_type_display = serializers.CharField(source='get_question_type_display', read_only=True)
    
    class Meta:
        model = Exercise
        fields = [
            'id', 
            'question_type',
            'question_type_display',
            'content',
            'options',
            'answer',
            'analysis',
            'difficulty',
            'memory_level',
            'mastery_level',
            'wrong_count',
            'correct_count',
            'title',
            'chapter',
            'updated_at'
        ]
        extra_kwargs = {
            'chapter': {'required': False},
        }
class ExerciseAnswerSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source='exercise.title', read_only=True)
    chapter_id = serializers.IntegerField(source='exercise.chapter.id', read_only=True)
    question_type_display = serializers.CharField(source='exercise.get_question_type_display', read_only=True)
    wrong_count = serializers.IntegerField(source='exercise.wrong_count',read_only=True)
    id = serializers.IntegerField(source='exercise.id',read_only=True)
    class Meta:
        model = ExerciseAnswer
        fields = [
            'id', 
            'title',
            'question_type_display',
            'difficulty',
            'memory_level',
            'mastery_level',
            'wrong_count',
            'chapter_id',
            'wrong_count',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {
            'chapter_id': {'required': False},
            'wrong_count': {'required': False}
        }

class DocumentSerializer_get(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = ['id', 'title', 'file', 'chapter', 'created_at']
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {
            'file': {'required': True},
            'chapter': {'required': True}
        }
        
    def get_created_at(self, obj):
        return timezone.localtime(obj.created_at).strftime('%Y-%m-%d %H:%M')
    
