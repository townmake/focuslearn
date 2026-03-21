
from django.core.management.base import BaseCommand
from courses.models import Chapter

class Command(BaseCommand):
    help = 'Initialize chapter count fields'

    def handle(self, *args, **options):
        chapters = Chapter.objects.all()
        total = chapters.count()
        
        for i, chapter in enumerate(chapters, 1):
            chapter.update_counts()
            self.stdout.write(f'Processed {i}/{total}: {chapter.title}')
            
        self.stdout.write(self.style.SUCCESS('Successfully initialized all chapter counts'))
