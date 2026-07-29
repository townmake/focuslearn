"""项目热度：创建周历任务后 +1（上限 10）；每累计 10 次创建，全体项目热度 -1（下限 0）。"""

from django.db import transaction
from django.db.models import F


def bump_heat_after_task_create(subject_id):
    if not subject_id:
        return

    from .models import Subject, SubjectHeatTracker

    with transaction.atomic():
        Subject.objects.filter(pk=subject_id, heat__lt=10).update(heat=F("heat") + 1)

        tracker, _ = SubjectHeatTracker.objects.select_for_update().get_or_create(
            pk=1,
            defaults={"creations_since_decay": 0},
        )
        tracker.creations_since_decay += 1
        if tracker.creations_since_decay >= 10:
            Subject.objects.filter(heat__gt=0).update(heat=F("heat") - 1)
            tracker.creations_since_decay = 0
        tracker.save(update_fields=["creations_since_decay"])
