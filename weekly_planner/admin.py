from django import forms
from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils.html import format_html

from .models import (
    DailyQuotableQuote,
    DeepSeekProviderSettings,
    LocalFamousQuote,
    QuickAccessLibraryIcon,
    Task,
    TaskList,
    WeeklyAiSummary,
)


class QuickAccessLibraryIconAdminForm(forms.ModelForm):
    class Meta:
        model = QuickAccessLibraryIcon
        fields = "__all__"

    def clean_image(self):
        f = self.cleaned_data.get("image")
        if not f:
            if self.instance.pk and self.instance.image:
                return self.instance.image
            raise forms.ValidationError("请上传图片")
        try:
            from PIL import Image
        except ImportError:
            return f
        img = Image.open(f)
        w, h = img.size
        if w != h or w not in (32, 64):
            raise forms.ValidationError("图标须为 32×32 或 64×64 像素的正方形")
        f.seek(0)
        return f


@admin.register(QuickAccessLibraryIcon)
class QuickAccessLibraryIconAdmin(admin.ModelAdmin):
    form = QuickAccessLibraryIconAdminForm
    list_display = ("id", "name", "sort_order", "preview", "created_at")
    list_editable = ("sort_order",)
    ordering = ("sort_order", "id")

    @admin.display(description="预览")
    def preview(self, obj):
        if not obj.image:
            return "—"
        return format_html(
            '<img src="{}" width="32" height="32" style="object-fit:contain;vertical-align:middle;border:1px solid #eee;border-radius:4px;" alt="" />',
            obj.image.url,
        )


@admin.register(DeepSeekProviderSettings)
class DeepSeekProviderSettingsAdmin(admin.ModelAdmin):
    list_display = ("__str__", "is_enabled", "default_model", "request_timeout")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "is_enabled",
                    "api_key",
                    "api_base",
                    "default_model",
                    "request_timeout",
                )
            },
        ),
    )

    def has_add_permission(self, request):
        return not DeepSeekProviderSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(WeeklyAiSummary)
class WeeklyAiSummaryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "scope_key",
        "week_start_date",
        "status",
        "title",
        "created_at",
    )
    list_filter = ("status", "scope_key")
    search_fields = ("title", "overview", "user__username")
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ("user",)


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


@admin.register(LocalFamousQuote)
class LocalFamousQuoteAdmin(admin.ModelAdmin):
    list_display = ("content_preview", "author", "is_active", "created_at")
    list_display_links = ("content_preview",)
    list_editable = ("is_active",)
    list_filter = ("is_active",)
    search_fields = ("content", "author")
    readonly_fields = ("created_at", "updated_at")
    change_list_template = "admin/weekly_planner/localfamousquote/change_list.html"

    fieldsets = (
        (None, {"fields": ("content", "author", "is_active")}),
        ("时间", {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="正文摘要")
    def content_preview(self, obj):
        t = (obj.content or "").replace("\n", " ")[:80]
        return t + ("…" if len(obj.content or "") > 80 else "")

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        custom = [
            path(
                "bulk-add/",
                self.admin_site.admin_view(self.bulk_add_view),
                name="%s_%s_bulk_add" % info,
            ),
        ]
        return custom + super().get_urls()

    def bulk_add_view(self, request):
        if not self.has_add_permission(request):
            messages.error(request, "无添加权限。")
            return redirect("admin:index")
        if request.method != "POST":
            return redirect(
                "admin:%s_%s_changelist"
                % (self.model._meta.app_label, self.model._meta.model_name)
            )
        raw = request.POST.get("bulk_lines", "")
        default_author = (request.POST.get("default_author") or "").strip()
        to_create = []
        for raw_line in raw.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            content = line
            author = default_author
            if "|" in line:
                left, right = line.split("|", 1)
                left, right = left.strip(), right.strip()
                if not left:
                    continue
                content = left
                author = right if right else default_author
            author_final = (author or "").strip() or "佚名"
            content = content.strip()
            if not content:
                continue
            if len(content) > 8000:
                content = content[:8000]
            to_create.append(
                LocalFamousQuote(
                    content=content,
                    author=author_final[:200],
                )
            )
        created = len(to_create)
        if created:
            LocalFamousQuote.objects.bulk_create(to_create, batch_size=500)
        self.message_user(
            request,
            "已添加 %s 条名人名言。" % created,
            level=messages.SUCCESS,
        )
        return redirect(
            "admin:%s_%s_changelist"
            % (self.model._meta.app_label, self.model._meta.model_name)
        )

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        info = self.model._meta.app_label, self.model._meta.model_name
        extra_context["bulk_add_url"] = reverse("admin:%s_%s_bulk_add" % info)
        return super().changelist_view(request, extra_context=extra_context)

