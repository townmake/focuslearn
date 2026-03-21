
from django.core.management.base import BaseCommand
from django.utils import timezone
from courses.models import Exercise, ExerciseAnswer, ReviewSet, Subject
from weekly_planner.models import Task
from datetime import timedelta
import math

class Command(BaseCommand):
    help = '基于spaced repetition 算法，生成每日复习计划'

    def handle(self, *args, **options):
        # 1. 获取今日需要复习的习题
        exercises_to_review = self.get_exercises_for_review()

        if not exercises_to_review:
            self.stdout.write("No exercises need review today")
            return

        # 2. 按照subject分组
        subjects = Subject.objects.all()
        
        for subject in subjects:
            # 获取需要复习的习题（根据算法筛选）
            exercises = self.get_review_exercises(subject,exercises_to_review)
            
            if exercises.exists():
                # 创建或更新每日复习集
                review_set, created = ReviewSet.objects.get_or_create(
                    name=f"{subject.name}-{timezone.now().date()}-复习任务",
                    chapter=None,
                    subject_id=subject.pk,
                    defaults={
                        'chapter': None  # 设置为独立复习集，不关联特定章节
                    }
                )
                review_set.exercises.set(exercises)
                review_set.save()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'成功为科目[{subject.name}]创建复习集，包含{exercises.count()}道习题'
                    )
                )

        
    def get_exercises_for_review(self):
        """基于间隔重复算法获取需要复习的习题"""
        exercises = []
        
        # 获取所有有答题记录的习题
        answered_exercises = Exercise.objects.filter(
            answers__isnull=False
        ).distinct()
        
        for exercise in answered_exercises:
            # 获取最新的3次答题记录
            latest_answers = exercise.answers.order_by('-created_at')[:3]
            
            if not latest_answers:
                continue
                
            # 计算记忆强度因子
            memory_factor = self.calculate_memory_factor(latest_answers)
            
            # 计算下次复习时间
            next_review_date = self.calculate_next_review_date(
                latest_answers[0].created_at.date(),
                memory_factor
            )
            
            # 确保日期不早于当前日期
            next_review_date = max(next_review_date, timezone.now().date())
            
            # 更新习题的下次复习日期
            exercise.next_review_date = next_review_date
            exercise.save()
            
            # 如果今天需要复习
            if next_review_date == timezone.now().date():
                exercises.append(exercise)
        
        return exercises
    
    def calculate_memory_factor(self, answer_records):
        """基于答题记录计算记忆强度因子"""
        # 1. 计算基础指标
        correct_count = sum(1 for a in answer_records if a.is_correct)
        correctness_ratio = correct_count / len(answer_records)
        
        # 2. 计算各项指标平均值（标准化到0-1范围）
        avg_difficulty = sum(a.difficulty for a in answer_records) / len(answer_records) / 5  # 1-5 → 0.2-1
        avg_memory = sum(a.memory_level for a in answer_records) / len(answer_records) / 5     # 1-5 → 0.2-1
        avg_mastery = sum(a.mastery_level for a in answer_records) / len(answer_records) / 5  # 1-5 → 0.2-1
        
        # 3. 综合计算记忆因子（带权重）
        weights = {
            'correctness': 0.4,    # 正确率最重要
            'mastery': 0.2,        # 掌握度次之
            'memory': 0.2,         # 记忆度
            'difficulty': 0.2      # 难度影响最小
        }
        
        memory_factor = (
            weights['correctness'] * correctness_ratio +
            weights['mastery'] * avg_mastery +
            weights['memory'] * avg_memory +
            weights['difficulty'] * (1 - avg_difficulty)  # 难度越高，记忆因子越低
        )
        
        return max(0.1, min(0.99, memory_factor))  # 限制在0.1-0.99之间
    
    def calculate_next_review_date(self, last_review_date, memory_factor):
        """基于记忆因子计算下次复习日期"""
        # 使用Anki的间隔重复算法变体
        if memory_factor > 0.9:
            interval_days = 14  # 记忆很好，两周后复习
        elif memory_factor > 0.7:
            interval_days = 7   # 记忆较好，一周后复习
        elif memory_factor > 0.5:
            interval_days = 3   # 记忆一般，3天后复习
        elif memory_factor > 0.3:
            interval_days = 1   # 记忆较差，明天复习
        else:
            interval_days = 0   # 记忆很差，今天就需要复习
            
        return last_review_date + timedelta(days=interval_days)
    
    def create_review_set(self, exercises):
        """创建复习集"""
        today = timezone.now().date()
        review_set, created = ReviewSet.objects.get_or_create(
            name=f"每日复习 - {today}",
            defaults={
                'chapter': exercises[0].chapter if exercises else None
            }
        )
        
        # 添加习题到复习集
        review_set.exercises.add(*exercises)
        return review_set
    
    def create_review_task(self, review_set):
        """创建复习任务"""
        today = timezone.now().date()
        Task.objects.create(
            title=f"复习 {review_set.name}",
            description=f"包含{review_set.exercises.count()}道需要复习的习题",
            start_date=today,
            end_date=today,
            start_time=timezone.now().time(),
            end_time=(timezone.now() + timedelta(hours=1)).time(),
            subject=review_set.chapter.subject if review_set.chapter else None,
            chapter=review_set.chapter,
            focus_level=70,
            energy_level=60
        )

    def get_review_exercises(self, subject, exercise_to_be_reviewed):
        """获取需要复习的习题"""
        # 筛选属于该科目的习题
        subject_exercises = [
            ex for ex in exercise_to_be_reviewed 
            if ex.chapter and ex.chapter.subject == subject
        ]
        
        if not subject_exercises:
            self.stdout.write(
                self.style.WARNING(f'科目[{subject.name}]没有需要复习的习题')
            )
            return Exercise.objects.none()
            
        # 转换为QuerySet
        exercise_ids = [ex.id for ex in subject_exercises]
        return Exercise.objects.filter(id__in=exercise_ids)
        


