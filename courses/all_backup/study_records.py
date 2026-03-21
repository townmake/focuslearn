
from django.core.paginator import Paginator
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import StudyRecord
from ..serializers import StudyRecordSerializer
from ..models import Subject, Chapter, StudyRecord

class StudyRecordListView(APIView):
    def get(self, request):
        # 获取查询参数
        created_date_start = request.GET.get('created_date_start')
        created_date_end = request.GET.get('created_date_end')
        page_type = request.GET.get('page_type')
        learning_content = request.GET.get('learning_content')
        chapter_id = request.GET.get('chapter')
        
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
            
        # 排序
        queryset = queryset.order_by('-created_date', '-start_time')
        
        
        # 分页
        paginator = Paginator(queryset, 10)  # 每页10条
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        # 获取相关数据用于筛选
        subjects = Subject.objects.all()
        chapters = Chapter.objects.all()
        page_types = StudyRecord.PAGE_TYPE_CHOICES
        
        context = {
            'records': page_obj,
            'subjects': subjects,
            'chapters': chapters,
            'page_types': page_types,
            'show_full_filters': True,
            'is_paginated': True,
            'page_obj': page_obj
        }
        
        print("上下文数据:", context)  # 调试信息
        print("分页对象记录数:", page_obj.object_list.count())  # 调试信息
        return render(request, 'courses/_study_records.html', context, 
                    content_type='text/html; fragment=true')

class BaseStudyRecordListView(StudyRecordListView):
    def get(self, request):
        # 获取查询参数
        created_date_start = request.GET.get('created_date_start')
        created_date_end = request.GET.get('created_date_end')
        page_type = request.GET.get('page_type')
        learning_content = request.GET.get('learning_content')
        chapter_id = request.GET.get('chapter')
        
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
            
        # 排序
        queryset = queryset.order_by('-created_date', '-start_time')
        
        # 分页
        paginator = Paginator(queryset, 10)  # 每页10条
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        # 获取相关数据用于筛选
        subjects = Subject.objects.all()
        chapters = Chapter.objects.all()
        page_types = StudyRecord.PAGE_TYPE_CHOICES
        
        context = {
            'records': page_obj,
            'subjects': subjects,
            'chapters': chapters,
            'page_types': page_types,
            'show_full_filters': True,
            'is_paginated': True,
            'page_obj': page_obj
        }
        
        print("上下文数据:", context)  # 调试信息
        print("分页对象记录数:", page_obj.object_list.count())  # 调试信息
        return render(request, 'courses/study_record_base.html', context)

