from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import Task
from courses.models import ReviewSet
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from .models import QuickAccess
from .forms import QuickAccessForm

@login_required
def planner_view(request):
    """
    任务规划器视图
    """
    context = {
        'title': '任务规划器',
        'current_date': timezone.now().strftime('%Y-%m-%d'),
    }
    return render(request, 'weekly_planner/planner.html', context)

@login_required
def calendar_view(request):
    """
    日历视图
    """
    context = {
        'title': '日历视图',
    }
    return render(request, 'weekly_planner/calendar.html', context)

@login_required
def fast_record(request):
    """
    笔记视图
    """
    context = {
        'title': '笔记视图',
    }
    return render(request, 'weekly_planner/fast_record.html', context)

def word_view(request):
    """
    单词管理视图
    """
    return render(request, 'weekly_planner/word_view.html')

@login_required
def home_tasks_view(request):
    """
    首页今日任务视图
    """
    today = timezone.now().date()
    tasks = Task.objects.filter(
        user=request.user,
        start_date=today
    ).order_by('start_time')
    
    # 分离已完成和未完成的任务
    completed_tasks = tasks.filter(is_completed=True)
    uncompleted_tasks = tasks.filter(is_completed=False)
    
    # 获取今日复习任务
    review_sets = ReviewSet.objects.filter(
        created_at__date=today
    ).select_related('chapter__subject')
    
    # 按科目分组
    subjects_reviews = {}
    for review in review_sets:
        subject = review.chapter.subject if review.chapter else None
        if subject not in subjects_reviews:
            subjects_reviews[subject] = []
        subjects_reviews[subject].append(review)
    
    context = {
        'completed_tasks': completed_tasks,
        'uncompleted_tasks': uncompleted_tasks,
        'subjects_reviews': subjects_reviews,
        'daily_review_sets': subjects_reviews  # 保持兼容
    }
    return render(request, 'home.html', context)

@login_required
@require_http_methods(["POST"])
def update_task_status(request):
    """
    更新任务状态视图
    """
    try:
        # 获取用户所有今日任务
        today = timezone.now().date()
        user_tasks = Task.objects.filter(
            user=request.user,
            start_date=today
        )
        
        # 获取所有被选中的任务ID
        checked_ids = {
            int(key.split('_')[1]) 
            for key in request.POST 
            if key.startswith('task_')
        }
        
        # 批量更新所有任务状态
        for task in user_tasks:
            new_status = task.id in checked_ids
            if task.is_completed != new_status:
                task.is_completed = new_status
                task.completed_at = timezone.now() if new_status else None
                task.save()
        
        return redirect('home')
    except Exception as e:
        return HttpResponseBadRequest(f"更新任务状态失败: {str(e)}")
    
class QuickAccessListView(ListView):
    model = QuickAccess
    template_name = 'weekly_planner/quick_access_list.html'
    context_object_name = 'quick_access_items'
    paginate_by = 36  # 6行×6列=36项每页

    def get_queryset(self):
        return super().get_queryset().order_by('position')

class QuickAccessDetailView(DetailView):
    model = QuickAccess
    template_name = 'weekly_planner/quick_access_detail.html'
    context_object_name = 'object'

class QuickAccessCreateView(SuccessMessageMixin, CreateView):
    model = QuickAccess
    form_class = QuickAccessForm
    template_name = 'weekly_planner/quick_access_create.html'
    success_url = reverse_lazy('weekly_planner:quick_access_list')
    success_message = "便捷记录已成功创建!"

    def form_valid(self, form):
        if not form.cleaned_data.get('icon') and self.request.POST.get('use_default_icon'):
            form.instance.icon = 'images/create_default.png'
        return super().form_valid(form)

class QuickAccessUpdateView(SuccessMessageMixin, UpdateView):
    model = QuickAccess
    form_class = QuickAccessForm
    template_name = 'weekly_planner/quick_access_edit.html'
    success_url = reverse_lazy('weekly_planner:quick_access_list')
    success_message = "便捷记录已成功更新!"

class QuickAccessDeleteView(DeleteView):
    model = QuickAccess
    success_url = reverse_lazy('weekly_planner:quick_access_list')

    def delete(self, request, *args, **kwargs):
        # 获取要删除的对象
        self.object = self.get_object()
        # 删除关联的图片文件
        if self.object.icon:
            self.object.icon.delete(save=False)
        # 删除数据库记录
        response = super().delete(request, *args, **kwargs)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': '便捷记录已删除!'})
        messages.success(request, "便捷记录已删除!")
        return response
