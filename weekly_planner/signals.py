from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import UserImportantDate


@receiver(post_save, sender=UserImportantDate)
@receiver(post_delete, sender=UserImportantDate)
def refresh_important_dates_home_snapshot_signal(sender, instance, **kwargs):
    from .important_date_snapshot import rebuild_important_dates_home_snapshot

    uid = getattr(instance, "user_id", None)
    if uid:
        rebuild_important_dates_home_snapshot(uid)
