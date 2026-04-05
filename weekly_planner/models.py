from django.core.validators import FileExtensionValidator
from django.db import models
from django.conf import settings
from django.utils import timezone
from courses.models import Subject, Chapter
from django.urls import reverse
from django.db.models import TextField


class TaskList(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default="#3498db")  # HEX color code
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = '任务列表'
        verbose_name_plural = '任务列表'

    def __str__(self):
        return f"{self.user.username} - {self.name}"

class Task(models.Model):
    REPEAT_CHOICES = [
        ('none', '不重复'),
        ('daily', '每天'),
        ('weekly', '每周'),
        ('monthly', '每月')
        ]   


    # 移除任务列表关联，改为直接关联用户
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    
    # 重复事件相关字段
    parent_series = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='child_events')
    #以下2字段暂时先不用了
    is_exception = models.BooleanField(default=False, help_text="标记是否为重复系列中的例外事件")
    original_date = models.DateTimeField(null=True, blank=True, help_text="例外事件的原始日期")
    
    # 添加科目和章节关联
    subject = models.ForeignKey('courses.Subject', related_name='tasks', on_delete=models.CASCADE, null=True)
    chapter = models.ForeignKey('courses.Chapter', related_name='tasks', on_delete=models.CASCADE, null=True)
    
    # 添加专注力和体力要求
    focus_level = models.IntegerField(default=50, help_text="专注力要求 (0-100)")
    energy_level = models.IntegerField(default=50, help_text="体力要求 (0-100)")
    
    title = models.CharField(max_length=200, default="未命名任务")
    description = models.TextField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    is_unscheduled = models.BooleanField(
        default=False,
        verbose_name="待安排",
        help_text="为 True 时不显示在周历上，仅在「待安排」列表中，确定时间后排入日历",
    )
    
    # 时间相关
    # 拆分日期和时间
    start_date = models.DateField(default=timezone.now)  # 只存储日期
    start_time = models.TimeField(default=timezone.now)  # 只存储时间
    end_date = models.DateField(default=timezone.now)    # 只存储日期
    end_time = models.TimeField(default=timezone.now)    # 只存储时间

    
    # 重复设置
    repeat_type = models.CharField(
        max_length=20,
        choices=REPEAT_CHOICES,
        default='none'
    )
    # 结束日期和重复日期配置，重复日期原先是设计可以选，现在这个字段也暂时不用了
    repeat_ends = models.DateField(null=True, blank=True)  # 从 DateTimeField 改为 DateField
    # repeat_days = models.JSONField(default=list, blank=True)  # 存储重复日期配置
    
    # 元数据
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_date', 'start_time','created_at']
        verbose_name = '任务'
        verbose_name_plural = '任务'

    def __str__(self):
        return self.title

    @property
    def start_datetime(self):
        """
        组合日期和时间的属性方法
        """
        return timezone.datetime.combine(self.start_date, self.start_time)
    
    @property
    def end_datetime(self):
        """
        组合日期和时间的属性方法
        """
        return timezone.datetime.combine(self.end_date, self.end_time)
    

    def save(self, *args, **kwargs):
        # 仅同一天内比较时刻；跨日时 end_time 可小于 start_time（如 23:00→次日 01:00）
        if self.start_date == self.end_date and self.end_time < self.start_time:
            self.end_time = self.start_time

        super().save(*args, **kwargs)
        

    @property
    def duration(self):
        """返回任务持续时间（分钟）"""
        return (self.end_datetime - self.start_datetime).total_seconds() / 60

class DailySummary(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        unique_together = ['user', 'date']
        verbose_name = '每日总结'
        verbose_name_plural = '每日总结'

    def __str__(self):
        return f"{self.user.username} - {self.date}"
    
class UserImportantDate(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank=True, default="")
    description = models.TextField(blank=True, default="")
    due_at = models.DateTimeField(null=True, blank=True, verbose_name="到期时间")
    planner_task = models.OneToOneField(
        "weekly_planner.Task",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="important_date_reminder",
        verbose_name="关联周历任务",
    )

    def __str__(self):
        return self.user.username


class ImportantDatesHomeSnapshot(models.Model):
    """首页「重要日期提醒」只读缓存（单行 JSON），避免每次打开首页关联查询 UserImportantDate。"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="important_dates_home_snapshot",
    )
    items = models.JSONField(default=list, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "首页重要日期快照"
        verbose_name_plural = "首页重要日期快照"
    
QUICK_ACCESS_LIBRARY_ICON_EXTENSIONS = ("png", "svg", "jpg", "jpeg", "gif", "webp")


class QuickAccessLibraryIcon(models.Model):
    """管理后台维护的速记可选图标（栅格图须为正方形；SVG 仅做基本格式检查）。"""

    name = models.CharField("名称", max_length=80, blank=True, default="")
    image = models.FileField(
        "图标",
        upload_to="quick_access_library_icons/",
        validators=[
            FileExtensionValidator(
                allowed_extensions=QUICK_ACCESS_LIBRARY_ICON_EXTENSIONS,
            )
        ],
        help_text="支持 PNG、SVG 等；栅格图须为正方形（宽高相等），SVG 建议视口为正方形。",
    )
    sort_order = models.PositiveIntegerField("排序", default=0, help_text="越小越靠前")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("sort_order", "id")
        verbose_name = "速记图标库"
        verbose_name_plural = "速记图标库"

    def __str__(self):
        return self.name or f"图标 #{self.pk}"


class QuickAccess(models.Model):
    title = models.CharField('标题', max_length=100)
    subtitle = models.CharField(
        '副标题',
        max_length=200,
        blank=True,
        default='',
        help_text='列表卡片上显示在标题下方的简短说明，可选',
    )
    icon = models.ImageField(
        '图标（已弃用）',
        upload_to='quick_access_icons/',
        blank=True,
        null=True,
        help_text='历史数据；新建请从图标库选择',
    )
    library_icon = models.ForeignKey(
        QuickAccessLibraryIcon,
        verbose_name="图标库图标",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="quick_access_items",
    )
    link = models.URLField('跳转链接')
    description = models.TextField(blank=True, verbose_name="描述")
    position = models.IntegerField('位置序号', default=0, help_text='数字越小排序越靠前')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '便捷记录'
        verbose_name_plural = '便捷记录'
        ordering = ['position', '-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('quick_access_detail', kwargs={'pk': self.pk})

    def get_icon_image_url(self):
        """列表/详情展示用：优先图标库，其次历史本地上传。"""
        if self.library_icon_id:
            lib = getattr(self, "library_icon", None)
            if lib and lib.image:
                return lib.image.url
        if self.icon:
            return self.icon.url
        return None

class Words(models.Model):
    word = models.CharField(max_length=30)
    translation = models.CharField(max_length=30)
    example_sentence = TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    level = models.IntegerField(default=1)  # 词汇等级，默认为1
    class Meta:
        ordering = ['-created_at']
        verbose_name = '单词'
        verbose_name_plural = '单词'
    def __str__(self):
        return self.word


class DailyQuotableQuote(models.Model):
    """
    每日三条备用名言（早/中/晚），数据来自 Quotable API。
    见 https://github.com/lukePeavey/quotable
    """

    class Slot(models.TextChoices):
        MORNING = "morning", "早"
        NOON = "noon", "中"
        EVENING = "evening", "晚"

    date = models.DateField("日期", db_index=True)
    slot = models.CharField("时段", max_length=10, choices=Slot.choices)
    content = models.TextField("正文")
    author = models.CharField("作者", max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "每日名言（Quotable）"
        verbose_name_plural = "每日名言（Quotable）"
        constraints = [
            models.UniqueConstraint(fields=["date", "slot"], name="uniq_daily_quotable_date_slot"),
        ]

    def __str__(self):
        return f"{self.date} {self.get_slot_display()} — {self.author}"


class LocalFamousQuote(models.Model):
    """首页欢迎区随机展示的名人名言，由管理员在后台维护。"""

    content = models.TextField("正文")
    author = models.CharField(
        "作者",
        max_length=200,
        blank=True,
        default="",
        help_text="留空时首页显示为「佚名」。批量录入可设默认作者，或单行用「正文|作者」。",
    )
    is_active = models.BooleanField("参与首页随机", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "本地名人名言"
        verbose_name_plural = "本地名人名言"
        ordering = ("-created_at",)

    def __str__(self):
        text = (self.content or "").strip().replace("\n", " ")
        return (text[:50] + "…") if len(text) > 50 else text or "(空)"


class DeepSeekProviderSettings(models.Model):
    """单例配置：管理后台仅保留一条，供全站调用 DeepSeek。"""

    api_key = models.CharField(
        "API Key",
        max_length=512,
        blank=True,
        help_text="DeepSeek 控制台创建的 API Key",
    )
    api_base = models.URLField(
        "API 基础地址",
        max_length=200,
        default="https://api.deepseek.com",
        help_text="一般无需修改",
    )
    default_model = models.CharField(
        "默认模型",
        max_length=100,
        default="deepseek-chat",
    )
    request_timeout = models.PositiveIntegerField(
        "请求超时（秒）",
        default=120,
        help_text="周总结等长文本可适当增大",
    )
    is_enabled = models.BooleanField("启用 DeepSeek 调用", default=True)

    class Meta:
        verbose_name = "DeepSeek API 配置"
        verbose_name_plural = "DeepSeek API 配置"

    def __str__(self):
        return "DeepSeek API 配置"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class WeeklyAiSummary(models.Model):
    """周智能总结（首页全项目 / 单项目），由 DeepSeek 根据周计划与学习记录生成。"""

    SCOPE_HOME = "home"
    SCOPE_SUBJECT_PREFIX = "subject:"

    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "待处理"),
        (STATUS_PROCESSING, "生成中"),
        (STATUS_COMPLETED, "已完成"),
        (STATUS_FAILED, "失败"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="weekly_ai_summaries",
        verbose_name="用户",
    )
    scope_key = models.CharField(
        "范围键",
        max_length=80,
        db_index=True,
        help_text="home=全项目；subject:<项目id>=单项目",
    )
    week_start_date = models.DateField("周起始（周一）", db_index=True)
    week_end_date = models.DateField("周结束（周日）")
    title = models.CharField("标题", max_length=300, blank=True, default="")
    overview = models.CharField(
        "概述",
        max_length=200,
        blank=True,
        default="",
        help_text="不超过约 50 字的短概述",
    )
    body = models.TextField("详细", blank=True, default="", help_text="AI 生成的周总结正文")
    status = models.CharField(
        "状态",
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )
    error_message = models.TextField("错误信息", blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "周智能总结"
        verbose_name_plural = "周智能总结"
        ordering = ("-week_start_date", "-created_at")
        constraints = [
            models.UniqueConstraint(
                fields=["user", "scope_key", "week_start_date"],
                name="uniq_weekly_ai_summary_user_scope_week",
            )
        ]

    def __str__(self):
        return f"{self.title or self.scope_key} ({self.week_start_date})"

    @staticmethod
    def scope_key_for_subject(subject_id: int) -> str:
        return f"{WeeklyAiSummary.SCOPE_SUBJECT_PREFIX}{int(subject_id)}"
