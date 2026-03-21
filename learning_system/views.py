from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from courses.models import Subject

@login_required(login_url='login')
def home(request):
    from weekly_planner.models import Task, UserImportantDate
    from courses.models import Subject, ReviewSet
    from django.utils import timezone
    
    today = timezone.now().date()
    tasks = Task.objects.filter(
        user=request.user,
        start_date=today
    ).order_by('start_time')
    
    # 分离已完成和未完成的任务
    completed_tasks = tasks.filter(is_completed=True)
    uncompleted_tasks = tasks.filter(is_completed=False)
    
    # 获取当天需要复习的科目习题集（subject_id不为空）
    start_date = timezone.datetime.combine(today, timezone.datetime.min.time())
    end_date = timezone.datetime.combine(today, timezone.datetime.max.time())
    review_sets = ReviewSet.objects.filter(
        created_at__range=(start_date, end_date),
        subject_id__isnull=False
    ).select_related('chapter__subject')  # 关联查询科目信息
    
    # 按科目分组，使用科目对象作为key
    subjects_reviews = {}
    for review in review_sets:
        if review.subject not in subjects_reviews:
            subjects_reviews[review.subject] = []
        subjects_reviews[review.subject].append(review)

    # 查询 UserImportantDate 并计算倒计时
    important_dates = UserImportantDate.objects.filter(user=request.user)
    important_dates_with_countdown = []
    for important_date in important_dates:
        if important_date.date:
            time_diff = (important_date.date - today).days
            if time_diff < 0:
                days_left = '日期已过'
            else:
                days_left = f' {time_diff} '
            important_dates_with_countdown.append({
                'id': important_date.id,
                'name': important_date.name,
                'date': important_date.date,
                'days_left': days_left
            })
    
    context = {
        'completed_tasks': completed_tasks,
        'uncompleted_tasks': uncompleted_tasks,
        'subjects': Subject.objects.all(),
        'reviews_sets':review_sets,
        'subjects_reviews': subjects_reviews,
        'daily_review_sets': subjects_reviews,  # 保持兼容
        'today': today,
        'important_dates_with_countdown': important_dates_with_countdown
    }
    
    return render(request, 'home.html', context)

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        # 检查用户是否存在
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user_exists = User.objects.filter(username=username).exists()
            if not user_exists:
                error_message = "该账号未在系统中配置，请联系管理员。"
                return render(request, 'login.html', {'error_message': error_message})
            
            # 如果用户存在，尝试认证
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                error_message = "密码不正确，请重试。"
                return render(request, 'login.html', {'error_message': error_message})
        except Exception as e:
            error_message = "登录过程中出现错误，请稍后重试。"
            return render(request, 'login.html', {'error_message': error_message})
    return render(request, 'login.html')

def register_view(request):
    if request.method == 'POST':
        # 这里添加注册逻辑
        pass
    return render(request, 'register.html')

def logout_view(request):
    logout(request)
    return redirect('home')

def generate_daily_review(request):
    from django.core.management import call_command
    from django.contrib import messages
    from django.core.cache import cache
    from django.utils import timezone
    
    # 获取当天日期字符串作为缓存key
    today_str = timezone.now().strftime('%Y-%m-%d')
    cache_key = f'daily_review_generated_{today_str}'
    
    # 检查是否已生成过
    if cache.get(cache_key):
        messages.warning(request, '今日复习任务已生成过，请勿重复操作')
        return redirect('home')
    
    try:
        call_command('generate_daily_review')
        # 设置24小时缓存
        cache.set(cache_key, True, 60*60*24)
        messages.success(request, '今日复习任务已成功生成')
    except Exception as e:
        messages.error(request, f'生成复习任务失败: {str(e)}')
    
    return redirect('home')