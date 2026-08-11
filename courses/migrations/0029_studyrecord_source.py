from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0028_chapter_last_roll_week_snapshot"),
    ]

    operations = [
        migrations.AddField(
            model_name="studyrecord",
            name="source",
            field=models.CharField(
                choices=[("plan", "计划执行"), ("manual", "手动插入")],
                db_index=True,
                default="manual",
                help_text="plan=周历计划完成/记录产生；manual=学习记录页手动插入（日历上显示红点）",
                max_length=16,
                verbose_name="来源",
            ),
        ),
    ]
