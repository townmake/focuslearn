from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST

from courses.models import Subject


@login_required(login_url='login')
def home(request):
    from weekly_planner.models import Task, UserImportantDate
    from courses.subject_weekly_stats import build_home_weekly_rows

    today = timezone.now().date()
    tasks = Task.objects.filter(
        user=request.user,
        start_date=today
    ).order_by('start_time')

    completed_tasks = tasks.filter(is_completed=True)
    uncompleted_tasks = tasks.filter(is_completed=False)

    # 查询 UserImportantDate（与 weekly_planner.important_date_api 序列化一致）
    from django.db.models import F
    from weekly_planner.important_date_api import serialize_important_date

    now = timezone.now()
    important_dates = UserImportantDate.objects.filter(user=request.user).order_by(
        F("due_at").asc(nulls_last=True), "id"
    )
    important_dates_with_countdown = [
        serialize_important_date(d, now, i) for i, d in enumerate(important_dates)
    ]

    from weekly_planner.quotable_service import (
        ensure_today_quotable_quotes,
        pick_random_welcome_quote,
    )

    ensure_today_quotable_quotes()
    welcome_quote = pick_random_welcome_quote()

    context = {
        "completed_tasks": completed_tasks,
        "uncompleted_tasks": uncompleted_tasks,
        "subjects": Subject.objects.all(),
        "today": today,
        "important_dates_with_countdown": important_dates_with_countdown,
        "weekly_dashboard_rows": build_home_weekly_rows(request.user),
        "welcome_quote": welcome_quote,
    }

    return render(request, "home.html", context)


@login_required(login_url="login")
@require_POST
def refresh_weekly_dashboard(request):
    """批量按本周计划+记录刷新所有项目与子任务统计（不写 already_hours）。"""
    from courses.subject_weekly_stats import persist_subject_weekly_stats

    for subject in Subject.objects.all().order_by("id"):
        persist_subject_weekly_stats(request.user, subject)
    get_user_model().objects.filter(pk=request.user.pk).update(
        weekly_dashboard_refreshed_at=timezone.now()
    )
    return JsonResponse({"status": "success"})

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