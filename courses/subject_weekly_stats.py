"""
项目（科目）周维度统计：周计划（周历 Task）与周学习记录（StudyRecord），按章节/任务名分组。
"""
import re
from collections import defaultdict
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.db.models import Q
from django.utils import timezone as dj_tz

from .models import Chapter, StudyRecord, Subject

_UNASSIGNED_KEY = "__未归属子任务__"


def _norm_title(s):
    """用于将周历任务名、记录里的任务名与子任务（Chapter）标题对齐。"""
    return (s or "").strip().casefold()


def get_local_week_range(reference=None):
    """
    自然周：周一至周日，起止均为当前时区。
    reference 为 aware datetime，默认当前时间。
    """
    tz = dj_tz.get_current_timezone()
    if reference is None:
        reference = dj_tz.now()
    local = dj_tz.localtime(reference)
    d = local.date()
    monday = d - timedelta(days=d.weekday())
    sunday = monday + timedelta(days=6)
    week_start = dj_tz.make_aware(datetime.combine(monday, time.min), tz)
    week_end = dj_tz.make_aware(datetime.combine(sunday, time(23, 59, 59, 999999)), tz)
    return week_start, week_end


def overlap_seconds(range_start, range_end, window_start, window_end):
    lo = max(range_start, window_start)
    hi = min(range_end, window_end)
    if hi <= lo:
        return 0
    return int((hi - lo).total_seconds())


def _task_aware_interval(task, tz):
    start_dt = dj_tz.make_aware(
        datetime.combine(task.start_date, task.start_time), tz
    )
    end_dt = dj_tz.make_aware(datetime.combine(task.end_date, task.end_time), tz)
    if end_dt < start_dt:
        end_dt = start_dt
    return start_dt, end_dt


def aggregate_subject_weekly_stats(user, subject):
    """
    统计当前登录用户、指定科目在「本周」（周一至周日，本地时区）内：

    - **周历 Task**：与本周时间窗求交集后的计划时长（小时）；
    - **StudyRecord**：与本周时间窗求交集后的实际投入（小时）。

    先归到各 **子任务（Chapter）**：优先用外键 `chapter_id`；若无关联，则用任务标题 / 记录里的任务名
    与子任务 **标题** 做规范化匹配（strip + casefold）。无法归类的计入「__未归属子任务__」。

    返回值中的合计 = 各子任务之和 + 未归属部分，用于写回 **Subject** 与 **Chapter**。
    """
    from weekly_planner.models import Task

    week_start, week_end = get_local_week_range()
    tz = dj_tz.get_current_timezone()
    ws_d, we_d = week_start.date(), week_end.date()

    chapters = list(Chapter.objects.filter(subject=subject))
    chapter_ids = {c.id for c in chapters}
    # 同标题多子任务时只命中第一条，避免重复键
    chapter_by_title_norm = {}
    for c in chapters:
        k = _norm_title(c.title)
        if k and k not in chapter_by_title_norm:
            chapter_by_title_norm[k] = c

    planned_by_id = defaultdict(lambda: Decimal("0"))
    actual_by_id = defaultdict(lambda: Decimal("0"))
    planned_unassigned = Decimal("0")
    actual_unassigned = Decimal("0")

    tasks = (
        Task.objects.filter(user=user)
        .filter(Q(subject_id=subject.id) | Q(chapter__subject_id=subject.id))
        .filter(start_date__lte=we_d, end_date__gte=ws_d)
        .select_related("chapter")
    )

    for task in tasks:
        t0, t1 = _task_aware_interval(task, tz)
        secs = overlap_seconds(t0, t1, week_start, week_end)
        if secs <= 0:
            continue
        hours = Decimal(secs) / Decimal(3600)
        if task.chapter_id and task.chapter_id in chapter_ids:
            planned_by_id[task.chapter_id] += hours
        elif task.subject_id == subject.id:
            c = chapter_by_title_norm.get(_norm_title(task.title))
            if c:
                planned_by_id[c.id] += hours
            else:
                planned_unassigned += hours
        else:
            planned_unassigned += hours

    name_match = subject.name.strip()
    records = (
        StudyRecord.objects.filter(user=user)
        .filter(end_time__gte=week_start, start_time__lte=week_end)
        .filter(
            Q(chapter__subject_id=subject.id) | Q(subject_name__iexact=name_match)
        )
    )

    for rec in records:
        secs = overlap_seconds(rec.start_time, rec.end_time, week_start, week_end)
        if secs <= 0:
            continue
        hours = Decimal(secs) / Decimal(3600)
        if rec.chapter_id and rec.chapter_id in chapter_ids:
            actual_by_id[rec.chapter_id] += hours
        else:
            c = chapter_by_title_norm.get(_norm_title(rec.chapter_name))
            if c:
                actual_by_id[c.id] += hours
            else:
                actual_unassigned += hours

    planned_total = sum(planned_by_id.values(), Decimal("0")) + planned_unassigned
    actual_total = sum(actual_by_id.values(), Decimal("0")) + actual_unassigned

    planned_by_chapter = {
        c.title: float(planned_by_id[c.id]) for c in chapters
    }
    actual_by_chapter = {c.title: float(actual_by_id[c.id]) for c in chapters}
    if planned_unassigned > 0:
        planned_by_chapter[_UNASSIGNED_KEY] = float(planned_unassigned)
    if actual_unassigned > 0:
        actual_by_chapter[_UNASSIGNED_KEY] = float(actual_unassigned)

    return {
        "planned_hours": float(planned_total),
        "actual_hours": float(actual_total),
        "planned_by_chapter": planned_by_chapter,
        "actual_by_chapter": actual_by_chapter,
        "planned_by_chapter_id": {cid: float(planned_by_id[cid]) for cid in chapter_ids},
        "actual_by_chapter_id": {cid: float(actual_by_id[cid]) for cid in chapter_ids},
        "planned_unassigned_hours": float(planned_unassigned),
        "actual_unassigned_hours": float(actual_unassigned),
        "week_start": week_start,
        "week_end": week_end,
    }


def persist_subject_weekly_stats(user, subject):
    """
    与项目详情「更新」、首页批量更新相同：按本周计划+记录聚合并写入各子任务与项目。
    不修改 already_hours（仅周日 management command 累加）。
    """
    from decimal import Decimal

    chapters = list(Chapter.objects.filter(subject=subject))
    subject.Chapters_count = len(chapters)
    subject.knowledge_points_count = sum(ch.knowledge_points_count for ch in chapters)

    stats = aggregate_subject_weekly_stats(user, subject)
    planned_by_id = stats["planned_by_chapter_id"]
    actual_by_id = stats["actual_by_chapter_id"]

    for ch in chapters:
        ph = Decimal(str(planned_by_id.get(ch.id, 0)))
        ah = Decimal(str(actual_by_id.get(ch.id, 0))).quantize(Decimal("0.01"))
        ch.estimated_hours = max(0, int(round(ph)))
        ch.actual_hours = ah
        if ch.estimated_hours > 0:
            ch.progress = min(
                100,
                max(0, int(float(ch.actual_hours) * 100 / ch.estimated_hours)),
            )
        else:
            ch.progress = 0
        ch.save(update_fields=["estimated_hours", "actual_hours", "progress"])

    subject.estimated_hours = int(round(stats["planned_hours"]))
    subject.actual_study_hours = int(round(stats["actual_hours"]))
    if subject.estimated_hours > 0:
        subject.progress = min(
            100,
            max(0, int(subject.actual_study_hours * 100 / subject.estimated_hours)),
        )
    else:
        subject.progress = 0
    subject.save()
    return stats


def build_home_weekly_rows(user):
    """
    只读聚合当前用户本周各项目计划/投入；两者皆为 0 的项目不进入列表。
    按本周计划时长降序。

    进度条标尺：在「本列表所有项目的计划小时、实际小时」中取全局最大值作为 100%，
    每条计划条、实际条均除以该值，计划与实际共用同一刻度以便对比。
    """
    subjects = Subject.objects.all().order_by("id")
    rows = []
    for subject in subjects:
        stats = aggregate_subject_weekly_stats(user, subject)
        p, a = stats["planned_hours"], stats["actual_hours"]
        if p <= 0 and a <= 0:
            continue
        color = (subject.color or "#4a6bdf").strip()
        if not re.match(r"^#[0-9A-Fa-f]{3}([0-9A-Fa-f]{3})?$", color):
            color = "#4a6bdf"
        rows.append(
            {
                "subject": subject,
                "planned_hours": p,
                "actual_hours": a,
                "color": color,
            }
        )
    rows.sort(key=lambda r: -r["planned_hours"])
    peak = 0.0
    for r in rows:
        peak = max(peak, r["planned_hours"], r["actual_hours"])
    scale = peak if peak > 0 else 1.0
    for r in rows:
        r["plan_bar_pct"] = min(100.0, 100.0 * r["planned_hours"] / scale)
        r["actual_bar_pct"] = min(100.0, 100.0 * r["actual_hours"] / scale)
    return rows


def sum_actual_hours_for_subject_in_range(subject, week_start, week_end, user=None):
    """
    在给定时间窗内，将与科目相关的学习记录重叠时长合计为小时（Decimal）。
    user 为 None 时不按用户过滤（周日汇总用）。
    """
    name_match = subject.name.strip()
    qs = StudyRecord.objects.filter(
        end_time__gte=week_start,
        start_time__lte=week_end,
    ).filter(
        Q(chapter__subject_id=subject.id) | Q(subject_name__iexact=name_match)
    )
    if user is not None:
        qs = qs.filter(user=user)

    total = Decimal("0")
    for rec in qs.iterator():
        secs = overlap_seconds(rec.start_time, rec.end_time, week_start, week_end)
        if secs > 0:
            total += Decimal(secs) / Decimal(3600)
    return total
