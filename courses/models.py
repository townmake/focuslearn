from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import TextField
from mptt.models import MPTTModel, TreeForeignKey
from django_extensions.db.models import TimeStampedModel
from django.core.files import File
from urllib.parse import urlparse
import os
import logging

logger = logging.getLogger(__name__)

# 修改所有用户外键字段
user = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE
)

class DictionaryLookupRecord(models.Model):
    """
    词典查询记录模型
    """
    query_text = models.CharField(max_length=255, verbose_name="查询文本",unique=True)
    src_text = models.TextField(verbose_name="源文本")
    dst_text = models.TextField(verbose_name="目标文本")
    # 保留原始URL用于调试
    src_tts_url = models.URLField(verbose_name="源语音URL", null=True, blank=True)
    dst_tts_url = models.URLField(verbose_name="目标语音URL", null=True, blank=True)
    
    # 本地存储字段
    src_audio = models.FileField(upload_to='tts/en/', verbose_name="源语音文件", null=True, blank=True)
    dst_audio = models.FileField(upload_to='tts/zh/', verbose_name="目标语音文件", null=True, blank=True)

    dict_data = models.JSONField(verbose_name="词典数据", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "词典查询记录"
        verbose_name_plural = "词典查询记录"

    def get_filename(self, url):
        """从URL提取安全文件名"""
        path = urlparse(url).path
        return os.path.basename(path).split('?')[0] or 'audio.mp3'

    def save_audio(self, url, field_name):
        """保存音频文件到指定字段"""
        if not url or getattr(self, field_name):
            return

        try:
            from django.core.files.base import ContentFile
            import requests
            from requests.exceptions import RequestException
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            filename = self.get_filename(url)
            content = ContentFile(response.content)
            
            # 保存到对应字段
            getattr(self, field_name).save(filename, content, save=False)
            
        except RequestException as e:
            logger.error(f"下载音频失败: {url} - {str(e)}")
        except Exception as e:
            logger.error(f"保存音频异常: {str(e)}")


class SubjectCategory(models.Model):
    """科目分类（后台可配置名称、是否在前台列表展示、展示顺序权重）"""

    name = models.CharField(max_length=100, verbose_name="科目分类名称")
    is_visible = models.BooleanField(default=True, verbose_name="是否显示")
    display_weight = models.IntegerField(
        default=0,
        verbose_name="显示权重",
        help_text="数值越大，在项目列表中越靠前展示",
    )

    class Meta:
        verbose_name = "科目分类"
        verbose_name_plural = "科目分类"
        ordering = ["-display_weight", "id"]

    def __str__(self):
        return self.name


class Subject(models.Model):
    category = models.ForeignKey(
        SubjectCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subjects",
        verbose_name="科目分类",
    )
    name = models.CharField(max_length=100, verbose_name="科目名称")
    description = models.TextField(blank=True, verbose_name="科目描述")
    estimated_hours = models.PositiveIntegerField(default=0,verbose_name="预计学时(小时)")
    order = models.PositiveIntegerField(default=0, verbose_name="排序序号")
    actual_study_hours = models.PositiveIntegerField(default=0, verbose_name="实际学时(小时)")
    already_hours = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="累计已投时长(小时)",
    )
    progress = models.PositiveIntegerField( default=0,  verbose_name="学习进度(%)", help_text="学习进度，0-100之间" )
    background_image = models.ImageField(
        upload_to='subject_bg/', 
        blank=True, 
        null=True, 
        verbose_name="背景图片"
    )
    color = models.CharField(
        max_length=20, 
        default='#4a6bdf', 
        verbose_name="主题颜色"
    )
    heat = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="项目热度",
        help_text="0–10，用于日历/记录里项目下拉排序；创建周历任务时会自动调整",
        validators=[MinValueValidator(0), MaxValueValidator(10)],
    )

    class OpenStatus(models.TextChoices):
        OPEN = "open", "开启"
        CLOSED = "closed", "关闭"

    open_status = models.CharField(
        max_length=16,
        choices=OpenStatus.choices,
        default=OpenStatus.OPEN,
        db_index=True,
        verbose_name="项目状态",
        help_text="关闭后的项目不出现在主列表与日历/记录选项目下拉中",
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="创建时间"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="更新时间"
    )

    
    # 统计字段
    Chapters_count = models.PositiveIntegerField(default=0, verbose_name="章节总数")
    knowledge_points_count = models.PositiveIntegerField(default=0, verbose_name="知识点总数")
    documents_count = models.PositiveIntegerField(default=0, verbose_name="文档总数")
    videos_count = models.PositiveIntegerField(default=0, verbose_name="视频总数")
    comments_count = models.PositiveIntegerField(default=0, verbose_name="评论总数")
    total_video_duration = models.PositiveIntegerField(default=0, verbose_name="视频总时长(分钟)")
    hist_stats_rolled_week_start = models.DateField(
        null=True,
        blank=True,
        verbose_name="历史统计已累加周起始",
        help_text="最近一次把本周统计写入各任务历史字段时的周一日期；同周重复插入总结不会重复累加",
    )
    
    class Meta:
        verbose_name = "科目"
        verbose_name_plural = "科目"
        ordering = ['-heat', 'order', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # 仅保存基础字段，统计字段由信号处理器更新
        super().save(*args, **kwargs)


class SubjectHeatTracker(models.Model):
    """单例：创建周历任务次数计数，满 10 次后全体项目热度 -1。"""

    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    creations_since_decay = models.PositiveIntegerField(
        default=0,
        verbose_name="距上次衰减的创建次数",
    )

    class Meta:
        verbose_name = "项目热度计数器"
        verbose_name_plural = "项目热度计数器"

    def __str__(self):
        return f"热度计数 {self.creations_since_decay}/10"


class Chapter(models.Model):
    subject = models.ForeignKey(
        Subject, 
        on_delete=models.CASCADE, 
        verbose_name="所属科目",
        related_name='chapters'
    )
    title = models.CharField(max_length=100, verbose_name="章节标题")
    description = models.TextField(blank=True, verbose_name="章节描述")
    order = models.PositiveIntegerField(default=0, verbose_name="排序序号")
    # 关联的知识点、文档、视频和评论
    knowledge_points = models.ManyToManyField('KnowledgePoint', related_name='chapter_related_points')
    documents = models.ManyToManyField('Document', related_name='chapter_documents')
    videos = models.ManyToManyField('Video', related_name='chapter_videos')
    comments = models.ManyToManyField('Comment', related_name='chapter_comments')
    estimated_hours = models.PositiveIntegerField(
        default=1, 
        verbose_name="预计学时(小时)"
    )
    actual_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="实际学时(小时)"
    )
    progress = models.PositiveIntegerField(
        default=0, 
        verbose_name="学习进度(%)"
    )

    class ProgressStatus(models.TextChoices):
        IN_PROGRESS = "进行中", "进行中"
        FOCUS = "攻坚", "攻坚"
        WRAP_UP = "收尾", "收尾"
        ON_HOLD = "挂起", "挂起"
        DONE = "完成", "完成"

    progress_status = models.CharField(
        _("进度状态"),
        max_length=20,
        choices=ProgressStatus.choices,
        default=ProgressStatus.IN_PROGRESS,
    )

    #统计字段
    knowledge_points_count = models.PositiveIntegerField(default=0)
    documents_count = models.PositiveIntegerField(default=0)
    videos_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)

    # 安排与回顾：写入「总结」时把当周统计累加进历史（避免每次扫全量历史）
    hist_plan_task_count = models.PositiveIntegerField(
        default=0,
        verbose_name="历史子任务数量",
        help_text="各周写入总结时累加的计划子任务数",
    )
    hist_planned_hours = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="历史计划投入时长(小时)",
    )
    hist_actual_hours = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="历史已投入时长(小时)",
    )
    # 最近一次写入总结时「本周贡献」快照，同周再次写入时用最新值替换而非跳过
    last_roll_week_start = models.DateField(
        null=True,
        blank=True,
        verbose_name="最近累加的周起始",
    )
    last_roll_plan_task_count = models.PositiveIntegerField(
        default=0,
        verbose_name="最近一周累加的子任务数",
    )
    last_roll_planned_hours = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="最近一周累加的计划时长",
    )
    last_roll_actual_hours = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="最近一周累加的已投入时长",
    )
    
    def save(self, *args, **kwargs):
        # 仅保存基础数据，统计字段由信号处理器更新
        super().save(*args, **kwargs)

    @property
    def chapter_video_duration(self):
        total_seconds = sum(v.duration for v in self.videos.all())
        return round(total_seconds / 60, 1) 
    

    class Meta:
        verbose_name = "章节"
        verbose_name_plural = "章节"
        ordering = ['subject', 'order']
    
    def __str__(self):
        return f"{self.subject.name} - {self.title}"


class KnowledgePoint(MPTTModel):
    """知识点模型"""
    lft = models.PositiveIntegerField(default=1)
    rght = models.PositiveIntegerField(default=2)
    tree_id = models.PositiveIntegerField(default=1)
    level = models.PositiveIntegerField(default=0)
    brother_id =models.PositiveIntegerField(default=1,null=False,help_text='兄弟ID')
    created = models.DateTimeField(
        _('创建时间'),
        default=timezone.datetime(1970,1,1)
    )
    modified = models.DateTimeField(
        _('修改时间'),
        default=timezone.datetime(1970,1,1)
    )

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = timezone.now()
        self.modified = timezone.now()
        super().save(*args, **kwargs)
    chapter = models.ForeignKey(
        Chapter,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='chapter_knowledge_points',
        verbose_name=_('所属章节')
    )
    title = models.CharField(_('标题'), max_length=255)
    description = models.TextField(_('描述'), blank=True)
    content = TextField(_('详细内容'), blank=True)
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_('上级知识点')
    )
    
    # 关联内容-后面再考虑如何关联起来
    documents = models.ManyToManyField(
        'Document',
        related_name='knowledge_points',
        blank=True,
        verbose_name=_('关联文档')
    )
    videos = models.ManyToManyField(
        'Video',
        related_name='knowledge_points',
        blank=True,
        verbose_name=_('关联视频')
    )
    class Meta:
        verbose_name = _('知识点')
        verbose_name_plural = _('知识点')
        ordering = ['tree_id', 'lft']
    
    class MPTTMeta:
        order_insertion_by = ['title']
    
    def __str__(self):
        return f"{self.title} ({self.chapter.title})"
    
    def get_absolute_url(self):
        return reverse('courses:knowledge_point_detail', kwargs={'pk': self.pk})

class KnowledgePointAnnotation(models.Model):
    """知识点内容注释模型"""
    knowledge_point = models.ForeignKey(
        KnowledgePoint,
        on_delete=models.CASCADE,
        related_name='annotations',
        verbose_name=_('关联知识点')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_('用户')
    )
    quote = models.TextField(_('引用内容'),null=False)
    content = models.TextField(_('注释内容'),blank=False,null=False)
    created_at = models.DateTimeField(
        _('创建时间'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('更新时间'),
        auto_now=True
    )
    content_tag = models.PositiveIntegerField(
        _('内容标签'),
        help_text=_('注释关联的内容在知识点详细内容中的标签')
    )
    content_length = models.PositiveIntegerField(
        _('内容长度'),
        default=0,
        help_text=_('注释关联的内容长度(字符数)')
    )

    class Meta:
        verbose_name = _('知识点注释')
        verbose_name_plural = _('知识点注释')
        ordering = ['created_at']
        unique_together = ('knowledge_point', 'content_tag')
    
    def __str__(self):
        return f"{self.knowledge_point.title} - {self.content[:20]}"

class Document(models.Model):
    chapter = models.ForeignKey(
        Chapter, 
        null=True,
        blank=True,
        on_delete=models.CASCADE, 
        verbose_name="所属章节"
    )
    title = models.CharField(
        max_length=100, 
        default='未命名文档',
        verbose_name="文档标题"
    )
    file = models.FileField(upload_to='documents/', verbose_name="文档文件")
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间"
    )
    
    class Meta:
        verbose_name = "文档"
        verbose_name_plural = "文档"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

class Video(models.Model):
    chapter = models.ForeignKey(
        Chapter, 
        null=True,
        blank=True,
        on_delete=models.CASCADE, 
        verbose_name="所属章节"
    )
    title = models.CharField(
        max_length=100, 
        default='未命名视频',
        verbose_name="视频标题"
    )
    url = models.URLField(
        default='https://example.com/video',
        verbose_name="视频链接"
    )
    duration = models.PositiveIntegerField(verbose_name="视频时长(秒)")
    description =TextField(_('视频描述'), blank=True,null=True)
    comments = models.ManyToManyField(
        'Comment',
        through='VideoComment',
        related_name='video_comments',
        verbose_name="视频评论"
    )
    
    class Meta:
        verbose_name = "视频"
        verbose_name_plural = "视频"
    
    def __str__(self):
        return self.title

class VideoComment(models.Model):
    """视频评论中间模型"""
    video = models.ForeignKey(
        Video,
        on_delete=models.CASCADE,
        related_name='video_comment_relations',
        verbose_name="关联视频"
    )
    comment = models.ForeignKey(
        'Comment',
        on_delete=models.CASCADE,
        related_name='comment_video_relations',
        verbose_name="关联评论"
    )
    timestamp = models.PositiveIntegerField(
        default=0,
        verbose_name="视频时间戳(秒)",
        help_text="评论对应的视频时间点(秒)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="更新时间"
    )
    is_pinned = models.BooleanField(
        default=False,
        verbose_name="是否置顶"
    )
    likes_count = models.PositiveIntegerField(
        default=0,
        verbose_name="点赞数"
    )

    class Meta:
        verbose_name = "视频评论"
        verbose_name_plural = "视频评论"
        ordering = ['-is_pinned', '-created_at']
        unique_together = ('video', 'comment')

    def __str__(self):
        return f"{self.video.title} - {self.comment.content[:20]}"

    def save(self, *args, **kwargs):
        # 自动更新关联视频的评论数
        if not self.pk:  # 新建记录时
            self.video.comments_count = VideoComment.objects.filter(video=self.video).count()
            self.video.save()
        super().save(*args, **kwargs)    


        
class MethodSummary(models.Model):
    name = models.CharField(max_length=255, verbose_name="方法名称")
    description = TextField(_('方法描述'), blank=True)
    note= models.TextField(verbose_name="备注", blank=True)
    knowledgePoint = models.ManyToManyField(KnowledgePoint, verbose_name="关联知识点")
    chapter = models.ForeignKey(
        Chapter,
        on_delete=models.CASCADE,
        related_name='method_summaries',
        verbose_name="所属章节",
        null=True,
        blank=True
    )
    chapter_title = models.CharField(
        max_length=100,
        verbose_name="章节标题",
        null=True,
        blank=True,
        help_text="如果章节已删除或不存在，则此字段用于显示章节标题"
    )
    difficulty_level = models.PositiveSmallIntegerField(
        _('难度'),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=3
    )
    important_level = models.PositiveSmallIntegerField(
        _('重要度'),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=3
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "方法总结"
        verbose_name_plural = "方法总结"

    def __str__(self):
        return self.name

class Comment(models.Model):
    chapter = models.ForeignKey(
        Chapter, 
        on_delete=models.CASCADE, 
        null=True,
        blank=True,
        verbose_name="所属章节"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, 
        verbose_name="用户"
    )
    title = models.TextField(
        verbose_name="评论标题",
        max_length=100,
        default="未命名评论",
        )
    content = TextField(_('评论内容'), blank=True, null=True)

    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="创建时间"
    )

    type = models.CharField(
        max_length=20, 
        choices=[
            ('videos', '视频评论'),
            ('documents', '文档评论'),
            ('knowledge_points', '知识点评论'),
            ('chapter', '章节评论'),
            ('smart-review', '复习任务评论'),
            ('other', '其他'),
        ],
        default='other',
        verbose_name="评论类型"
    )
    type_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="评论对象ID"
    )
    position = models.TimeField(
        blank=True,
        null=True,
        help_text="视频中的时间位置",
        verbose_name="评论位置"
    )

    updated_at = models.DateTimeField(
        auto_now=True, 
        blank=True,
        null=True,
        verbose_name="更新时间"
    )
    
    parentid = models.PositiveIntegerField(
        null=True,
        blank=True,
        default=0,
        verbose_name="父评论ID"
    )
    is_pinned = models.BooleanField(
        default=False,
        verbose_name="是否置顶"
    )
    likes_count = models.PositiveIntegerField(
        default=0,
        verbose_name="点赞数"
    )

    class Meta:
        verbose_name = "评论"
        verbose_name_plural = "评论"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.content[:20]}"

class StudyRecord(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, 
        verbose_name="用户"
    )
    created_date = models.DateField(
        default=timezone.now, 
        verbose_name="记录日期"
    )
    start_time = models.DateTimeField(verbose_name="开始时间")
    end_time = models.DateTimeField(verbose_name="结束时间")
    duration = models.PositiveIntegerField(verbose_name="学习时长(秒)")
    
    PAGE_TYPE_CHOICES = [
        ('research', '调研'),
        ('thinking', '思考'),
        ('communication', '沟通'),
        ('implementation', '实施'),
        ('retrospective', '复盘'),
        ('process_step', '流程步骤'),
        ('other', '其他'),
    ]
    page_type = models.CharField(
        max_length=20,
        choices=PAGE_TYPE_CHOICES,
        verbose_name="任务类型"
    )
    chapter = models.ForeignKey(
        Chapter, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        verbose_name="关联章节"
    )
    subject_name = models.CharField(
        max_length=100, 
        verbose_name="科目名称"
    )
    chapter_name = models.CharField(
        max_length=100, 
        verbose_name="章节名称"
    )
    learning_content = models.TextField(verbose_name="学习内容")
    description = models.TextField(blank=True, verbose_name="学习描述")

    class Source(models.TextChoices):
        PLAN = "plan", "计划执行"
        MANUAL = "manual", "手动插入"

    source = models.CharField(
        max_length=16,
        choices=Source.choices,
        default=Source.MANUAL,
        verbose_name="来源",
        db_index=True,
        help_text="plan=周历计划完成/记录产生；manual=学习记录页手动插入（日历上显示红点）",
    )
    
    class Meta:
        verbose_name = "记录"
        verbose_name_plural = "记录"
        ordering = ['-start_time']
    
    def __str__(self):
        return f"{self.user.username} - {self.subject_name} - {timezone.localtime(self.start_time).strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def duration_display(self):
        hours = self.duration // 3600
        minutes = (self.duration % 3600) // 60
        seconds = self.duration % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


class SubjectPlanSummary(models.Model):
    """项目安排与回顾：总结（富文本正文 + 标题/概述）。"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subject_plan_summaries",
        verbose_name="用户",
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="plan_summaries",
        verbose_name="项目",
    )
    title = models.CharField(max_length=200, verbose_name="标题")
    overview = models.TextField(blank=True, verbose_name="概述")
    body = models.TextField(blank=True, verbose_name="正文", help_text="AiEditor 等保存的 HTML")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "项目总结"
        verbose_name_plural = "项目总结"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.subject_id})"


# 添加在所有模型定义之后

    # @receiver([post_save, post_delete], sender=KnowledgePoint)
    # @receiver([post_save, post_delete], sender=Document)
    # @receiver([post_save, post_delete], sender=Video)
    # @receiver([post_save, post_delete], sender=Comment)
    # @receiver([post_save, post_delete], sender=Exercise)
    # def update_chapter_stats(sender, instance, **kwargs):
    #     """
    #     当关联对象变更时自动更新Chapter统计字段
    #     """
    #     if hasattr(instance, 'chapter'):  # 处理ForeignKey关系
    #         chapter = instance.chapter
    #         # 更新知识点统计
    #         if isinstance(instance, KnowledgePoint):
    #             chapter.knowledge_points_count = chapter.knowledge_points.count()
    #         # 更新文档统计
    #         elif isinstance(instance, Document):
    #             chapter.documents_count = chapter.documents.count()
    #         # 更新视频统计
    #         elif isinstance(instance, Video):
    #             chapter.videos_count = chapter.videos.count()
    #             chapter.save()  # 会触发chapter_video_duration计算
    #         # 更新评论统计
    #         elif isinstance(instance, Comment):
    #             chapter.comments_count = chapter.comments.count()
    #         # 更新习题统计
    #         elif isinstance(instance, Exercise):
    #             chapter.exercises_count = chapter.exercises.count()
    #         chapter.save()
    #     elif hasattr(instance, 'chapters'):  # 处理ManyToMany关系
    #         for chapter in instance.chapters.all():
    #             chapter.save()

    @receiver(post_save, sender='courses.StudyRecord')
    def update_chapter_study_hours(sender, instance, created, **kwargs):
        """
        当记录保存时更新章节的实际学习时长
        """
        if created and instance.chapter:  # 只处理新建记录且有关联章节的情况
            from decimal import Decimal
            # 将秒转换为小时并保留2位小数
            hours = Decimal(instance.duration) / Decimal(3600)
            hours = hours.quantize(Decimal('0.00'))  # 四舍五入到2位小数
            
            # 更新章节的实际学习时长
            chapter = instance.chapter
            chapter.actual_hours += hours
            chapter.save()

class OCRUsageRecord(models.Model):
    """OCR使用记录"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="用户"
    )
    chapter = models.ForeignKey(
        'Chapter',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="关联章节"
    )
    image_size = models.PositiveIntegerField(verbose_name="图片大小(KB)")
    char_count = models.PositiveIntegerField(verbose_name="识别字符数")
    ocr_type = models.CharField(max_length=20, verbose_name="OCR类型")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="使用时间")
    status = models.BooleanField(default=True, verbose_name="是否成功")

    class Meta:
        verbose_name = "OCR使用记录"
        verbose_name_plural = "OCR使用记录"
        ordering = ['-created_at']