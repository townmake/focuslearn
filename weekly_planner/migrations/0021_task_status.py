from django.db import migrations, models


def forwards_sync_status(apps, schema_editor):
    Task = apps.get_model("weekly_planner", "Task")
    Task.objects.filter(is_completed=True).update(status="done")
    Task.objects.filter(is_completed=False).update(status="todo")


class Migration(migrations.Migration):

    dependencies = [
        ("weekly_planner", "0020_task_urgency_importance_default_low"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="status",
            field=models.CharField(
                choices=[("todo", "待办"), ("done", "完成")],
                db_index=True,
                default="todo",
                help_text="待办 / 完成；与 is_completed 保持同步",
                max_length=16,
                verbose_name="状态",
            ),
        ),
        migrations.RunPython(forwards_sync_status, migrations.RunPython.noop),
    ]
