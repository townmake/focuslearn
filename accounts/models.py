from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """首页「本周项目统计」批量更新成功后的时间戳；无更新则不展示。"""
    weekly_dashboard_refreshed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="首页周统计最后更新时间",
    )
    weekly_dashboard_snapshot = models.JSONField(
        null=True,
        blank=True,
        verbose_name="首页周统计快照",
        help_text="点击「更新」时写入；首页只读此快照，避免每次打开首页全量聚合。",
    )