"""
首页 / 项目页：周智能总结（DeepSeek 异步生成）。
"""
import json

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET, require_POST

from courses.models import Subject
from courses.subject_weekly_stats import get_local_week_range
from weekly_planner.models import WeeklyAiSummary
from weekly_planner.weekly_ai_summary_service import start_weekly_ai_summary_thread


def _week_bounds():
    ws, we = get_local_week_range()
    return ws.date(), we.date()


@login_required
@require_POST
def home_weekly_ai_summary_start(request):
    """启动「全项目」本周智能总结（后台线程）。"""
    regenerate = request.POST.get("regenerate") == "1"
    ws_d, we_d = _week_bounds()
    scope_key = WeeklyAiSummary.SCOPE_HOME

    with transaction.atomic():
        obj = (
            WeeklyAiSummary.objects.select_for_update()
            .filter(
                user=request.user,
                scope_key=scope_key,
                week_start_date=ws_d,
            )
            .first()
        )
        if obj is None:
            obj = WeeklyAiSummary(
                user=request.user,
                scope_key=scope_key,
                week_start_date=ws_d,
                week_end_date=we_d,
                status=WeeklyAiSummary.STATUS_PENDING,
            )
            obj.save()
        elif regenerate:
            obj.week_end_date = we_d
            obj.title = ""
            obj.overview = ""
            obj.body = ""
            obj.error_message = ""
            obj.status = WeeklyAiSummary.STATUS_PENDING
            obj.save(
                update_fields=[
                    "week_end_date",
                    "title",
                    "overview",
                    "body",
                    "error_message",
                    "status",
                    "updated_at",
                ]
            )

        if obj.status == WeeklyAiSummary.STATUS_PROCESSING:
            return JsonResponse(
                {
                    "ok": True,
                    "status": "processing",
                    "id": obj.id,
                    "message": "正在生成中，请稍候在下方查看或刷新页面。",
                }
            )

        if obj.status == WeeklyAiSummary.STATUS_COMPLETED and not regenerate:
            return JsonResponse(
                {
                    "ok": True,
                    "status": "completed",
                    "id": obj.id,
                    "message": "本周已有总结。若需重新生成，请勾选重新生成后再提交。",
                }
            )

        obj.status = WeeklyAiSummary.STATUS_PROCESSING
        obj.error_message = ""
        obj.save(update_fields=["status", "error_message", "updated_at"])

    start_weekly_ai_summary_thread(obj.id)
    return JsonResponse(
        {
            "ok": True,
            "status": "started",
            "id": obj.id,
            "message": "已提交生成，DeepSeek 处理可能需要数十秒，请稍后点击刷新或等待自动完成提示。",
        }
    )


@login_required
@require_GET
def weekly_ai_summary_status(request, pk: int):
    """查询单条总结状态（供轮询）。"""
    s = get_object_or_404(WeeklyAiSummary, pk=pk, user=request.user)
    return JsonResponse(
        {
            "id": s.id,
            "status": s.status,
            "title": s.title,
            "overview": s.overview,
            "body": s.body,
            "error_message": s.error_message,
            "week_start_date": str(s.week_start_date),
            "week_end_date": str(s.week_end_date),
        }
    )


@login_required
@require_POST
def weekly_ai_summary_update_body(request, pk: int):
    """
    周总结手动修订（Markdown 正文；可选标题/概述）。
    仅允许当前用户、且已完成的记录（首页或项目 scope 均可）。
    """
    s = get_object_or_404(WeeklyAiSummary, pk=pk, user=request.user)
    if s.status != WeeklyAiSummary.STATUS_COMPLETED:
        return JsonResponse(
            {"ok": False, "error": "仅已完成的总结可保存。"},
            status=400,
        )
    try:
        payload = json.loads(request.body.decode() or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "无效 JSON"}, status=400)

    update_fields = ["updated_at"]
    if "body" in payload:
        body = payload.get("body")
        if not isinstance(body, str):
            return JsonResponse({"ok": False, "error": "body 须为字符串"}, status=400)
        s.body = body
        update_fields.append("body")
    if "title" in payload:
        title = payload.get("title")
        if not isinstance(title, str):
            return JsonResponse({"ok": False, "error": "title 须为字符串"}, status=400)
        s.title = title.strip()[:300]
        update_fields.append("title")
    if "overview" in payload:
        overview = payload.get("overview")
        if not isinstance(overview, str):
            return JsonResponse({"ok": False, "error": "overview 须为字符串"}, status=400)
        s.overview = overview.strip()[:200]
        update_fields.append("overview")

    if len(update_fields) == 1:
        return JsonResponse(
            {"ok": False, "error": "请提供 body、title 或 overview"},
            status=400,
        )

    s.save(update_fields=update_fields)
    return JsonResponse(
        {
            "ok": True,
            "id": s.id,
            "title": s.title,
            "overview": s.overview,
            "body": s.body,
        }
    )


@login_required
@require_POST
def subject_weekly_ai_summary_start(request, subject_pk: int):
    """某项目本周智能总结（写入 WeeklyAiSummary，scope_key=subject:<id>）。"""
    subject = get_object_or_404(Subject, pk=subject_pk)
    regenerate = request.POST.get("regenerate") == "1"
    ws_d, we_d = _week_bounds()
    scope_key = WeeklyAiSummary.scope_key_for_subject(subject_pk)

    with transaction.atomic():
        obj = (
            WeeklyAiSummary.objects.select_for_update()
            .filter(
                user=request.user,
                scope_key=scope_key,
                week_start_date=ws_d,
            )
            .first()
        )
        if obj is None:
            obj = WeeklyAiSummary(
                user=request.user,
                scope_key=scope_key,
                week_start_date=ws_d,
                week_end_date=we_d,
                status=WeeklyAiSummary.STATUS_PENDING,
            )
            obj.save()
        elif regenerate:
            obj.week_end_date = we_d
            obj.title = ""
            obj.overview = ""
            obj.body = ""
            obj.error_message = ""
            obj.status = WeeklyAiSummary.STATUS_PENDING
            obj.save(
                update_fields=[
                    "week_end_date",
                    "title",
                    "overview",
                    "body",
                    "error_message",
                    "status",
                    "updated_at",
                ]
            )

        if obj.status == WeeklyAiSummary.STATUS_PROCESSING:
            return JsonResponse(
                {
                    "ok": True,
                    "status": "processing",
                    "id": obj.id,
                    "message": "正在生成中，请稍候刷新页面查看。",
                }
            )

        if obj.status == WeeklyAiSummary.STATUS_COMPLETED and not regenerate:
            return JsonResponse(
                {
                    "ok": True,
                    "status": "completed",
                    "id": obj.id,
                    "message": "本周该项目已有总结。需要重新生成请传 regenerate=1。",
                }
            )

        obj.status = WeeklyAiSummary.STATUS_PROCESSING
        obj.error_message = ""
        obj.save(update_fields=["status", "error_message", "updated_at"])

    start_weekly_ai_summary_thread(obj.id)
    return JsonResponse(
        {
            "ok": True,
            "status": "started",
            "id": obj.id,
            "message": "已提交生成，请稍后刷新本页查看总结。",
        }
    )
