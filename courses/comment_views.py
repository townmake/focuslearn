
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .models import Comment, Video
from django.utils import timezone
import json

@login_required
@require_http_methods(["GET"])
def get_comments(request):
    """获取指定类型的评论列表(API接口)"""
    comment_type = request.GET.get('type', 'other')
    type_id = request.GET.get('type_id')
    page = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', 10)
    
    if not type_id:
        return JsonResponse({'error': 'type_id is required'}, status=400)
    
    queryset = Comment.objects.filter(
        type=comment_type,
        type_id=type_id
    ).order_by('-created_at')
    
    # 分页处理
    total_count = queryset.count()
    comments = queryset[(int(page)-1)*int(page_size):int(page)*int(page_size)]
    
    # 序列化评论数据
    comment_list = []
    for comment in comments:
        comment_list.append({
            'id': comment.id,
            'user': {
                'id': comment.user.id,
                'username': comment.user.username
            },
            'title': comment.title,
            'content': comment.content,
            'position': comment.position,
            'created_at': timezone.localtime(comment.created_at).strftime('%Y-%m-%d %H:%M'),
            'type': comment.type,
            'type_id': comment.type_id
        })
    
    return JsonResponse({
        'success': True,
        'data': {
            'comments': comment_list,
            'pagination': {
                'total': total_count,
                'page': int(page),
                'page_size': int(page_size),
                'page_count': (total_count + int(page_size) - 1) // int(page_size)
            }
        }
    })

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def submit_comment(request):
    """提交新评论"""
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
            comment_type = data.get('type', 'other')
            type_id = data.get('type_id')
            title = data.get('title', '')
            content = data.get('content', '')
            position = data.get('position', None)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    else:
        comment_type = request.POST.get('type', 'other')
        type_id = request.POST.get('type_id')
        title = request.POST.get('title', '')
        content = request.POST.get('content', '')
        position = request.POST.get('position', None)
    
    if not all([type_id, title, content]):
        return JsonResponse({'error': 'Missing required fields'}, status=400)
    
    # 创建评论
    comment = Comment.objects.create(
        user=request.user,
        type=comment_type,
        type_id=type_id,
        title=title,
        content=content,
        position=position,
        created_at=timezone.now()
    )
    
    return JsonResponse({
        'success': True,
        'comment_id': comment.id
    })
