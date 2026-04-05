from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST

from courses.models import Subject
from courses.subject_weekly_stats import get_local_week_range
from weekly_planner.models import WeeklyAiSummary


def _home_weekly_ai_context(request):
    completed = list(
        WeeklyAiSummary.objects.filter(
            user=request.user,
            scope_key=WeeklyAiSummary.SCOPE_HOME,
            status=WeeklyAiSummary.STATUS_COMPLETED,
        ).order_by("week_start_date")
    )
    ws_aware, _we = get_local_week_range()
    ws_d = ws_aware.date()
    week_job = (
        WeeklyAiSummary.objects.filter(
            user=request.user,
            scope_key=WeeklyAiSummary.SCOPE_HOME,
            week_start_date=ws_d,
        )
        .first()
    )
    ctx = {
        "weekly_ai_display": None,
        "weekly_ai_prev_id": None,
        "weekly_ai_next_id": None,
        "weekly_ai_week_job": week_job,
    }
    if not completed:
        return ctx
    sel = request.GET.get("weekly_summary")
    current = None
    if sel:
        try:
            current = next(x for x in completed if str(x.pk) == str(sel))
        except StopIteration:
            current = None
    if current is None:
        current = completed[-1]
    idx = completed.index(current)
    prev_s = completed[idx - 1] if idx > 0 else None
    next_s = completed[idx + 1] if idx < len(completed) - 1 else None
    ctx["weekly_ai_display"] = current
    ctx["weekly_ai_prev_id"] = prev_s.pk if prev_s else None
    ctx["weekly_ai_next_id"] = next_s.pk if next_s else None
    return ctx


@login_required(login_url='login')
def home(request):
    from weekly_planner.important_date_snapshot import get_home_important_dates_items
    from weekly_planner.models import Task

    today = timezone.now().date()
    tasks = Task.objects.filter(
        user=request.user,
        start_date=today
    ).order_by('start_time')

    completed_tasks = tasks.filter(is_completed=True)
    uncompleted_tasks = tasks.filter(is_completed=False)

    important_dates_with_countdown = get_home_important_dates_items(request.user)

    from weekly_planner.quotable_service import pick_random_welcome_quote
    from courses.subject_weekly_stats import restore_home_weekly_rows_from_snapshot

    welcome_quote = pick_random_welcome_quote()

    weekly_dashboard_rows = restore_home_weekly_rows_from_snapshot(
        request.user.weekly_dashboard_snapshot
    )
    weekly_dashboard_plan_total = sum(
        r["planned_hours"] for r in weekly_dashboard_rows
    )
    weekly_dashboard_actual_total = sum(
        r["actual_hours"] for r in weekly_dashboard_rows
    )

    context = {
        "completed_tasks": completed_tasks,
        "uncompleted_tasks": uncompleted_tasks,
        "subjects": Subject.objects.all(),
        "today": today,
        "important_dates_with_countdown": important_dates_with_countdown,
        "weekly_dashboard_rows": weekly_dashboard_rows,
        "weekly_dashboard_plan_total": weekly_dashboard_plan_total,
        "weekly_dashboard_actual_total": weekly_dashboard_actual_total,
        "welcome_quote": welcome_quote,
    }
    context.update(_home_weekly_ai_context(request))

    return render(request, "home.html", context)


@login_required(login_url="login")
def random_welcome_quote(request):
    """首页「今日一句」换一句：从本地名人名言库随机取一条（JSON）。"""
    from weekly_planner.quotable_service import pick_random_welcome_quote

    q = pick_random_welcome_quote()
    if not q:
        return JsonResponse(
            {
                "content": None,
                "author": None,
                "message": "暂无可展示的名言，请在后台「本地名人名言」中添加。",
            }
        )
    return JsonResponse({"content": q["content"], "author": q["author"]})


@login_required(login_url="login")
@require_POST
def refresh_weekly_dashboard(request):
    """批量按本周计划+记录刷新所有项目与子任务统计（不写 already_hours）。"""
    from courses.subject_weekly_stats import (
        build_home_weekly_rows,
        persist_subject_weekly_stats,
        snapshot_home_weekly_rows,
    )

    for subject in Subject.objects.all().order_by("id"):
        persist_subject_weekly_stats(request.user, subject)
    rows = build_home_weekly_rows(request.user)
    snapshot = snapshot_home_weekly_rows(rows)
    get_user_model().objects.filter(pk=request.user.pk).update(
        weekly_dashboard_refreshed_at=timezone.now(),
        weekly_dashboard_snapshot=snapshot,
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