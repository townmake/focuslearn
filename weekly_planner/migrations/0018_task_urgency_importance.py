from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("weekly_planner", "0017_quickaccesslibraryicon_square_any_size"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="urgency_level",
            field=models.CharField(
                choices=[
                    ("low", "不紧急"),
                    ("medium", "一般"),
                    ("high", "紧急"),
                ],
                db_index=True,
                default="medium",
                max_length=16,
                verbose_name="紧急程度",
            ),
        ),
        migrations.AddField(
            model_name="task",
            name="importance_level",
            field=models.CharField(
                choices=[
                    ("low", "不重要"),
                    ("medium", "一般"),
                    ("high", "重要"),
                ],
                db_index=True,
                default="medium",
                max_length=16,
                verbose_name="重要程度",
            ),
        ),
    ]
