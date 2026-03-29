"""
将指定自然周内、各项目下的学习记录实际投入（小时）累加到 Subject.already_hours。

建议在每周日 23:00 左右执行当前周；若在周一凌晨执行，请加 --previous-week 以统计刚结束的上一周。

示例（crontab，周日 23:05）：
    5 23 * * 0 cd /path/to/focuslearn && /path/to/venv/bin/python manage.py rollup_weekly_actual_to_already_hours

示例（周一 00:10，汇总上周）：
    10 0 * * 1 cd /path/to/focuslearn && /path/to/venv/bin/python manage.py rollup_weekly_actual_to_already_hours --previous-week
"""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone as dj_tz

from courses.models import Subject
from courses.subject_weekly_stats import get_local_week_range, sum_actual_hours_for_subject_in_range


class Command(BaseCommand):
    help = "将一周内的学习记录实际投入累加到科目的 already_hours（默认统计「今天所在自然周」，可用 --previous-week）"

    def add_arguments(self, parser):
        parser.add_argument(
            "--previous-week",
            action="store_true",
            help="以「昨天」为参考日确定自然周，适用于周一凌晨汇总刚结束的一周",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="只打印将要累加的数值，不写库",
        )

    def handle(self, *args, **options):
        ref = dj_tz.localtime(dj_tz.now())
        if options["previous_week"]:
            from datetime import timedelta

            ref = ref - timedelta(days=1)
        week_start, week_end = get_local_week_range(ref)

        self.stdout.write(
            f"统计窗口（本地时区）: {week_start.isoformat()} — {week_end.isoformat()}"
        )

        updated = 0
        for subject in Subject.objects.all().order_by("id"):
            delta = sum_actual_hours_for_subject_in_range(
                subject, week_start, week_end, user=None
            )
            if delta <= 0:
                continue
            self.stdout.write(
                f"  科目 [{subject.id}] {subject.name}: +{delta} 小时 -> already_hours"
            )
            if not options["dry_run"]:
                subject.already_hours = (subject.already_hours or Decimal("0")) + delta
                subject.save(update_fields=["already_hours"])
            updated += 1

        if options["dry_run"]:
            self.stdout.write(self.style.WARNING(f"dry-run：未写入数据库，共 {updated} 个科目有数据"))
        else:
            self.stdout.write(self.style.SUCCESS(f"完成，已更新 {updated} 个科目"))
