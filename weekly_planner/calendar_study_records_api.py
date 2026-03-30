"""
日历视图：返回当前用户在时间范围内与视图相交的 StudyRecord（学习/任务记录）。
"""
from datetime import datetime, time

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.utils import timezone

from courses.models import StudyRecord


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def calendar_study_records(request):
    start_date = request.query_params.get("start_date")
    end_date = request.query_params.get("end_date")
    if not start_date or not end_date:
        return Response(
            {"error": "需要参数 start_date 与 end_date（YYYY-MM-DD）"},
            status=400,
        )
    try:
        d0 = datetime.strptime(start_date, "%Y-%m-%d").date()
        d1 = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        return Response({"error": "日期格式无效"}, status=400)

    tz = timezone.get_current_timezone()
    range_start = timezone.make_aware(datetime.combine(d0, time.min), tz)
    range_end = timezone.make_aware(
        datetime.combine(d1, time(23, 59, 59, 999999)), tz
    )

    type_labels = dict(StudyRecord.PAGE_TYPE_CHOICES)

    qs = (
        StudyRecord.objects.filter(user=request.user)
        .filter(end_time__gte=range_start, start_time__lte=range_end)
        .order_by("start_time")
    )

    def _fc_iso(dt):
        """转为当前时区墙钟时间 ISO，去掉微秒，便于前端稳定解析。"""
        if dt is None:
            return None
        return timezone.localtime(dt).replace(microsecond=0).isoformat()

    out = []
    for r in qs:
        text = (r.learning_content or "").strip()
        title = (text[:42] + "…") if len(text) > 42 else (text or "（无内容）")

        out.append(
            {
                "id": r.id,
                "title": title,
                "start": _fc_iso(r.start_time),
                "end": _fc_iso(r.end_time),
                "learning_content": r.learning_content or "",
                "description": r.description or "",
                "page_type": r.page_type,
                "page_type_display": type_labels.get(r.page_type, r.page_type),
                "subject_name": r.subject_name or "",
                "chapter_name": r.chapter_name or "",
                "chapter_id": r.chapter_id,
                "duration_display": r.duration_display,
            }
        )

    return Response(out)
