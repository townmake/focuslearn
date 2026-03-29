from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("weekly_planner", "0007_userimportantdate_due_description"),
    ]

    operations = [
        migrations.CreateModel(
            name="DailyQuotableQuote",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("date", models.DateField(db_index=True, verbose_name="日期")),
                (
                    "slot",
                    models.CharField(
                        choices=[
                            ("morning", "早"),
                            ("noon", "中"),
                            ("evening", "晚"),
                        ],
                        max_length=10,
                        verbose_name="时段",
                    ),
                ),
                ("content", models.TextField(verbose_name="正文")),
                ("author", models.CharField(max_length=200, verbose_name="作者")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "每日名言（Quotable）",
                "verbose_name_plural": "每日名言（Quotable）",
            },
        ),
        migrations.AddConstraint(
            model_name="dailyquotablequote",
            constraint=models.UniqueConstraint(
                fields=("date", "slot"), name="uniq_daily_quotable_date_slot"
            ),
        ),
    ]
