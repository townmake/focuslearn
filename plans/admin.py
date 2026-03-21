from django.contrib import admin
from .models import SimplePlan, LearningPlan, PlanItem, RevisionReminder

@admin.register(SimplePlan)
class SimplePlanAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'date', 'is_completed', 'created_at')
    list_filter = ('is_completed', 'date')
    search_fields = ('title', 'description', 'user__username')
    ordering = ('date', 'created_at')

@admin.register(LearningPlan)
class LearningPlanAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'subject', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active', 'subject')
    search_fields = ('title', 'description', 'user__username')
    ordering = ('start_date', 'end_date')

@admin.register(PlanItem)
class PlanItemAdmin(admin.ModelAdmin):
    list_display = ('chapter', 'learning_plan', 'planned_date', 'is_completed')
    list_filter = ('is_completed', 'planned_date', 'learning_plan__subject')
    search_fields = ('chapter__title', 'learning_plan__title', 'notes')
    ordering = ('planned_date',)

@admin.register(RevisionReminder)
class RevisionReminderAdmin(admin.ModelAdmin):
    list_display = ('chapter', 'user', 'reminder_date', 'is_completed')
    list_filter = ('is_completed', 'reminder_date')
    search_fields = ('chapter__title', 'user__username', 'notes')
    ordering = ('reminder_date',)