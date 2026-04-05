import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("weekly_planner", "0013_deepseek_and_weekly_ai_summary"),
    ]

    operations = [
        migrations.CreateModel(
            name="QuickAccessLibraryIcon",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(blank=True, default="", max_length=80, verbose_name="名称")),
                ("image", models.ImageField(upload_to="quick_access_library_icons/", verbose_name="图标")),
                (
                    "sort_order",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="越小越靠前",
                        verbose_name="排序",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "速记图标库",
                "verbose_name_plural": "速记图标库",
                "ordering": ("sort_order", "id"),
            },
        ),
        migrations.AddField(
            model_name="quickaccess",
            name="library_icon",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="quick_access_items",
                to="weekly_planner.quickaccesslibraryicon",
                verbose_name="图标库图标",
            ),
        ),
        migrations.AlterField(
            model_name="quickaccess",
            name="icon",
            field=models.ImageField(
                blank=True,
                help_text="历史数据；新建请从图标库选择",
                null=True,
                upload_to="quick_access_icons/",
                verbose_name="图标（已弃用）",
            ),
        ),
    ]
