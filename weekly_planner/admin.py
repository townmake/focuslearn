from django.contrib import admin
from .models import TaskList, Task, DailyQuotableQuote
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


@admin.register(DailyQuotableQuote)
class DailyQuotableQuoteAdmin(admin.ModelAdmin):
    list_display = ("date", "slot", "author", "content_preview", "created_at")
    list_filter = ("date", "slot")
    search_fields = ("content", "author")
    ordering = ("-date", "slot")

    @admin.display(description="摘要")
    def content_preview(self, obj):
        t = (obj.content or "")[:60]
        return t + ("…" if len(obj.content or "") > 60 else "")


# Subject和Chapter已经在courses应用中注册，这里不再重复注册