# Generated manually for description + due_at (migrate from date)

import datetime

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.utils import timezone


def copy_date_to_due_at(apps, schema_editor):
    UserImportantDate = apps.get_model("weekly_planner", "UserImportantDate")
    for row in UserImportantDate.objects.all():
        if getattr(row, "date", None) and not getattr(row, "due_at", None):
            dt = datetime.datetime.combine(row.date, datetime.time(0, 0))
            if settings.USE_TZ:
                dt = timezone.make_aware(dt, timezone.get_current_timezone())
            row.due_at = dt
            row.save(update_fields=["due_at"])


class Migration(migrations.Migration):

    dependencies = [
        ("weekly_planner", "0006_words"),
    ]

    operations = [
        migrations.AddField(
            model_name="userimportantdate",
            name="description",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="userimportantdate",
            name="due_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="到期时间"),
        ),
        migrations.RunPython(copy_date_to_due_at, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="userimportantdate",
            name="date",
        ),
        migrations.AlterField(
            model_name="userimportantdate",
            name="name",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
    ]
