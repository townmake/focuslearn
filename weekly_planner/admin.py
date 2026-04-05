from pathlib import Path

from django import forms
from django.contrib import admin, messages
from django.db.models import Max
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from .models import (
    DailyQuotableQuote,
    DeepSeekProviderSettings,
    LocalFamousQuote,
    QUICK_ACCESS_LIBRARY_ICON_EXTENSIONS,
    QuickAccessLibraryIcon,
    Task,
    TaskList,
    WeeklyAiSummary,
)

_LIBRARY_ICON_EXT_SET = frozenset(QUICK_ACCESS_LIBRARY_ICON_EXTENSIONS)


def validate_quick_access_library_icon_file(uploaded_file):
    """校验速记图标库上传文件。通过返回 None，否则返回错误文案（短句）。"""
    name = getattr(uploaded_file, "name", "") or ""
    ext = Path(name).suffix.lower().lstrip(".")
    if ext not in _LIBRARY_ICON_EXT_SET:
        return "不支持的文件格式"

    uploaded_file.seek(0)
    if ext == "svg":
        head = uploaded_file.read(500)
        uploaded_file.seek(0)
        if b"<svg" not in head.lower():
            return "无效的 SVG 文件"
        return None

    try:
        from PIL import Image
    except ImportError:
        return None
    img = Image.open(uploaded_file)
    w, h = img.size
    if w != h:
        return "图标须为正方形（宽度与高度相等）"
    uploaded_file.seek(0)
    return None


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
        err = validate_quick_access_library_icon_file(f)
        if err:
            raise forms.ValidationError(err)
        return f


@admin.register(QuickAccessLibraryIcon)
class QuickAccessLibraryIconAdmin(admin.ModelAdmin):
    form = QuickAccessLibraryIconAdminForm
    change_list_template = "admin/weekly_planner/quickaccesslibraryicon/change_list.html"
    list_display = ("id", "name", "sort_order", "preview", "created_at")
    list_editable = ("sort_order",)
    ordering = ("sort_order", "id")

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        extra = [
            path(
                "bulk-upload/",
                self.admin_site.admin_view(self.bulk_upload_view),
                name="%s_%s_bulk_upload" % info,
            ),
        ]
        return extra + super().get_urls()

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["bulk_upload_url"] = reverse(
            "admin:%s_%s_bulk_upload" % (self.model._meta.app_label, self.model._meta.model_name)
        )
        return super().changelist_view(request, extra_context=extra_context)

    def bulk_upload_view(self, request):
        if not self.has_add_permission(request):
            messages.error(request, "无添加权限。")
            return redirect("admin:index")

        if request.method == "POST":
            files = request.FILES.getlist("icons_folder") + request.FILES.getlist("icons_files")
            if not files:
                messages.warning(request, "未选择任何文件。")
                return redirect(request.path)

            max_so = QuickAccessLibraryIcon.objects.aggregate(m=Max("sort_order"))["m"]
            next_order = max_so or 0
            created_names = []
            skipped = []

            for uf in files:
                base = Path((uf.name or "")).name
                if not base or base.startswith("."):
                    continue
                if base.lower() in ("thumbs.db", "desktop.ini"):
                    continue
                ext = Path(base).suffix.lower().lstrip(".")
                if ext not in _LIBRARY_ICON_EXT_SET:
                    skipped.append("%s：跳过（不支持格式）" % base)
                    continue

                err = validate_quick_access_library_icon_file(uf)
                if err:
                    skipped.append("%s：%s" % (base, err))
                    continue

                display_name = (Path(base).stem or base)[:80]
                next_order += 1
                obj = QuickAccessLibraryIcon(name=display_name, sort_order=next_order)
                try:
                    obj.image.save(base, uf, save=True)
                except Exception as exc:
                    next_order -= 1
                    skipped.append("%s：保存失败（%s）" % (base, exc))

                else:
                    created_names.append(base)

            n = len(created_names)
            if n:
                self.message_user(
                    request,
                    "已成功添加 %s 个图标。" % n,
                    level=messages.SUCCESS,
                )
            if skipped:
                tail = skipped[:30]
                more = "" if len(skipped) <= 30 else " … 另有 %s 条未显示" % (len(skipped) - 30)
                self.message_user(
                    request,
                    "部分文件未导入：%s%s" % ("；".join(tail), more),
                    level=messages.WARNING,
                )
            if not n and not skipped:
                messages.info(request, "没有符合要求的图标文件。")

            return redirect(
                "admin:%s_%s_changelist"
                % (self.model._meta.app_label, self.model._meta.model_name)
            )

        context = {
            **self.admin_site.each_context(request),
            "title": "批量上传图标",
            "opts": self.model._meta,
        }
        return TemplateResponse(
            request,
            "admin/weekly_planner/quickaccesslibraryicon/bulk_upload.html",
            context,
        )

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

