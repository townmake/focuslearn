from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("weekly_planner", "0014_quick_access_library_icon"),
    ]

    operations = [
        migrations.AddField(
            model_name="quickaccess",
            name="subtitle",
            field=models.CharField(
                blank=True,
                default="",
                help_text="列表卡片上显示在标题下方的简短说明，可选",
                max_length=200,
                verbose_name="副标题",
            ),
        ),
    ]
