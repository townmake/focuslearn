"""首页重要日期列表：从 ImportantDatesHomeSnapshot 读取，写入由信号触发 rebuild。"""
from django.db.models import F

from .important_date_api import serialize_important_date
from .models import ImportantDatesHomeSnapshot, UserImportantDate


def rebuild_important_dates_home_snapshot(user_id):
    """聚合当前用户全部提醒为 JSON，写入 ImportantDatesHomeSnapshot。"""
    from django.contrib.auth import get_user_model
    from django.utils import timezone

    User = get_user_model()
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return

    now = timezone.now()
    qs = (
        UserImportantDate.objects.filter(user=user)
        .select_related("planner_task", "planner_task__subject")
        .order_by(F("due_at").asc(nulls_last=True), "id")
    )
    items = []
    for i, o in enumerate(qs):
        row = serialize_important_date(o, now, i)
        if o.due_at:
            row["calendar_date"] = timezone.localtime(o.due_at).strftime("%Y-%m-%d")
        else:
            row["calendar_date"] = ""
        row["planner_task_id"] = o.planner_task_id
        items.append(row)

    ImportantDatesHomeSnapshot.objects.update_or_create(
        user=user, defaults={"items": items}
    )


def get_home_important_dates_items(user):
    """首页视图调用：无快照时现建一次。"""
    snap = ImportantDatesHomeSnapshot.objects.filter(user=user).first()
    if snap is None:
        rebuild_important_dates_home_snapshot(user.pk)
        snap = ImportantDatesHomeSnapshot.objects.filter(user=user).first()
    if not snap:
        return []
    return list(snap.items)
