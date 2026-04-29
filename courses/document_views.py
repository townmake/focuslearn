from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Document, Comment
from .serializers import DocumentSerializer_post,DocumentSerializer_get

@login_required
def document_detail(request, pk):
    """文档详情页视图"""
    document = get_object_or_404(Document, pk=pk)
    comments = Comment.objects.filter(type='documents', type_id=pk).order_by('-created_at')
    return render(request, 'courses/document_detail.html', {
        'document': document,
        'comments': comments,
        'comment_type': 'documents',
        'type_id': pk
    })

@login_required
def document_file_view(request, chapter_id, filename):
    """
    处理文档文件访问的视图
    示例URL: /courses/chapter/52/detail/虚拟存储答案部分-章节3-内存管理.pdf
    """
    try:
        # 查找匹配的文档记录
        document = Document.objects.get(
            chapter_id=chapter_id,
            file__icontains=filename
        )
        
        # 构建正确的文件URL
        file_url = document.file.url
        
        # 重定向到实际的媒体文件
        from django.shortcuts import redirect
        return redirect(file_url)
        
    except Document.DoesNotExist:
        # 如果没有找到对应的文档记录，返回404
        from django.http import Http404
        raise Http404("文档不存在")
        
    except Document.MultipleObjectsReturned:
        # 如果找到多个匹配的文档，返回第一个
        document = Document.objects.filter(
            chapter_id=chapter_id,
            file__icontains=filename
        ).first()
        return redirect(document.file.url)

class DocumentCreateAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DocumentSerializer_post(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DocumentUpdateAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        document = get_object_or_404(Document, pk=pk)
        serializer = DocumentSerializer_post(document, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DocumentDeleteAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        document = get_object_or_404(Document, pk=pk)
        document.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class DocumentListAPI(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DocumentSerializer_get
    pagination_class = StandardResultsSetPagination
    queryset = Document.objects.all().order_by('-created_at')

    def get_queryset(self):
        queryset = super().get_queryset()
        title = self.request.query_params.get('title', '')
        created_date_start = self.request.query_params.get('created_date_start', '')
        created_date_end = self.request.query_params.get('created_date_end', '')
        chapter_id = self.request.query_params.get('chapter_id', '')
        
        if title:
            queryset = queryset.filter(title__icontains=title)
        if created_date_start and created_date_end:
            queryset = queryset.filter(created_at__range=[created_date_start, created_date_end])
        if chapter_id:
            queryset = queryset.filter(chapter__id=chapter_id)
            
        return queryset

    def get_paginated_response(self, data):
        response = super().get_paginated_response(data)
        if not data:
            response.data['results'] = []
            response.data['empty_message'] = '暂无数据'
            response.data['can_create'] = True
        # 添加前端需要的分页字段
        response.data['current_page'] = self.paginator.page.number
        response.data['count'] = self.paginator.page.paginator.count
        return response
