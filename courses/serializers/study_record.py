
from rest_framework import serializers
from ..models import StudyRecord

class StudyRecordSerializer(serializers.ModelSerializer):
    created_date = serializers.DateField(format="%Y-%m-%d")
    start_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    end_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    chapter_name = serializers.CharField(source='chapter.title', read_only=True)
    
    class Meta:
        model = StudyRecord
        fields = [
            'id',
            'created_date',
            'start_time',
            'end_time',
            'duration',
            'page_type',
            'subject_name',
            'chapter_name',
            'learning_content',
            'description'
        ]
