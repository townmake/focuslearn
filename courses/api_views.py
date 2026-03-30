
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Max
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Chapter, KnowledgePoint, KnowledgePointAnnotation
from courses.views import get_tree_data
from .serializers import (
    KnowledgePointSerializer,
    KnowledgePointSerializer_PUT,
    VideoSerializer,
    DocumentSerializer_get,
    ExerciseSerializer,
    KnowledgePointAnnotationSerializer
)
from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.utils.dateformat import DateFormat



class KnowledgePointAnnotationListAPI(APIView):
    """知识点注释列表API"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """查询知识点下的所有注释"""
        knowledge_point = get_object_or_404(KnowledgePoint, pk=pk)
        annotations = KnowledgePointAnnotation.objects.filter(
            knowledge_point=knowledge_point
        ).order_by('created_at')
        # serializer = KnowledgePointAnnotationSerializer(annotations, many=True)
        # return Response(serializer.data)
        # 使用自定义序列化方法
        formatted_annotations = self.format_annotations(annotations)
        
        return Response(formatted_annotations, status=status.HTTP_200_OK)

    def format_annotations(self, annotations):
        """格式化注释数据"""
        formatted = []
        for ann in annotations:
            df = DateFormat(ann.updated_at)
            formatted_ann = {
                'id': ann.id,
                'content_tag': ann.content_tag,
                'quote': ann.quote,
                'content': ann.content,
                'user_display': ann.user.get_full_name() if ann.user else '未知用户',
                'updated_at': df.format('Y-m-d H:i:s'),  # 格式化为 "2025-05-28 21:57:04"
                'created_at': df.format('Y-m-d H:i:s')   # 添加创建时间
            }
            formatted.append(formatted_ann)
        return formatted

    def post(self, request, pk):
        """新增知识点下的注释"""
        knowledge_point = get_object_or_404(KnowledgePoint, pk=pk)
        
        # 自动计算content_tag - 获取当前知识点下最大的content_tag值并加1
        max_tag = KnowledgePointAnnotation.objects.filter(
            knowledge_point=knowledge_point
        ).aggregate(max_tag=Max('content_tag'))['max_tag'] or 0
        
        # 复制请求数据并添加自动计算的content_tag
        data = request.data.copy()
        data['content_tag'] = max_tag + 1
        data['user'] = request.user.id
        
        # 确保user_id包含在验证数据中
        data['user'] = request.user.id
        
        serializer = KnowledgePointAnnotationSerializer(
            data=data,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save(
                knowledge_point=knowledge_point,
                user=request.user
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class KnowledgePointAnnotationDetailAPI(APIView):
    """知识点注释详情API"""
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return KnowledgePointAnnotation.objects.get(pk=pk)
        except KnowledgePointAnnotation.DoesNotExist:
            from django.http import Http404
            raise Http404("KnowledgePointAnnotation not found")

    def get(self, request, pk):
        """获取单个注释详情"""
        annotation = self.get_object(pk)
        serializer = KnowledgePointAnnotationSerializer(annotation)
        return Response(serializer.data)

    def put(self, request, pk):
        """更新注释内容"""
        annotation = self.get_object(pk)
        if annotation.user != request.user:
            return Response({'error': '您没有权限修改此注释'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = KnowledgePointAnnotationSerializer(annotation, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """删除注释"""
        annotation = self.get_object(pk)
        if annotation.user != request.user:
            return Response({'error': '您没有权限删除此注释'}, status=status.HTTP_403_FORBIDDEN)
        
        annotation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
def knowledge_points_list(request):
    chapter_id = request.GET.get('chapter')
    exclude_id = request.GET.get('exclude')
    
    if not chapter_id:
        return Response({'error': 'chapter参数必填'}, status=400)
    
    queryset = KnowledgePoint.objects.filter(chapter_id=chapter_id)
    
    if exclude_id:
        queryset = queryset.exclude(id=exclude_id)
    
    data = [{
        'id': kp.id,
        'title': kp.title,
        'description': kp.description
    } for kp in queryset]
    
    return Response({'results': data})

@api_view(['GET'])
def knowledge_point_resources(request, pk):
    try:
        knowledge_point = KnowledgePoint.objects.get(pk=pk)
    except KnowledgePoint.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    videos = knowledge_point.videos.all().values('id', 'title', 'duration')
    documents = knowledge_point.documents.all().values('id', 'title', 'file')
    exercises = knowledge_point.exercises.all().values('id', 'question_type', 'content')
    
    return Response({
        'videos': list(videos),
        'documents': list(documents),
        'exercises': list(exercises)
    }, status=status.HTTP_200_OK)


@api_view(['PUT'])
def update_knowledge_point_content(request, pk):
    try:
        knowledge_point = KnowledgePoint.objects.get(pk=pk)
    except KnowledgePoint.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    if 'content' not in request.data:
        return Response({'error': 'Content is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    knowledge_point.content = request.data['content']
    knowledge_point.save()
    return Response({'status': 'content updated'})

def search_knowledge_points(request, chapter_id):
    """
    知识点模糊查询API
    支持根据章节ID和关键词进行模糊查询
    """
    query = request.GET.get('query', '').strip()
    if not query:
        return JsonResponse([])
    
    # 模糊匹配知识点标题
    points = KnowledgePoint.objects.filter(
        chapter_id=chapter_id,
        title__icontains=query
    ).values('id', 'title')[:12]  # 限制最多返回12个结果
    
    return JsonResponse(list(points), safe=False)

class KnowledgePointDetailAPI(APIView):
    """知识点详情API"""
    def get(self, request, pk):
        knowledge_point = get_object_or_404(KnowledgePoint, pk=pk)
        serializer = KnowledgePointSerializer(knowledge_point)
        return Response(serializer.data)

class KnowledgePointResourcesAPI(APIView):
    """知识点关联资源API"""
    def get(self, request, pk):
        knowledge_point = get_object_or_404(KnowledgePoint, pk=pk)
        
        videos = knowledge_point.videos.all()
        documents = knowledge_point.documents.all()
        exercises = knowledge_point.exercises.all()
        
        data = {
            'videos': VideoSerializer(videos, many=True).data,
            'documents': DocumentSerializer_get(documents, many=True).data,
            'exercises': ExerciseSerializer(exercises, many=True).data
        }
        
        return Response(data)

class KnowledgePointUpdateAPI(APIView):
    """知识点更新API"""
    def put(self, request, pk):
        knowledge_point = get_object_or_404(KnowledgePoint, pk=pk)
        serializer = KnowledgePointSerializer(knowledge_point, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class KnowledgePointDeleteAPI(APIView):
    """知识点删除API"""
    def delete(self, request, pk):
        from django.db import transaction
        
        with transaction.atomic():
            # 递归删除知识点及其所有子知识点
            def delete_knowledge_point_and_children(kp):
                # 先删除所有子知识点
                children = KnowledgePoint.objects.filter(parent=kp)
                for child in children:
                    delete_knowledge_point_and_children(child)
                # 然后删除当前知识点
                kp.delete()
            
            knowledge_point = get_object_or_404(KnowledgePoint, pk=pk)
            delete_knowledge_point_and_children(knowledge_point)
            
        return Response(status=status.HTTP_204_NO_CONTENT)

class KnowledgePointCreateAPI(APIView):
    """知识点创建API"""
    def post(self, request):
        serializer = KnowledgePointSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class KnowledgePointAPI(APIView):
    @csrf_exempt
    def post(self, request):
        serializer = KnowledgePointSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class KnowledgeTreeAPI(APIView):
    def get(self, request, chapter_id):
        chapter = get_object_or_404(Chapter, pk=chapter_id)
        
        # 获取知识点并预取关联数据提高性能
        knowledge_points = KnowledgePoint.objects.filter(
            chapter=chapter
        ).select_related('chapter').prefetch_related('children').order_by('brother_id')

        
        # 转换为树形结构
        tree_data = get_tree_data(knowledge_points) if knowledge_points.exists() else []
        
        return Response({
            'chapter_id': chapter.id,
            'chapter_title': chapter.title,
            'tree_data': tree_data
        }, status=status.HTTP_200_OK)
    


class KnowledgePointDetailAPI(APIView):
    """
    知识点详情API
    支持GET(获取详情), PUT/PATCH(更新), DELETE(删除)
    """
    def get(self, request, pk):
        try:
            kp = KnowledgePoint.objects.get(pk=pk)
            serializer = KnowledgePointSerializer(kp)
            return Response(serializer.data)
        except KnowledgePoint.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        kp = KnowledgePoint.objects.get(pk=pk)
        serializer = KnowledgePointSerializer_PUT(kp, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        from django.db import transaction
        
        with transaction.atomic():
            # 递归删除知识点及其所有子知识点
            def delete_knowledge_point_and_children(kp):
                # 先删除所有子知识点
                children = KnowledgePoint.objects.filter(parent=kp)
                for child in children:
                    delete_knowledge_point_and_children(child)
                # 然后删除当前知识点
                kp.delete()
            
            knowledge_point = get_object_or_404(KnowledgePoint, pk=pk)
            delete_knowledge_point_and_children(knowledge_point)
            
        return Response(status=status.HTTP_204_NO_CONTENT)

class KnowledgePointListAPI(APIView):
    """
    知识点列表API
    支持GET(列表), POST(创建)
    """
    def get(self, request):
        kps = KnowledgePoint.objects.all()
        serializer = KnowledgePointSerializer(kps, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = KnowledgePointSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

