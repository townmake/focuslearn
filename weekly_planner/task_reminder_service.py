"""周历任务与首页「重要日期提醒」双向同步。"""
from datetime import datetime, timedelta

from django.utils import timezone


def task_end_datetime(task):
    dt = datetime.combine(task.end_date, task.end_time)
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def task_times_from_due_at(due_at):
    """以到期时间为任务结束时刻，开始 = 结束前 1 小时（可跨日）。"""
    end_local = timezone.localtime(due_at).replace(second=0, microsecond=0)
    start_local = end_local - timedelta(hours=1)
    return (
        start_local.date(),
        start_local.time().replace(microsecond=0),
        end_local.date(),
        end_local.time().replace(microsecond=0),
    )


def sync_task_important_reminder(task, enabled: bool):
    from weekly_planner.models import UserImportantDate

    if not task or not task.user_id:
        return
    if enabled:
        due = task_end_datetime(task)
        UserImportantDate.objects.update_or_create(
            planner_task=task,
            defaults={
                "user": task.user,
                "name": (task.title or "")[:100],
                "description": ((task.description or "")[:2000]) if task.description else "",
                "due_at": due,
            },
        )
    else:
        UserImportantDate.objects.filter(planner_task=task).delete()


def refresh_important_date_from_task_if_linked(task):
    from weekly_planner.models import UserImportantDate

    if not task.pk:
        return
    rem = UserImportantDate.objects.filter(planner_task_id=task.pk).first()
    if not rem:
        return
    rem.due_at = task_end_datetime(task)
    rem.name = (task.title or "")[:100]
    if task.description is not None:
        rem.description = (task.description or "")[:2000]
    rem.save(update_fields=["due_at", "name", "description"])


def apply_due_at_to_linked_planner_task(important_date, due_at):
    """首页编辑到期时间时，同步周历任务时段。"""
    task = important_date.planner_task
    if not task:
        return
    sd, st, ed, et = task_times_from_due_at(due_at)
    task.start_date, task.start_time = sd, st
    task.end_date, task.end_time = ed, et
    task.save(update_fields=["start_date", "start_time", "end_date", "end_time"])
