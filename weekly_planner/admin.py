from django.contrib import admin
from .models import TaskList, Task
# 导入courses中的模型，如果需要在这里引用
from courses.models import Subject, Chapter


@admin.register(TaskList)
class TaskListAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created_at')
    list_filter = ('user',)
    search_fields = ('name',)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'subject', 'chapter', 'is_completed', 'start_datetime', 'focus_level', 'energy_level')
    list_filter = ('is_completed', 'user', 'subject')
    search_fields = ('title', 'description')

# Subject和Chapter已经在courses应用中注册，这里不再重复注册