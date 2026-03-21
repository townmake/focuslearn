
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import StudyRecord, Chapter
import logging

logger = logging.getLogger(__name__)

class StudyRecordCreateAPI(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        data = request.data
        try:
            # 验证必要字段
            required_fields = ['pageType', 'duration', 'startTime', 'endTime']
            for field in required_fields:
                if field not in data:
                    return Response(
                        {'error': f'缺少必要字段: {field}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # 处理章节信息
            chapter = None
            subject_name = ""
            chapter_name = ""
            
            if data['pageType'] == 'chapter' and 'pageId' in data:
                try:
                    chapter = Chapter.objects.get(id=data['pageId'])
                    subject_name = chapter.subject.name if chapter.subject else ""
                    chapter_name = chapter.title
                except Chapter.DoesNotExist:
                    logger.warning(f"章节不存在: {data['pageId']}")

            # 创建学习记录
            record = StudyRecord.objects.create(
                user=request.user,
                created_date=timezone.now().date(),
                start_time=data['startTime'],
                end_time=data['endTime'],
                duration=data['duration'],
                page_type=data['pageType'],
                chapter=chapter,
                subject_name=subject_name,
                chapter_name=chapter_name,
                learning_content=data.get('activeTab', ''),
                description=data.get('description', '')
            )

            return Response(
                {
                    'id': record.id,
                    'message': '学习记录创建成功',
                    'duration_display': record.duration_display
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            logger.error(f"创建学习记录失败: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
