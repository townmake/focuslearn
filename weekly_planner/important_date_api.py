"""用户重要日期：序列化与 JSON API（首页提醒 CRUD）。"""
import json
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from courses.models import Chapter, Subject

from .models import Task, UserImportantDate
from .task_reminder_service import apply_due_at_to_linked_planner_task, task_times_from_due_at


def _parse_client_datetime(s):
    """解析前端 datetime-local 字符串（视为当前时区本地时间）。"""
    if not s or not str(s).strip():
        return None
    s = str(s).strip()
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def serialize_important_date(obj, now, index=0):
    """与首页、API 共用的展示结构。"""
    name = (obj.name or "").strip() or "未命名"
    desc = (obj.description or "").strip()

    is_expired = False
    if not obj.due_at:
        days_display = "未设置时间"
    else:
        if obj.due_at < now:
            is_expired = True
            days_display = "已过期"
        else:
            local_now = timezone.localtime(now)
            local_due = timezone.localtime(obj.due_at)
            d0 = local_now.date()
            d1 = local_due.date()
            diff_days = (d1 - d0).days
            if diff_days < 0:
                is_expired = True
                days_display = "已过期"
            elif diff_days == 0:
                days_display = local_due.strftime("今日 %H:%M 前")
            else:
                days_display = f"还有 {diff_days} 天"

    due_local = None
    due_at_display = ""
    if obj.due_at:
        ld = timezone.localtime(obj.due_at)
        due_local = ld.strftime("%Y-%m-%dT%H:%M")
        due_at_display = ld.strftime("%Y-%m-%d %H:%M")

    planner_subject_id = None
    planner_chapter_id = None
    planner_category_id = None
    if obj.planner_task_id:
        t = obj.planner_task
        planner_subject_id = t.subject_id
        planner_chapter_id = t.chapter_id
        if t.subject_id:
            cat_id = getattr(t.subject, "category_id", None)
            planner_category_id = cat_id

    return {
        "id": obj.id,
        "name": name,
        "description": desc,
        "due_at": due_local,
        "due_at_display": due_at_display,
        "days_display": days_display,
        "is_expired": is_expired,
        "stripe_even": index % 2 == 0,
        "planner_subject_id": planner_subject_id,
        "planner_chapter_id": planner_chapter_id,
        "planner_category_id": planner_category_id,
    }


@login_required
@require_http_methods(["GET", "POST"])
def important_dates_api(request):
    from .important_date_snapshot import get_home_important_dates_items

    if request.method == "GET":
        return JsonResponse({"items": get_home_important_dates_items(request.user)})

    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "无效的 JSON"}, status=400)

    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip()
    due_at = _parse_client_datetime(data.get("due_at"))
    if not name:
        return JsonResponse({"error": "名称不能为空"}, status=400)
    if not due_at:
        return JsonResponse({"error": "请填写到期日期时间"}, status=400)

    subject_id = data.get("subject")
    chapter_id = data.get("chapter")
    if not subject_id or not chapter_id:
        return JsonResponse({"error": "请选择项目与子任务，以便同步到周计划"}, status=400)
    subject = get_object_or_404(Subject, pk=subject_id)
    chapter = get_object_or_404(Chapter, pk=chapter_id, subject=subject)

    sd, st, ed, et = task_times_from_due_at(due_at)
    task = Task.objects.create(
        user=request.user,
        subject=subject,
        chapter=chapter,
        title=name[:200],
        description=description or "",
        start_date=sd,
        start_time=st,
        end_date=ed,
        end_time=et,
        repeat_type="none",
    )
    UserImportantDate.objects.create(
        user=request.user,
        name=name,
        description=description,
        due_at=due_at,
        planner_task=task,
    )
    return JsonResponse(
        {"items": get_home_important_dates_items(request.user)}, status=201
    )


@login_required
@require_http_methods(["PUT", "PATCH", "DELETE"])
def important_date_detail_api(request, pk):
    from .important_date_snapshot import get_home_important_dates_items

    obj = get_object_or_404(
        UserImportantDate.objects.select_related("planner_task", "planner_task__subject"),
        pk=pk,
        user=request.user,
    )

    if request.method == "DELETE":
        if obj.planner_task_id:
            obj.planner_task.delete()
        else:
            obj.delete()
        return JsonResponse({"items": get_home_important_dates_items(request.user)})

    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "无效的 JSON"}, status=400)

    if "name" in data:
        name = (data.get("name") or "").strip()
        if not name:
            return JsonResponse({"error": "名称不能为空"}, status=400)
        obj.name = name
    if "description" in data:
        obj.description = (data.get("description") or "").strip()
    if "due_at" in data:
        due_at = _parse_client_datetime(data.get("due_at"))
        if not due_at:
            return JsonResponse({"error": "请填写到期日期时间"}, status=400)
        obj.due_at = due_at
    obj.save()

    if obj.planner_task_id:
        t = obj.planner_task
        t_fields = []
        if "name" in data:
            t.title = obj.name[:200]
            t_fields.append("title")
        if "description" in data:
            t.description = obj.description or ""
            t_fields.append("description")
        if t_fields:
            t.save(update_fields=t_fields)
        if "due_at" in data:
            apply_due_at_to_linked_planner_task(obj, obj.due_at)
        if "subject" in data or "chapter" in data:
            sid = data.get("subject", t.subject_id)
            cid = data.get("chapter", t.chapter_id)
            subject = get_object_or_404(Subject, pk=sid)
            chapter = get_object_or_404(Chapter, pk=cid, subject=subject)
            t.subject = subject
            t.chapter = chapter
            t.save(update_fields=["subject_id", "chapter_id"])
    elif data.get("subject") and data.get("chapter"):
        subject = get_object_or_404(Subject, pk=data["subject"])
        chapter = get_object_or_404(Chapter, pk=data["chapter"], subject=subject)
        sd, st, ed, et = task_times_from_due_at(obj.due_at)
        task = Task.objects.create(
            user=request.user,
            subject=subject,
            chapter=chapter,
            title=obj.name[:200],
            description=obj.description or "",
            start_date=sd,
            start_time=st,
            end_date=ed,
            end_time=et,
            repeat_type="none",
        )
        obj.planner_task = task
        obj.save(update_fields=["planner_task_id"])

    return JsonResponse({"items": get_home_important_dates_items(request.user)})


@login_required
@require_http_methods(["GET"])
def subject_category_options_api(request):
    """周历/首页：分类 → 项目 二级联动数据源。"""
    from courses.models import SubjectCategory

    categories = []
    for c in SubjectCategory.objects.filter(is_visible=True).order_by("-display_weight", "id"):
        subs = Subject.objects.filter(category=c).order_by("order", "name")
        categories.append(
            {
                "id": c.id,
                "name": c.name,
                "subjects": [{"id": s.id, "name": s.name} for s in subs],
            }
        )
    loose = Subject.objects.filter(category__isnull=True).order_by("order", "name")
    if loose.exists():
        categories.append(
            {
                "id": None,
                "name": "未分类",
                "subjects": [{"id": s.id, "name": s.name} for s in loose],
            }
        )
    return JsonResponse({"categories": categories})
