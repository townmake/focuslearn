from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_auto_20250527_1439"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="weekly_dashboard_refreshed_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="首页周统计最后更新时间",
            ),
        ),
    ]
