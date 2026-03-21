from django.db import models
from accounts.models import User
from courses.models import Subject, Chapter

class SimplePlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='simple_plans')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date = models.DateField()
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'created_at']

    def __str__(self):
        return self.title

class LearningPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learning_plans')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class PlanItem(models.Model):
    learning_plan = models.ForeignKey(LearningPlan, on_delete=models.CASCADE, related_name='items')
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE)
    planned_date = models.DateField()
    is_completed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['planned_date']
        unique_together = ['learning_plan', 'chapter']

    def __str__(self):
        return f"{self.chapter.title} - {self.planned_date}"

class RevisionReminder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='revision_reminders')
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE)
    reminder_date = models.DateField()
    is_completed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['reminder_date']

    def __str__(self):
        return f"Revision for {self.chapter.title} on {self.reminder_date}"