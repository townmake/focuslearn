# Generated manually — remove KnowledgePoint difficulty / memory / mastery fields

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0018_subject_category'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='knowledgepoint',
            name='difficulty',
        ),
        migrations.RemoveField(
            model_name='knowledgepoint',
            name='memory_level',
        ),
        migrations.RemoveField(
            model_name='knowledgepoint',
            name='mastery_level',
        ),
    ]
