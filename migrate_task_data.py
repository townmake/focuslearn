import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learning_system.settings')
django.setup()

from django.db import transaction
from weekly_planner.models import Task
from courses.models import Subject, Chapter

def migrate_task_data():
    """
    将现有任务数据迁移到新结构
    1. 为所有任务添加用户关联（从task_list获取）
    2. 为所有任务添加默认科目和章节
    3. 为所有任务添加默认的专注力和体力值
    """
    print("开始迁移任务数据...")
    
    # 获取或创建默认科目
    default_subject, created = Subject.objects.get_or_create(
        name="默认科目",
        defaults={
            "description": "系统迁移时自动创建的默认科目",
            "color": "#3498db"
        }
    )
    if created:
        print(f"创建了默认科目: {default_subject.name}")
    
    # 获取或创建默认章节
    default_chapter, created = Chapter.objects.get_or_create(
        name="默认章节",
        subject=default_subject,
        defaults={
            "description": "系统迁移时自动创建的默认章节",
            "order": 0
        }
    )
    if created:
        print(f"创建了默认章节: {default_chapter.name}")
    
    # 更新所有任务
    with transaction.atomic():
        tasks_without_user = Task.objects.filter(user__isnull=True)
        count = tasks_without_user.count()
        
        if count == 0:
            print("没有需要迁移的任务数据")
            return
        
        print(f"发现 {count} 个需要迁移的任务")
        
        # 获取系统中的第一个用户作为默认用户
        from django.contrib.auth import get_user_model
        User = get_user_model()
        default_user = None
        if User.objects.exists():
            default_user = User.objects.first()
            print(f"使用默认用户: {default_user.username}")
        
        for task in tasks_without_user:
            # 从任务列表获取用户
            if hasattr(task, 'task_list') and task.task_list and task.task_list.user:
                task.user = task.task_list.user
            elif default_user:
                task.user = default_user
                print(f"为任务 {task.id} 分配默认用户")
            else:
                print(f"警告: 任务 {task.id} 没有关联的任务列表或用户，且系统中没有用户，无法迁移")
                continue
                
            task.subject = default_subject
            task.chapter = default_chapter
            task.focus_level = 50  # 默认专注力
            task.energy_level = 50  # 默认体力
            task.save()
            print(f"已迁移任务: {task.title}")
    
    print("任务数据迁移完成")

if __name__ == "__main__":
    migrate_task_data()