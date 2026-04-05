from django.apps import AppConfig


class WeeklyPlannerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'weekly_planner'
    verbose_name = '周计划管理'

    def ready(self):
        import weekly_planner.signals  # noqa: F401