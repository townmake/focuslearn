"""用户重要日期：序列化与 JSON API（首页提醒 CRUD）。"""
import json
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .models import UserImportantDate


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

    return {
        "id": obj.id,
        "name": name,
        "description": desc,
        "due_at": due_local,
        "due_at_display": due_at_display,
        "days_display": days_display,
        "is_expired": is_expired,
        "stripe_even": index % 2 == 0,
    }


def _ordered_qs(user):
    return UserImportantDate.objects.filter(user=user).order_by(
        F("due_at").asc(nulls_last=True), "id"
    )


@login_required
@require_http_methods(["GET", "POST"])
def important_dates_api(request):
    now = timezone.now()
    if request.method == "GET":
        qs = _ordered_qs(request.user)
        items = [serialize_important_date(o, now, i) for i, o in enumerate(qs)]
        return JsonResponse({"items": items})

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

    UserImportantDate.objects.create(
        user=request.user,
        name=name,
        description=description,
        due_at=due_at,
    )
    qs = _ordered_qs(request.user)
    items = [serialize_important_date(o, now, i) for i, o in enumerate(qs)]
    return JsonResponse({"items": items}, status=201)


@login_required
@require_http_methods(["PUT", "PATCH", "DELETE"])
def important_date_detail_api(request, pk):
    now = timezone.now()
    obj = get_object_or_404(UserImportantDate, pk=pk, user=request.user)

    if request.method == "DELETE":
        obj.delete()
        qs = _ordered_qs(request.user)
        items = [serialize_important_date(o, now, i) for i, o in enumerate(qs)]
        return JsonResponse({"items": items})

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

    qs = _ordered_qs(request.user)
    items = [serialize_important_date(o, now, i) for i, o in enumerate(qs)]
    return JsonResponse({"items": items})
