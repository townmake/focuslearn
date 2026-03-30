from rest_framework import serializers
from django.utils import timezone
from datetime import datetime, date, time
from .models import TaskList, Task, Subject, Chapter, DailySummary, Words
import pytz

class CustomDateField(serializers.Field):
    """
    自定义日期字段，处理 datetime 对象
    """
    def to_representation(self, value):
        """
        将 datetime 或 date 对象转换为 ISO 格式字符串
        """
        if value is None:
            return None
        
        # 如果是 date 对象，转换为字符串
        if isinstance(value, date):
            return value.isoformat()
        
        # 如果是 datetime 对象，确保时区处理
        if isinstance(value, datetime):
            # 如果是 naive datetime，使用当前时区
            if value.tzinfo is None:
                value = timezone.make_aware(value)
            return value.isoformat()
        
        return value

    def to_internal_value(self, data):
        """
        将输入转换为日期对象
        """
            # 处理 None 或空字符串
        if data is None or data == '':
            return None
        
        if isinstance(data, str):
            return datetime.strptime(data, '%Y-%m-%d').date()
        return data


class TaskSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    subject_color = serializers.CharField(source='subject.color', read_only=True)
    chapter_name = serializers.CharField(source='chapter.title', read_only=True)
    
    # 使用自定义日期字段
    start_date = CustomDateField()
    end_date = CustomDateField()
    repeat_ends = CustomDateField()
    
    # 动态添加只读字段
    start = serializers.SerializerMethodField(read_only=True)
    end = serializers.SerializerMethodField(read_only=True)
    
    def get_start(self, obj):
        """
        为 FullCalendar 组合开始时间
        """
        if not obj.start_date or not obj.start_time:
            return None
        
        try:
            # 组合日期和时间（墙钟时间），再用 make_aware 绑定当前时区，避免 replace+pytz 错位
            local_datetime = datetime.combine(obj.start_date, obj.start_time)
            if timezone.is_naive(local_datetime):
                local_datetime = timezone.make_aware(local_datetime)
            return local_datetime.replace(microsecond=0).isoformat()
        except Exception as e:
            print(f"Error converting start datetime: {e}")
            return None

    def get_end(self, obj):
        """
        为 FullCalendar 组合结束时间
        """
        if not obj.end_date or not obj.end_time:
            return None
        
        try:
            local_datetime = datetime.combine(obj.end_date, obj.end_time)
            if timezone.is_naive(local_datetime):
                local_datetime = timezone.make_aware(local_datetime)
            return local_datetime.replace(microsecond=0).isoformat()
        except Exception as e:
            print(f"Error converting end datetime: {e}")
            return None
    
    class Meta:
        model = Task
        fields = [
            'id', 'user', 'title', 'description', 'is_completed',
            'start_date', 'start_time', 'end_date', 'end_time', 
            'start',  # 新增字段，用于 FullCalendar
            'end',    # 新增字段，用于 FullCalendar
            'repeat_type', 'repeat_ends','subject', 'chapter', 'subject_name', 'chapter_name',
            'focus_level', 'energy_level', 'created_at', 'updated_at',
            'subject_color', 'parent_series', 'is_exception', 'original_date'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']

        def validate(self, data):
            """
            自定义验证方法，处理日期和时间的验证
            """
            # 检查日期
            if data.get('start_date') and data.get('end_date'):
                if data['start_date'] > data['end_date']:
                    raise serializers.ValidationError({
                        "end_date": "结束日期不能早于开始日期"
                    })
            
            # 检查时间（仅在日期相同时）
            if (data.get('start_date') == data.get('end_date') and 
                data.get('start_time') is not None and 
                data.get('end_time') is not None):
                
                # 使用 datetime.time 对象进行比较
                if data['start_time'] > data['end_time']:
                    raise serializers.ValidationError({
                        "end_time": "结束时间不能早于开始时间"
                    })
            
            # 如果时间为空，设置默认时间
            if data.get('start_time') is None:
                data['start_time'] = datetime.time(9, 0)  # 默认 9:00
            
            if data.get('end_time') is None:
                data['end_time'] = datetime.time(10, 0)  # 默认 10:00
            return data
    
    def create(self, validated_data):
        """
        创建任务时的处理
        """
        # 确保用户字段被设置
        validated_data['user'] = self.context['request'].user
        
        return super().create(validated_data)
    
class TaskBulkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            'user', 'title', 'description', 'is_completed',
            'start_date', 'start_time', 'end_date', 'end_time', 
            'repeat_type', 'repeat_ends','subject', 'chapter', 
            'focus_level', 'energy_level', 'parent_series'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    def create(self, validated_data):

        tasks = [Task(**item) for item in validated_data]
        return Task.objects.bulk_create(tasks)


class TaskListSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)
    
    class Meta:
        model = TaskList
        fields = [
            'id', 'title', 'color', 'order', 'tasks',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate_color(self, value):
        """验证颜色代码格式"""
        if not value.startswith('#') or len(value) != 7:
            raise serializers.ValidationError("请提供有效的HEX颜色代码，例如：#FF0000")
        return value

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = [
            'id', 'name', 'description', 'color',
            'order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class ChapterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapter
        fields = [
            'id', 'subject', 'title', 'description',
            'order'
        ]

class DailySummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = DailySummary
        fields = [
            'id', 'user', 'date', 'description',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']

class WordsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Words
        fields = [
            'id', 'word', 'translation', 'example_sentence',
            'created_at', 'updated_at', 'level'
        ]
        read_only_fields = ['created_at', 'updated_at']