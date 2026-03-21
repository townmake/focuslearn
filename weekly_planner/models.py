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


        # 确保结束时间不早于开始时间
        if self.end_time < self.start_time:
            self.end_time = self.start_time

        # 保存任务
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
    name = models.CharField(max_length=100, blank=True, null=True)
    date = models.DateField(null=True, blank=True)  # 允许为空，以便用户可以在稍后设置

    def __str__(self):
        return self.user.username
    
class QuickAccess(models.Model):
    title = models.CharField('标题', max_length=100)
    icon = models.ImageField('图标', upload_to='quick_access_icons/', help_text='上传图标图片')
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
