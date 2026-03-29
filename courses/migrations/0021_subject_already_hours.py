from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0020_alter_studyrecord_page_type_task_types'),
    ]

    operations = [
        migrations.AddField(
            model_name='subject',
            name='already_hours',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                max_digits=10,
                verbose_name='累计已投时长(小时)',
            ),
        ),
    ]
