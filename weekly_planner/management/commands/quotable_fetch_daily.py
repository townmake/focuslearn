"""
从 Quotable 拉取今日名言，供 crontab 早/中/晚各跑一次。

示例（早 8 点只补「早」档，并强制换新）：
    python manage.py quotable_fetch_daily --slot morning --force

示例（补全今日尚缺的全部时段）：
    python manage.py quotable_fetch_daily
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from weekly_planner.models import DailyQuotableQuote
from weekly_planner.quotable_service import ensure_today_quotable_quotes, refresh_slot


class Command(BaseCommand):
    help = "拉取 Quotable 名言写入今日早/中/晚备用（见 weekly_planner.DailyQuotableQuote）"

    def add_arguments(self, parser):
        parser.add_argument(
            "--slot",
            choices=["morning", "noon", "evening"],
            help="只处理该时段；不传则尝试补全今日三条（仅缺则拉）",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="删除该时段已有记录后重新拉取（需配合 --slot）",
        )

    def handle(self, *args, **options):
        today = timezone.localdate()
        slot = options["slot"]
        force = options["force"]

        if slot:
            if force:
                ok = refresh_slot(today, slot, force=True)
                self.stdout.write(
                    self.style.SUCCESS("已强制刷新时段 %s" % slot)
                    if ok
                    else self.style.WARNING("刷新失败（可查看日志）")
                )
            else:
                ensure_today_quotable_quotes(slots=[slot])
                self.stdout.write(
                    self.style.SUCCESS("已处理时段 %s（缺则拉取）" % slot)
                )
        else:
            if force:
                self.stderr.write("--force 需配合 --slot")
                return
            ensure_today_quotable_quotes()
            n = DailyQuotableQuote.objects.filter(date=today).count()
            self.stdout.write(self.style.SUCCESS("今日已存 %s 条名言" % n))
