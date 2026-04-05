
from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from .models import KnowledgePoint, SubjectCategory, Subject


@admin.register(KnowledgePoint)
class KnowledgePointAdmin(MPTTModelAdmin):
    list_display = ('title', 'chapter')
    list_filter = ('chapter__subject', 'chapter')
    search_fields = ('title', 'description')
    mptt_level_indent = 20
    fieldsets = (
        (None, {
            'fields': ('chapter', 'title', 'parent', 'description', 'content')
        }),
        ('关联内容', {
            'fields': ('documents', 'videos'),
            'classes': ('collapse',)
        })
    )
    filter_horizontal = ('documents', 'videos')


@admin.register(SubjectCategory)
class SubjectCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_visible', 'display_weight')
    list_editable = ('is_visible', 'display_weight')
    list_display_links = ('name',)
    ordering = ('-display_weight', 'id')
    search_fields = ('name',)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'order', 'estimated_hours', 'already_hours', 'progress')
    list_filter = ('category',)
    search_fields = ('name', 'description')
    autocomplete_fields = ('category',)
