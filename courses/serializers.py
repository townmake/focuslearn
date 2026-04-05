
from rest_framework import serializers
from .models import (
    Chapter, StudyRecord, KnowledgePoint, Video, Document,
    KnowledgePointAnnotation,
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
            'content', 'created_at', 'updated_at', 'content_tag', 'quote'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_user_display(self, obj):
        return obj.user.username if obj.user else None

    def get_knowledge_point_title(self, obj):
        return obj.knowledge_point.title if obj.knowledge_point else None


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


class StudyRecordSerializer(serializers.ModelSerializer):
    duration_display = serializers.CharField(read_only=True)

    class Meta:
        model = StudyRecord
        fields = [
            'id',
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
            'description',
        ]
        read_only_fields = ['id', 'user', 'duration_display']
        extra_kwargs = {
            'user': {'required': False},
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
            'chapter',
            'chapter_title',
            'parent',
            'parent_title',
            'documents',
            'videos',
            'created',
            'modified',
            'brother_id',
        ]
        extra_kwargs = {
            'parent': {'required': False},
            'documents': {'required': False},
            'videos': {'required': False},
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
            brother_id = max(1, int(brother_id))
            instance.brother_id = brother_id
            instance.save()

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
            'duration': {'required': False}
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
