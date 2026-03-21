
from rest_framework.views import APIView
from rest_framework.response import Response
from ..models import StudyRecord
from ..serializers import StudyRecordSerializer

class StudyRecordsAPIView(APIView):
    def get(self, request):
        # 获取查询参数
        created_date_start = request.GET.get('created_date_start')
        created_date_end = request.GET.get('created_date_end')
        page_type = request.GET.get('page_type')
        learning_content = request.GET.get('learning_content')
        chapter_id = request.GET.get('chapter')
        page = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', 10)
        
        # 获取当前用户的学习记录
        queryset = StudyRecord.objects.filter(user=request.user)
        
        # 应用过滤条件
        if created_date_start and created_date_end:
            queryset = queryset.filter(created_date__range=[created_date_start, created_date_end])
        if page_type:
            queryset = queryset.filter(page_type=page_type)
        if learning_content:
            queryset = queryset.filter(learning_content__icontains=learning_content)
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
