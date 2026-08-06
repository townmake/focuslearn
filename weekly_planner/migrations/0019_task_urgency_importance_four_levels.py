from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("weekly_planner", "0018_task_urgency_importance"),
    ]

    operations = [
        migrations.AlterField(
            model_name="task",
            name="urgency_level",
            field=models.CharField(
                choices=[
                    ("low", "低"),
                    ("medium", "中"),
                    ("high", "高"),
                    ("critical", "紧急"),
                ],
                db_index=True,
                default="medium",
                max_length=16,
                verbose_name="紧急程度",
            ),
        ),
        migrations.AlterField(
            model_name="task",
            name="importance_level",
            field=models.CharField(
                choices=[
                    ("low", "低"),
                    ("medium", "中"),
                    ("high", "高"),
                    ("critical", "重要"),
                ],
                db_index=True,
                default="medium",
                max_length=16,
                verbose_name="重要程度",
            ),
        ),
    ]
