"""
周智能总结：汇总周历任务与学习记录 → DeepSeek → 写入 WeeklyAiSummary。
后台线程中执行，避免阻塞 HTTP。
"""
from __future__ import annotations

import json
import logging
import re
import threading
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.db import close_old_connections, transaction
from django.db.models import Q
from django.utils import timezone

from courses.models import StudyRecord, Subject
from courses.subject_weekly_stats import overlap_seconds, _task_aware_interval

logger = logging.getLogger(__name__)


def _date_cn(d: date) -> str:
    return f"{d.year}年{d.month}月{d.day}日"


def _format_dt(dt) -> str:
    if not dt:
        return ""
    return timezone.localtime(dt).strftime("%Y-%m-%d %H:%M")


def collect_week_tasks_for_user(
    user,
    week_start,
    week_end,
    *,
    subject_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    from weekly_planner.models import Task

    tz = timezone.get_current_timezone()
    ws_d, we_d = week_start.date(), week_end.date()
    qs = Task.objects.filter(user=user).filter(
        start_date__lte=we_d, end_date__gte=ws_d
    ).select_related("subject", "chapter", "chapter__subject")
    if subject_id is not None:
        qs = qs.filter(
            Q(subject_id=subject_id) | Q(chapter__subject_id=subject_id)
        )

    out = []
    for t in qs:
        t0, t1 = _task_aware_interval(t, tz)
        secs = overlap_seconds(t0, t1, week_start, week_end)
        if secs <= 0:
            continue
        hours = float(Decimal(secs) / Decimal(3600))
        subj_name = ""
        if t.subject_id:
            subj_name = t.subject.name if t.subject else ""
        elif t.chapter and t.chapter.subject:
            subj_name = t.chapter.subject.name
        chap_title = t.chapter.title if t.chapter_id else ""
        out.append(
            {
                "task_id": t.id,
                "title": t.title,
                "description": (t.description or "")[:2000],
                "is_completed": t.is_completed,
                "is_unscheduled": t.is_unscheduled,
                "start_date": str(t.start_date),
                "end_date": str(t.end_date),
                "start_time": str(t.start_time)[:8],
                "end_time": str(t.end_time)[:8],
                "overlap_hours_in_week": round(hours, 3),
                "repeat_type": t.repeat_type,
                "subject_id": t.subject_id,
                "subject_name": subj_name,
                "chapter_id": t.chapter_id,
                "chapter_title": chap_title,
            }
        )
    return out


def collect_week_records_for_user(
    user,
    week_start,
    week_end,
    *,
    subject_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    qs = StudyRecord.objects.filter(user=user).filter(
        end_time__gte=week_start, start_time__lte=week_end
    )
    if subject_id is not None:
        subj = Subject.objects.filter(pk=subject_id).first()
        name_match = subj.name.strip() if subj else ""
        qs = qs.filter(
            Q(chapter__subject_id=subject_id)
            | Q(subject_name__iexact=name_match)
        )

    out = []
    for r in qs.select_related("chapter", "chapter__subject"):
        secs = overlap_seconds(r.start_time, r.end_time, week_start, week_end)
        if secs <= 0:
            continue
        hours = round(float(Decimal(secs) / Decimal(3600)), 3)
        out.append(
            {
                "record_id": r.id,
                "start_time": _format_dt(r.start_time),
                "end_time": _format_dt(r.end_time),
                "duration_hours": hours,
                "page_type": r.page_type,
                "subject_name": r.subject_name,
                "chapter_name": r.chapter_name,
                "chapter_id": r.chapter_id,
                "learning_content": (r.learning_content or "")[:3000],
                "description": (r.description or "")[:1000],
            }
        )
    return out


def build_weekly_context_payload(
    user,
    week_start,
    week_end,
    *,
    subject_id: Optional[int] = None,
) -> Dict[str, Any]:
    ws_d, we_d = week_start.date(), week_end.date()
    tasks = collect_week_tasks_for_user(user, week_start, week_end, subject_id=subject_id)
    records = collect_week_records_for_user(user, week_start, week_end, subject_id=subject_id)
    subjects_meta = []
    if subject_id is not None:
        s = Subject.objects.filter(pk=subject_id).first()
        if s:
            subjects_meta.append({"id": s.id, "name": s.name, "color": s.color or ""})
    else:
        for s in Subject.objects.all().order_by("id"):
            subjects_meta.append({"id": s.id, "name": s.name, "color": s.color or ""})
    return {
        "week_range": {
            "monday": str(ws_d),
            "sunday": str(we_d),
            "timezone": str(timezone.get_current_timezone()),
        },
        "subjects_catalog": subjects_meta,
        "planner_tasks_overlapping_week": tasks,
        "study_records_overlapping_week": records,
    }


def build_title_for_week(
    subject: Optional[Subject],
    week_start_d: date,
    week_end_d: date,
) -> str:
    left = _date_cn(week_start_d)
    right = _date_cn(week_end_d)
    if subject:
        name = (subject.name or "项目").strip() or "项目"
        return f"{name} {left}-{right}周总结"
    return f"各项目 {left}-{right}周总结"


def _run_summary_job(summary_id: int) -> None:
    close_old_connections()
    from integrations.deepseek import DeepSeekClient, DeepSeekError
    from integrations.deepseek.client import parse_json_from_model_text

    from weekly_planner.models import DeepSeekProviderSettings, WeeklyAiSummary

    try:
        summary = WeeklyAiSummary.objects.get(pk=summary_id)
    except WeeklyAiSummary.DoesNotExist:
        return

    settings_row = DeepSeekProviderSettings.load()
    if not settings_row.is_enabled or not (settings_row.api_key or "").strip():
        summary.status = WeeklyAiSummary.STATUS_FAILED
        summary.error_message = "DeepSeek 未启用或未配置 API Key。"
        summary.save(update_fields=["status", "error_message", "updated_at"])
        return

    subject_id = None
    subject_obj = None
    if summary.scope_key.startswith(WeeklyAiSummary.SCOPE_SUBJECT_PREFIX):
        m = re.match(r"^subject:(\d+)$", summary.scope_key)
        if m:
            subject_id = int(m.group(1))
            subject_obj = Subject.objects.filter(pk=subject_id).first()

    tz = timezone.get_current_timezone()
    monday = summary.week_start_date
    sunday = summary.week_end_date
    week_start = timezone.make_aware(datetime.combine(monday, time.min), tz)
    week_end = timezone.make_aware(
        datetime.combine(sunday, time(23, 59, 59, 999999)), tz
    )

    payload = build_weekly_context_payload(
        summary.user, week_start, week_end, subject_id=subject_id
    )
    payload_json = json.dumps(payload, ensure_ascii=False, indent=2)
    if len(payload_json) > 120000:
        payload_json = payload_json[:120000] + "\n…(内容过长已截断)"

    system_prompt = (
        "你是学习规划助手。用户将提供 JSON：本周周历计划任务与学习记录（含项目/子任务、完成状态、时长、描述等）。\n"
        "你必须只输出一个 JSON 对象（除 JSON 外不要输出任何前缀/后缀说明文字），包含两个键：\n"
        '1) "detail"：字符串，**正文整体为 Markdown**。要求简洁，避免长篇摘抄原始 JSON：\n'
        "   - 开头用 **GitHub 风格管道表格** 对比各「项目」本周**计划投入**与**学习记录投入**（小时数可按 JSON 中 "
        "subject_name 与任务/记录的 overlap_hours、duration_hours 等汇总；列建议："
        "项目 | 计划(小时) | 记录(小时) | 简评）。仅一个项目时表格仍写一行。\n"
        "   - 表格必须有表头行与分隔行（例如 `| --- | --- | --- | --- |`），以便正确渲染。\n"
        "   - 表格之后，对每个项目用 `### 项目名` 标题，下接 **1～3 句** 极简小结。\n"
        "   - 最后用 `### 总览` 标题，下接 **2～4 句** 总体总结。\n"
        '2) "overview"：从全文提炼的一句话极简概括，**严格不超过 50 个汉字**（标点尽量少）。\n'
    )
    user_prompt = (
        "以下为本周数据（JSON）。请生成周总结：\n\n" + payload_json
    )

    client = DeepSeekClient(
        api_key=settings_row.api_key,
        base_url=settings_row.api_base or "https://api.deepseek.com",
        model=(settings_row.default_model or "deepseek-chat").strip(),
        timeout=int(settings_row.request_timeout or 120),
    )

    raw = None
    try:
        raw = client.chat_completion(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format_json=True,
        )
    except DeepSeekError as e:
        logger.warning("DeepSeek JSON 模式失败 summary=%s: %s，尝试普通模式", summary_id, e)
        try:
            raw = client.chat_completion(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format_json=False,
            )
        except DeepSeekError as e2:
            summary.status = WeeklyAiSummary.STATUS_FAILED
            summary.error_message = str(e2)[:2000]
            summary.save(update_fields=["status", "error_message", "updated_at"])
            return

    if not (raw or "").strip():
        summary.status = WeeklyAiSummary.STATUS_FAILED
        summary.error_message = "DeepSeek 返回为空。"
        summary.save(update_fields=["status", "error_message", "updated_at"])
        return

    try:
        data = parse_json_from_model_text(raw)
    except (json.JSONDecodeError, ValueError) as e:
        summary.status = WeeklyAiSummary.STATUS_FAILED
        summary.error_message = f"解析 AI 返回 JSON 失败: {e}"
        summary.save(update_fields=["status", "error_message", "updated_at"])
        return

    detail = (data.get("detail") or data.get("正文") or "").strip()
    overview = (data.get("overview") or data.get("概述") or "").strip()
    # 按字数（中文）截断概述：最多 50 字
    if len(overview) > 50:
        overview = overview[:50]

    title = build_title_for_week(subject_obj, summary.week_start_date, summary.week_end_date)

    summary.title = title[:300]
    summary.overview = overview[:200]
    summary.body = detail
    summary.status = WeeklyAiSummary.STATUS_COMPLETED
    summary.error_message = ""
    summary.save(
        update_fields=[
            "title",
            "overview",
            "body",
            "status",
            "error_message",
            "updated_at",
        ]
    )


def start_weekly_ai_summary_thread(summary_id: int) -> None:
    t = threading.Thread(target=_job_wrapper, args=(summary_id,), daemon=True)
    t.start()


def _job_wrapper(summary_id: int) -> None:
    try:
        _run_summary_job(summary_id)
    except Exception:
        logger.exception("周总结任务异常 summary_id=%s", summary_id)
        close_old_connections()
        from weekly_planner.models import WeeklyAiSummary

        try:
            with transaction.atomic():
                s = WeeklyAiSummary.objects.select_for_update().get(pk=summary_id)
                s.status = WeeklyAiSummary.STATUS_FAILED
                s.error_message = "服务器内部错误，请稍后重试。"
                s.save(update_fields=["status", "error_message", "updated_at"])
        except Exception:
            pass
    finally:
        close_old_connections()
