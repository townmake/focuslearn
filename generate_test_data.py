
import os
import django
from django.utils import timezone
from faker import Faker

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learning_system.settings')
django.setup()

from courses.models import Subject, Chapter, KnowledgePoint, Document, Video
from django.contrib.auth.models import User

fake = Faker()

def create_subjects():
    subjects = []
    for i in range(2):
        subject = Subject.objects.create(
            name=fake.word().capitalize() + "科目",
            description=fake.text(),
            estimated_hours=fake.random_int(min=20, max=100),
            order=i+1
        )
        subjects.append(subject)
    return subjects

def create_chapters(subjects):
    chapters = []
    for subject in subjects:
        for i in range(3):
            chapter = Chapter.objects.create(
                subject=subject,
                title=f"第{i+1}章 " + fake.sentence(),
                description=fake.text(),
                order=i+1,
                estimated_hours=fake.random_int(min=2, max=10)
            )
            chapters.append(chapter)
    return chapters

def create_knowledge_points(chapters):
    for chapter in chapters:
        for i in range(5):
            KnowledgePoint.objects.create(
                chapter=chapter,
                title=f"知识点{i+1} " + fake.sentence(),
                description=fake.text(),
                content=fake.text(),
                difficulty=fake.random_int(min=1, max=5)
            )

# def create_resources(chapters):
#     for chapter in chapters:
#         # 创建文档
#         for i in range(2):
#             Document.objects.create(
#                 chapter=chapter,
#                 title=f"文档{i+1} " + fake.sentence(),
#                 file=f"documents/doc_{fake.uuid4()}.pdf"
#             )
        
#         # 创建视频
#         for i in range(3):
#             Video.objects.create(
#                 chapter=chapter,
#                 title=f"视频{i+1} " + fake.sentence(),
#                 url=f"https://example.com/video/{fake.uuid4()}",
#                 duration=fake.random_int(min=300, max=3600)
#             )
        
#         # 创建习题
#         for i in range(5):
#             Exercise.objects.create(
#                 chapter=chapter,
#                 question_type='single_choice',
#                 content=f"问题{i+1}: " + fake.sentence() + "?",
#                 answer=fake.sentence(),
#                 difficulty=fake.random_int(min=1, max=5)
#             )

# def create_admin_user():
#     if not User.objects.filter(username='user').exists():
#         User.objects.create_superuser(
#             username='user',
#             email='user@example.com',
#             password='User1234'
#         )

def main():
    print("开始生成测试数据...")
    subjects = create_subjects()
    chapters = create_chapters(subjects)
    create_knowledge_points(chapters)
    # create_resources(chapters)
    # create_admin_user()
    print("测试数据生成完成！")

if __name__ == '__main__':
    main()
