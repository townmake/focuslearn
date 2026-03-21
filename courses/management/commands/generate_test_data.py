
from django.core.management.base import BaseCommand
from courses.models import Subject, Chapter, KnowledgePoint, Document, Video
from django.contrib.auth.models import User
import random
from faker import Faker

fake = Faker()

class Command(BaseCommand):
    help = 'Generate test data for the learning system'

    def handle(self, *args, **options):
        # 创建测试科目
        subjects = []
        for i in range(1, 6):
            subject = Subject.objects.create(
                name=f"测试科目{i}",
                description=fake.text(),
                color=f"#{random.randint(0, 0xFFFFFF):06x}",
                estimated_hours=random.randint(10, 50)
            )
            subjects.append(subject)
            self.stdout.write(f'Created subject: {subject.name}')

            # 为每个科目创建3-5个章节
            for j in range(1, random.randint(3, 6)):
                chapter = Chapter.objects.create(
                    subject=subject,
                    title=f"{subject.name}-章节{j}",
                    content=fake.text(),
                    description=fake.sentence(),
                    order=j
                )
                self.stdout.write(f'Created chapter: {chapter.title}')

                # 为每个章节创建5-10个知识点
                for k in range(1, random.randint(5, 11)):
                    knowledge_point = KnowledgePoint.objects.create(
                        chapter=chapter,
                        title=f"{chapter.title}-知识点{k}",
                        content=fake.text(),
                        order=k
                    )
                    self.stdout.write(f'Created knowledge point: {knowledge_point.title}')

                # 为每个章节创建3-5个文档
                for d in range(1, random.randint(3, 6)):
                    document = Document.objects.create(
                        chapter=chapter,
                        name=f"{chapter.title}-文档{d}",
                        file_type=random.choice(['pdf', 'doc', 'xls', 'txt']),
                        size=random.randint(100, 5000)
                    )
                    self.stdout.write(f'Created document: {document.name}')

                # 为每个章节创建2-4个视频
                for v in range(1, random.randint(2, 5)):
                    video = Video.objects.create(
                        chapter=chapter,
                        name=f"{chapter.title}-视频{v}",
                        duration=random.randint(300, 3600)
                    )
                    self.stdout.write(f'Created video: {video.name}')

        self.stdout.write(self.style.SUCCESS('Successfully generated test data'))
