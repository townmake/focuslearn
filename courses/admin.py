
from django.contrib import admin
from django.core.management import call_command
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import ReviewSet

def generate_daily_review(modeladmin, request, queryset):
    try:
        call_command('generate_daily_review')
        messages.success(request, "每日复习计划已生成")
    except Exception as e:
        messages.error(request, f"生成复习计划失败: {str(e)}")
    return HttpResponseRedirect(reverse('admin:courses_reviewset_changelist'))

generate_daily_review.short_description = "生成今日复习计划"

@admin.register(ReviewSet)
class ReviewSetAdmin(admin.ModelAdmin):
    actions = [generate_daily_review]
from mptt.admin import MPTTModelAdmin
from .models import KnowledgePoint

@admin.register(KnowledgePoint)
class KnowledgePointAdmin(MPTTModelAdmin):
    list_display = ('title', 'chapter', 'difficulty', 'memory_level', 'mastery_level')
    list_filter = ('chapter__subject', 'chapter')
    search_fields = ('title', 'description')
    mptt_level_indent = 20
    fieldsets = (
        (None, {
            'fields': ('chapter', 'title', 'parent', 'description', 'content')
        }),
        ('评估指标', {
            'fields': ('difficulty', 'memory_level', 'mastery_level')
        }),
        ('关联内容', {
            'fields': ('documents', 'videos', 'exercises'),
            'classes': ('collapse',)
        })
    )
    filter_horizontal = ('documents', 'videos', 'exercises')


from .models import SubjectCategory, Subject


@admin.register(SubjectCategory)
class SubjectCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_visible', 'display_weight')
    list_editable = ('is_visible', 'display_weight')
    list_display_links = ('name',)
    ordering = ('-display_weight', 'id')
    search_fields = ('name',)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'order', 'estimated_hours', 'progress')
    list_filter = ('category',)
    search_fields = ('name', 'description')
    autocomplete_fields = ('category',)
