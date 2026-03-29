# 学习记录 page_type 改为任务类型枚举，并迁移旧数据

from django.db import migrations, models


def migrate_studyrecord_page_types(apps, schema_editor):
    StudyRecord = apps.get_model('courses', 'StudyRecord')
    old_to_new = {
        'study': 'thinking',
        'exercise': 'implementation',
        'review': 'retrospective',
        'other': 'other',
    }
    for old_val, new_val in old_to_new.items():
        StudyRecord.objects.filter(page_type=old_val).update(page_type=new_val)
    valid = {
        'research', 'thinking', 'communication', 'implementation',
        'retrospective', 'process_step', 'other',
    }
    StudyRecord.objects.exclude(page_type__in=valid).update(page_type='other')


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0019_remove_knowledgepoint_rating_fields'),
    ]

    operations = [
        migrations.RunPython(migrate_studyrecord_page_types, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='studyrecord',
            name='page_type',
            field=models.CharField(
                choices=[
                    ('research', '调研'),
                    ('thinking', '思考'),
                    ('communication', '沟通'),
                    ('implementation', '实施'),
                    ('retrospective', '复盘'),
                    ('process_step', '流程步骤'),
                    ('other', '其他'),
                ],
                max_length=20,
                verbose_name='任务类型',
            ),
        ),
    ]
