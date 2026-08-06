"""
项目（科目）周维度统计：周计划（周历 Task）与周学习记录（StudyRecord），按章节/任务名分组。
"""
import re
import types
from collections import defaultdict
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.db.models import Q
from django.utils import timezone as dj_tz

from .models import Chapter, StudyRecord, Subject

_UNASSIGNED_KEY = "__未归属子任务__"

# 首页快照中「未关联科目/章节的计划任务」行的占位 id（非数据库 Subject）
ORPHAN_WEEKLY_PLAN_SUBJECT_ID = 0
_ORPHAN_WEEKLY_PLAN_LABEL = "未关联科目的计划任务"


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


def aggregate_subjects_week_list_stats(user, subject_ids, week_start=None, week_end=None):
    """
    项目列表「本周」四项统计（批量，按自然周窗口）：

    - week_task_count：本周有重叠的周历计划条数（不含待安排）
    - week_unfinished_task_count：上述计划中未完成（is_completed=False）条数
    - week_planned_hours：本周计划重叠时长合计（小时）
    - week_actual_hours：本周学习记录重叠时长合计（小时）

    归属：优先 chapter.subject_id，否则 task.subject_id；
    记录优先 chapter.subject_id，否则按 subject_name 匹配。
    """
    from weekly_planner.models import Task

    ids = [int(i) for i in subject_ids if i is not None]
    empty = {
        "week_task_count": 0,
        "week_unfinished_task_count": 0,
        "week_planned_hours": 0.0,
        "week_actual_hours": 0.0,
    }
    result = {sid: dict(empty) for sid in ids}
    if not ids:
        return result

    if week_start is None or week_end is None:
        week_start, week_end = get_local_week_range()
    tz = dj_tz.get_current_timezone()
    ws_d, we_d = week_start.date(), week_end.date()

    id_set = set(ids)
    subjects = list(Subject.objects.filter(id__in=ids).only("id", "name"))
    name_to_id = {}
    for s in subjects:
        k = (s.name or "").strip().casefold()
        if k and k not in name_to_id:
            name_to_id[k] = s.id

    task_count = defaultdict(int)
    unfinished_count = defaultdict(int)
    planned_hours = defaultdict(lambda: Decimal("0"))
    actual_hours = defaultdict(lambda: Decimal("0"))

    tasks = (
        Task.objects.filter(user=user)
        .filter(Q(subject_id__in=ids) | Q(chapter__subject_id__in=ids))
        .filter(start_date__lte=we_d, end_date__gte=ws_d)
        .filter(is_unscheduled=False)
        .select_related("chapter")
        .only(
            "id",
            "subject_id",
            "chapter_id",
            "is_completed",
            "start_date",
            "start_time",
            "end_date",
            "end_time",
            "chapter__subject_id",
        )
    )
    for task in tasks.iterator():
        sid = None
        if task.chapter_id and getattr(task.chapter, "subject_id", None) in id_set:
            sid = task.chapter.subject_id
        elif task.subject_id in id_set:
            sid = task.subject_id
        if sid is None:
            continue
        t0, t1 = _task_aware_interval(task, tz)
        secs = overlap_seconds(t0, t1, week_start, week_end)
        if secs <= 0:
            continue
        task_count[sid] += 1
        if not task.is_completed:
            unfinished_count[sid] += 1
        planned_hours[sid] += Decimal(secs) / Decimal(3600)

    name_match_q = Q()
    for s in subjects:
        n = (s.name or "").strip()
        if n:
            name_match_q |= Q(subject_name__iexact=n)

    records = StudyRecord.objects.filter(
        user=user,
        end_time__gte=week_start,
        start_time__lte=week_end,
    ).filter(Q(chapter__subject_id__in=ids) | name_match_q).select_related("chapter").only(
        "id",
        "chapter_id",
        "subject_name",
        "start_time",
        "end_time",
        "chapter__subject_id",
    )
    for rec in records.iterator():
        sid = None
        if rec.chapter_id and getattr(rec.chapter, "subject_id", None) in id_set:
            sid = rec.chapter.subject_id
        else:
            sid = name_to_id.get((rec.subject_name or "").strip().casefold())
        if sid is None or sid not in id_set:
            continue
        secs = overlap_seconds(rec.start_time, rec.end_time, week_start, week_end)
        if secs <= 0:
            continue
        actual_hours[sid] += Decimal(secs) / Decimal(3600)

    for sid in ids:
        result[sid] = {
            "week_task_count": task_count.get(sid, 0),
            "week_unfinished_task_count": unfinished_count.get(sid, 0),
            "week_planned_hours": float(
                planned_hours.get(sid, Decimal("0")).quantize(Decimal("0.01"))
            ),
            "week_actual_hours": float(
                actual_hours.get(sid, Decimal("0")).quantize(Decimal("0.01"))
            ),
        }
    return result


def attach_subject_week_list_stats(subjects, stats_map):
    """给 Subject 挂上本周列表展示字段。"""
    out = []
    for s in subjects:
        st = stats_map.get(
            s.id,
            {
                "week_task_count": 0,
                "week_unfinished_task_count": 0,
                "week_planned_hours": 0.0,
                "week_actual_hours": 0.0,
            },
        )
        s.week_task_count = st["week_task_count"]
        s.week_unfinished_task_count = st["week_unfinished_task_count"]
        s.week_planned_hours = st["week_planned_hours"]
        s.week_actual_hours = st["week_actual_hours"]
        out.append(s)
    return out


def _orphan_weekly_plan_namespace(display_name=None):
    """用于首页列表展示：无真实 Subject 时的占位对象（id=0，不可点进项目详情）。"""
    name = (display_name or _ORPHAN_WEEKLY_PLAN_LABEL).strip() or _ORPHAN_WEEKLY_PLAN_LABEL
    return types.SimpleNamespace(id=ORPHAN_WEEKLY_PLAN_SUBJECT_ID, pk=ORPHAN_WEEKLY_PLAN_SUBJECT_ID, name=name)


def orphan_weekly_planned_hours(user, week_start, week_end, ws_d, we_d, tz):
    """
    周历中「科目、章节均为空」的任务，不会进入 aggregate_subject_weekly_stats 的任一条目，
    在日历里仍可能显示；此处单独汇总本周与窗口重叠的计划小时。
    """
    from weekly_planner.models import Task

    total = Decimal("0")
    qs = Task.objects.filter(user=user).filter(
        start_date__lte=we_d,
        end_date__gte=ws_d,
        subject__isnull=True,
        chapter__isnull=True,
    )
    for task in qs:
        t0, t1 = _task_aware_interval(task, tz)
        secs = overlap_seconds(t0, t1, week_start, week_end)
        if secs > 0:
            total += Decimal(secs) / Decimal(3600)
    return float(total)


def _normalize_subject_bar_color(subject, fallback_hex="#4a6bdf"):
    color = (subject.color or fallback_hex).strip()
    if not re.match(r"^#[0-9A-Fa-f]{3}([0-9A-Fa-f]{3})?$", color):
        color = fallback_hex
    return color


def _apply_weekly_bar_percentages(rows):
    """进度条标尺：列表内计划/实际小时全局最大值为 100%。会就地写入 plan_bar_pct、actual_bar_pct。"""
    peak = 0.0
    for r in rows:
        peak = max(peak, r["planned_hours"], r["actual_hours"])
    scale = peak if peak > 0 else 1.0
    for r in rows:
        r["plan_bar_pct"] = min(100.0, 100.0 * r["planned_hours"] / scale)
        r["actual_bar_pct"] = min(100.0, 100.0 * r["actual_hours"] / scale)
    return rows


def build_home_weekly_rows(user):
    """
    只读聚合当前用户本周各项目计划/投入；两者皆为 0 的项目不进入列表。
    按本周计划时长降序。

    进度条标尺：在「本列表所有项目的计划小时、实际小时」中取全局最大值作为 100%，
    每条计划条、实际条均除以该值，计划与实际共用同一刻度以便对比。

    注意：会查询周历与学习记录，开销较大；首页展示应优先使用快照（见 snapshot / restore）。
    """
    subjects = Subject.objects.all().order_by("id")
    rows = []
    for subject in subjects:
        stats = aggregate_subject_weekly_stats(user, subject)
        p, a = stats["planned_hours"], stats["actual_hours"]
        if p <= 0 and a <= 0:
            continue
        rows.append(
            {
                "subject": subject,
                "planned_hours": p,
                "actual_hours": a,
                "color": _normalize_subject_bar_color(subject),
            }
        )
    rows.sort(key=lambda r: -r["planned_hours"])

    tz = dj_tz.get_current_timezone()
    week_start, week_end = get_local_week_range()
    ws_d, we_d = week_start.date(), week_end.date()
    orphan_p = orphan_weekly_planned_hours(user, week_start, week_end, ws_d, we_d, tz)
    if orphan_p > 0:
        rows.append(
            {
                "subject": _orphan_weekly_plan_namespace(),
                "planned_hours": orphan_p,
                "actual_hours": 0.0,
                "color": "#888888",
            }
        )

    return _apply_weekly_bar_percentages(rows)


def snapshot_home_weekly_rows(rows):
    """将 build_home_weekly_rows 的结果序列化，写入用户快照字段。"""
    out = []
    for r in rows:
        sid = r["subject"].pk
        out.append(
            {
                "subject_id": sid,
                "subject_name": r["subject"].name,
                "color": r["color"],
                "planned_hours": float(r["planned_hours"]),
                "actual_hours": float(r["actual_hours"]),
            }
        )
    return out


def restore_home_weekly_rows_from_snapshot(snapshot):
    """
    从用户保存的快照恢复首页列表（仅查 Subject，不再聚合 Task/StudyRecord）。
    snapshot 为 None 或空列表时返回 []。
    """
    if not snapshot:
        return []
    ids = [
        x["subject_id"]
        for x in snapshot
        if x.get("subject_id") is not None and x["subject_id"] != ORPHAN_WEEKLY_PLAN_SUBJECT_ID
    ]
    subjects_by_id = {s.id: s for s in Subject.objects.filter(pk__in=ids)}
    rows = []
    for x in snapshot:
        sid = x.get("subject_id")
        if sid == ORPHAN_WEEKLY_PLAN_SUBJECT_ID:
            rows.append(
                {
                    "subject": _orphan_weekly_plan_namespace(x.get("subject_name")),
                    "planned_hours": float(x["planned_hours"]),
                    "actual_hours": float(x.get("actual_hours") or 0),
                    "color": (x.get("color") or "#888888").strip(),
                }
            )
            continue
        subj = subjects_by_id.get(sid)
        if not subj:
            continue
        raw_color = (x.get("color") or subj.color or "#4a6bdf").strip()
        if not re.match(r"^#[0-9A-Fa-f]{3}([0-9A-Fa-f]{3})?$", raw_color):
            raw_color = _normalize_subject_bar_color(subj)
        rows.append(
            {
                "subject": subj,
                "planned_hours": float(x["planned_hours"]),
                "actual_hours": float(x["actual_hours"]),
                "color": raw_color,
            }
        )
    rows.sort(key=lambda r: -r["planned_hours"])
    return _apply_weekly_bar_percentages(rows)


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


def _task_duration_hours(task, tz):
    """单条周历任务的计划时长（小时）。"""
    t0, t1 = _task_aware_interval(task, tz)
    secs = max(0, int((t1 - t0).total_seconds()))
    return Decimal(secs) / Decimal(3600)


def aggregate_chapters_week_plan_record_stats(user, subject, week_start=None, week_end=None):
    """
    仅统计「本周」窗口内、按 chapter 外键归属的：

    - plan_task_count：与本周有重叠的周历 Task 条数
    - planned_hours：与本周重叠的计划时长（小时）
    - actual_hours：与本周重叠的学习记录时长（小时）

    返回 dict[chapter_id] -> {plan_task_count, planned_hours, actual_hours}
    """
    from weekly_planner.models import Task

    if week_start is None or week_end is None:
        week_start, week_end = get_local_week_range()
    tz = dj_tz.get_current_timezone()
    ws_d, we_d = week_start.date(), week_end.date()

    chapters = list(Chapter.objects.filter(subject=subject).only("id"))
    chapter_ids = [c.id for c in chapters]
    result = {
        cid: {
            "plan_task_count": 0,
            "planned_hours": 0.0,
            "actual_hours": 0.0,
        }
        for cid in chapter_ids
    }
    if not chapter_ids:
        return result

    planned_hours = defaultdict(lambda: Decimal("0"))
    plan_counts = defaultdict(int)
    actual_hours = defaultdict(lambda: Decimal("0"))

    tasks = (
        Task.objects.filter(user=user, chapter_id__in=chapter_ids)
        .filter(start_date__lte=we_d, end_date__gte=ws_d)
        .only("id", "chapter_id", "start_date", "start_time", "end_date", "end_time")
    )
    for task in tasks.iterator():
        cid = task.chapter_id
        if cid not in result:
            continue
        t0, t1 = _task_aware_interval(task, tz)
        secs = overlap_seconds(t0, t1, week_start, week_end)
        if secs <= 0:
            continue
        plan_counts[cid] += 1
        planned_hours[cid] += Decimal(secs) / Decimal(3600)

    records = StudyRecord.objects.filter(
        user=user,
        chapter_id__in=chapter_ids,
        end_time__gte=week_start,
        start_time__lte=week_end,
    ).only("id", "chapter_id", "start_time", "end_time")
    for rec in records.iterator():
        cid = rec.chapter_id
        if cid not in result:
            continue
        secs = overlap_seconds(rec.start_time, rec.end_time, week_start, week_end)
        if secs <= 0:
            continue
        actual_hours[cid] += Decimal(secs) / Decimal(3600)

    for cid in chapter_ids:
        result[cid] = {
            "plan_task_count": plan_counts.get(cid, 0),
            "planned_hours": float(
                planned_hours.get(cid, Decimal("0")).quantize(Decimal("0.01"))
            ),
            "actual_hours": float(
                actual_hours.get(cid, Decimal("0")).quantize(Decimal("0.01"))
            ),
        }
    return result


def rollup_subject_week_stats_into_history(user, subject):
    """
    在项目「总结」插入成功后调用：把本周各任务的三项统计累加进 Chapter 历史字段。

    - 新的一周：直接累加本周值，并记下本周贡献快照
    - 同一周再次写入总结：用最新本周值「替换」该周贡献（先减旧快照再加新值），避免早写总结把本周锁死
    """
    from django.db import transaction

    week_start, week_end = get_local_week_range()
    ws_d = week_start.date()
    week_stats = aggregate_chapters_week_plan_record_stats(
        user, subject, week_start=week_start, week_end=week_end
    )

    with transaction.atomic():
        subj = Subject.objects.select_for_update().get(pk=subject.pk)
        chapters = list(
            Chapter.objects.select_for_update().filter(subject_id=subj.id)
        )
        replaced = subj.hist_stats_rolled_week_start == ws_d

        for ch in chapters:
            s = week_stats.get(
                ch.id,
                {"plan_task_count": 0, "planned_hours": 0.0, "actual_hours": 0.0},
            )
            new_cnt = int(s["plan_task_count"] or 0)
            new_plan = Decimal(str(s["planned_hours"] or 0)).quantize(Decimal("0.01"))
            new_act = Decimal(str(s["actual_hours"] or 0)).quantize(Decimal("0.01"))

            hist_cnt = int(ch.hist_plan_task_count or 0)
            hist_plan = Decimal(str(ch.hist_planned_hours or 0))
            hist_act = Decimal(str(ch.hist_actual_hours or 0))

            if ch.last_roll_week_start == ws_d:
                hist_cnt = max(0, hist_cnt - int(ch.last_roll_plan_task_count or 0))
                hist_plan = max(
                    Decimal("0"),
                    hist_plan - Decimal(str(ch.last_roll_planned_hours or 0)),
                )
                hist_act = max(
                    Decimal("0"),
                    hist_act - Decimal(str(ch.last_roll_actual_hours or 0)),
                )

            ch.hist_plan_task_count = hist_cnt + new_cnt
            ch.hist_planned_hours = (hist_plan + new_plan).quantize(Decimal("0.01"))
            ch.hist_actual_hours = (hist_act + new_act).quantize(Decimal("0.01"))
            ch.last_roll_week_start = ws_d
            ch.last_roll_plan_task_count = new_cnt
            ch.last_roll_planned_hours = new_plan
            ch.last_roll_actual_hours = new_act
            ch.save(
                update_fields=[
                    "hist_plan_task_count",
                    "hist_planned_hours",
                    "hist_actual_hours",
                    "last_roll_week_start",
                    "last_roll_plan_task_count",
                    "last_roll_planned_hours",
                    "last_roll_actual_hours",
                ]
            )

        subj.hist_stats_rolled_week_start = ws_d
        subj.save(update_fields=["hist_stats_rolled_week_start"])

    return {
        "rolled": True,
        "replaced_same_week": replaced,
        "week_start": str(ws_d),
        "by_chapter": week_stats,
    }


def attach_chapter_plan_record_stats(chapters, week_stats_map):
    """给 Chapter 挂上本周实时统计 + 库内历史累计（不写库）。"""
    out = []
    for ch in chapters:
        w = week_stats_map.get(
            ch.id,
            {"plan_task_count": 0, "planned_hours": 0.0, "actual_hours": 0.0},
        )
        ch.week_plan_task_count = w["plan_task_count"]
        ch.week_planned_hours = w["planned_hours"]
        ch.week_actual_hours = w["actual_hours"]
        ch.hist_plan_task_count_display = int(getattr(ch, "hist_plan_task_count", 0) or 0)
        ch.hist_planned_hours_display = float(getattr(ch, "hist_planned_hours", 0) or 0)
        ch.hist_actual_hours_display = float(getattr(ch, "hist_actual_hours", 0) or 0)
        out.append(ch)
    return out


# 兼容旧名
def aggregate_chapters_plan_record_stats(user, subject):
    return aggregate_chapters_week_plan_record_stats(user, subject)
