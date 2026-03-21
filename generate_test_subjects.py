
import os
import random
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learning_system.settings')
django.setup()

from courses.models import Subject
from faker import Faker

fake = Faker('zh_CN')

def create_test_subjects(count=20):
    for i in range(count):
        subject = Subject.objects.create(
            name=f"{fake.word()}科目{i+1}",
            description=fake.text(),
            color=f"#{''.join([random.choice('0123456789ABCDEF') for _ in range(6)])}",
            estimated_hours=random.randint(10, 100),
            actual_study_hours=random.randint(0, 100),
            order=i
        )
        print(f"创建科目: {subject.name}")

if __name__ == '__main__':
    print("开始生成测试科目数据...")
    create_test_subjects()
    print("测试数据生成完成！")
