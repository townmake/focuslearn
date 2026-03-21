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
    
class Subject(models.Model):
    name = models.CharField(max_length=100, verbose_name="科目名称")
    description = models.TextField(blank=True, verbose_name="科目描述")
    estimated_hours = models.PositiveIntegerField(default=0,verbose_name="预计学时(小时)")
    order = models.PositiveIntegerField(default=0, verbose_name="排序序号")
    actual_study_hours = models.PositiveIntegerField(default=0, verbose_name="实际学时(小时)")
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
    
    class Meta:
        verbose_name = "科目"
        verbose_name_plural = "科目"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # 仅保存基础字段，统计字段由信号处理器更新
        super().save(*args, **kwargs)

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
    process_description = models.CharField(_('进度描述'), max_length=255, null=True, blank=True)

    models.CharField(_('标题'), max_length=255)
    #统计字段
    knowledge_points_count = models.PositiveIntegerField(default=0)
    documents_count = models.PositiveIntegerField(default=0)
    videos_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    
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
    difficulty = models.PositiveSmallIntegerField(
        _('难度'), 
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=3
    )
    memory_level = models.PositiveSmallIntegerField(
        _('记忆度'),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=3
    )
    mastery_level = models.PositiveSmallIntegerField(
        _('掌握度'),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=3
    )
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
    exercises = models.ManyToManyField(
        'Exercise',
        related_name='related_knowledge_points',
        blank=True,
        verbose_name=_('关联习题')
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


        
class Exercise(models.Model):
    """习题模型"""
    QUESTION_TYPE_CHOICES = [
        ('single_choice', '单选题'),
        ('multiple_choice', '多选题'),
        ('true_false', '判断题'),
        ('fill_blank', '填空题'),
        ('short_answer', '简答题'),
        ('calculation', '计算题'),
        ('reading_answer', '阅读理解'),
        ('translation', '翻译题'),
        ('cloze_test', '完形填空题'),
        ('essay', '作文题'),
        ('other', '其他'),
    ]
    
    chapter = models.ForeignKey(
        Chapter,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='exercises',
        verbose_name=_('所属章节')
    )
    question_type = models.CharField(
        _('题型'),
        max_length=20,
        choices=QUESTION_TYPE_CHOICES,
        default='single_choice'
    )
    title = models.CharField(_('题目标题'), max_length=255, blank=True, null=True)
    content = TextField(_('题目内容'))
    options = models.JSONField(
        _('选项'),
        blank=True,
        null=True,
        help_text=_('JSON格式存储的选项，如{"A":"选项1","B":"选项2"}')
    )
    answer = models.TextField(_('答案'))
    analysis = TextField(_('解析'), blank=True)
    difficulty = models.PositiveSmallIntegerField(
        _('难度'),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=3
    )
    memory_level = models.PositiveSmallIntegerField(
        _('记忆度'),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=3
    )
    mastery_level = models.PositiveSmallIntegerField(
        _('掌握度'),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=3
    )
    # 答错次数
    wrong_count = models.PositiveIntegerField(_('错误次数'), default=0,null=True, blank=True)
    # 关联的知识点-后面再考虑如何关联起来
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    last_studied_at = models.DateTimeField(_('最后学习时间'), null=True, blank=True)
    #答题时间
    answer_time = models.PositiveIntegerField(_('答题时间(秒)'), default=0, null=True, blank=True)
    correct_count = models.PositiveIntegerField(_('正确次数'), default=0, null=True, blank=True)
    id = models.AutoField(primary_key=True)
    parent_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        default=0,
        verbose_name=_('父习题ID')
    )
    order = models.PositiveIntegerField(_('题目顺序'), default=0, null=True, blank=True)
    next_review_date = models.DateField(
        _('下次复习日期'),
        null=True,
        blank=True,
        help_text=_('根据间隔重复算法计算的下次复习日期')
    )
    # 关联的知识点
    knowledge_points = models.ManyToManyField(
        'KnowledgePoint',
        related_name='related_exercises',
        blank=True,
        through='ExerciseKnowledgePoint',
        through_fields=('exercise', 'knowledge_point'),
        verbose_name=_('关联知识点')
    )
    
    class Meta:
        verbose_name = _('习题')
        verbose_name_plural = _('习题')
        ordering = ['chapter', 'id']
    
    def __str__(self):
        return f"{self.get_question_type_display()}: {self.content[:50]}"

class MethodSummary(models.Model):
    name = models.CharField(max_length=255, verbose_name="方法名称")
    description = TextField(_('方法描述'), blank=True)
    note= models.TextField(verbose_name="备注", blank=True)
    exercises = models.ManyToManyField(Exercise, verbose_name="关联习题")
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

    @property
    def exercise_count(self):
        return self.exercises.count()


class ExerciseKnowledgePoint(models.Model):
    """习题与知识点关联中间模型"""
    exercise = models.ForeignKey(
        'Exercise',
        on_delete=models.CASCADE,
        verbose_name='习题'
    )
    knowledge_point = models.ForeignKey(
        'KnowledgePoint',
        on_delete=models.CASCADE,
        verbose_name='知识点'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='关联时间'
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='排序序号'
    )

    class Meta:
        verbose_name = '习题知识点关联'
        verbose_name_plural = '习题知识点关联'
        ordering = ['exercise', 'order']
        unique_together = ('exercise', 'knowledge_point')

    def __str__(self):
        return f"{self.exercise.id} - {self.knowledge_point.title}"


class ExerciseAnswer(models.Model):
    """答题记录模型"""
    exercise = models.ForeignKey(
        'Exercise',
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name='习题'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='用户'
    )
    exercise_set_completion = models.ForeignKey(
        'ExerciseSetCompletion',
        on_delete=models.CASCADE,
        related_name='answers',
        null=True,
        blank=True,
        verbose_name='关联练习集完成记录'
    )
    review_set_completion = models.ForeignKey(
        'ReviewSetCompletion',
        on_delete=models.CASCADE,
        related_name='review_answers',
        null=True,
        blank=True,
        verbose_name='关联复习集完成记录'
    )
    answer = models.TextField(verbose_name='用户答案')
    time_spent = models.PositiveIntegerField(
        default=0,
        blank=True,
        null=True,
        verbose_name='答题时长(秒)',
        help_text='用户答题所用的时间'
    )
    is_correct = models.BooleanField(verbose_name='是否正确')
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='答题时间'
    )
    difficulty = models.PositiveSmallIntegerField(
        default=3,
        verbose_name='难度',
        null=True,
        blank=True
    )
    mastery_level = models.PositiveSmallIntegerField(
        default=3,
        verbose_name='掌握度',
        null=True,
        blank=True
    )
    memory_level = models.PositiveSmallIntegerField(
        default=3,
        verbose_name='记忆度',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = '答题记录'
        verbose_name_plural = '答题记录'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.exercise.id} - {'正确' if self.is_correct else '错误'}"


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
            ('exercises', '习题评论'),
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



class ExerciseSet(models.Model):
    """练习集模型"""
    name = models.CharField(max_length=100, verbose_name="练习集名称")
    chapter = models.ForeignKey(
        Chapter,
        on_delete=models.CASCADE,
        related_name='exercise_sets',
        verbose_name="所属章节"
    )
    suggested_time = models.PositiveIntegerField(
        verbose_name="建议完成时间(分钟)",
        help_text="建议完成练习集的时间(分钟)"
    )
    exercises = models.ManyToManyField(
        Exercise,
        related_name='exercise_sets',
        verbose_name="包含习题"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="更新时间"
    )
    completion_count = models.PositiveIntegerField(
        default=0,
        verbose_name="完成次数"
    )
    last_completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="最近完成时间"
    )

    class Meta:
        verbose_name = "练习集"
        verbose_name_plural = "练习集"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.chapter.title})"

    def get_absolute_url(self):
        return reverse('courses:exercise_set_detail', kwargs={'pk': self.pk})

class ExerciseSetCompletion(models.Model):
    """练习集完成记录"""
    exercise_set = models.ForeignKey(
        ExerciseSet,
        on_delete=models.CASCADE,
        related_name='completions',
        verbose_name="练习集"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="用户"
    )
    completed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="完成时间"
    )
    time_spent = models.PositiveIntegerField(
        verbose_name="实际用时(秒)"
    )
    score = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="得分"
    )
    correct_count = models.PositiveIntegerField(
        verbose_name="正确题数"
    )
    total_count = models.PositiveIntegerField(
        verbose_name="总题数"
    )

    class Meta:
        verbose_name = "练习集完成记录"
        verbose_name_plural = "练习集完成记录"
        ordering = ['-completed_at']

    def __str__(self):
        return f"{self.user.username} - {self.exercise_set.name}"
    
class ReviewSet(models.Model):
    """复习集模型"""
    name = models.CharField(max_length=100, verbose_name="复习集名称")
    chapter = models.ForeignKey(
        Chapter,
        on_delete=models.CASCADE,
        related_name='review_sets',
        verbose_name="所属章节",
        null=True,
        blank=True
    )
    subject_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="关联的科目Id"
    )
    
    exercises = models.ManyToManyField(
        Exercise,
        related_name='review_sets',
        verbose_name="包含习题",
        blank=True
    )

    @property
    def subject(self):
        """通过章节获取关联科目"""
        if self.chapter:
            return self.chapter.subject
        return None
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="更新时间"
    )
    completion_count = models.PositiveIntegerField(
        default=0,
        verbose_name="完成次数"
    )
    last_completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="最近完成时间"
    )

    class Meta:
        verbose_name = "复习集"
        verbose_name_plural = "复习集"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.chapter.title})"

    def get_absolute_url(self):
        return reverse('courses:review_set_detail', kwargs={'pk': self.pk})

class ReviewSetCompletion(models.Model):
    """复习集完成记录"""
    review_set = models.ForeignKey(
        ReviewSet,
        on_delete=models.CASCADE,
        related_name='review_completions',
        verbose_name="复习集"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="用户"
    )
    completed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="完成时间"
    )
    time_spent = models.PositiveIntegerField(
        verbose_name="实际用时(秒)"
    )
    score = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="得分"
    )
    correct_count = models.PositiveIntegerField(
        verbose_name="正确题数"
    )
    total_count = models.PositiveIntegerField(
        verbose_name="总题数"
    )

    class Meta:
        verbose_name = "复习集完成记录"
        verbose_name_plural = "复习集完成记录"
        ordering = ['-completed_at']

    def __str__(self):
        return f"{self.user.username} - {self.review_set.name}"


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
        ('study', '学习'),
        ('exercise', '练习'),
        ('review', '复习'),
        ('other', '其他'),
    ]
    page_type = models.CharField(
        max_length=20, 
        choices=PAGE_TYPE_CHOICES, 
        verbose_name="学习类型"
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
    
    class Meta:
        verbose_name = "学习记录"
        verbose_name_plural = "学习记录"
        ordering = ['-start_time']
    
    def __str__(self):
        return f"{self.user.username} - {self.subject_name} - {timezone.localtime(self.start_time).strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def duration_display(self):
        hours = self.duration // 3600
        minutes = (self.duration % 3600) // 60
        seconds = self.duration % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    



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
        当学习记录保存时更新章节的实际学习时长
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