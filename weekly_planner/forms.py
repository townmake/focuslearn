from django import forms
from .models import QuickAccess

class QuickAccessForm(forms.ModelForm):
    class Meta:
        model = QuickAccess
        fields = ['title', 'icon', 'link', 'description', 'position']
        widgets = {
            'icon': forms.ClearableFileInput(attrs={'accept': 'image/*'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['icon'].required = False
        self.fields['link'].required = False
        self.fields['link'].widget.attrs['placeholder'] = '可选，留空将无法直接跳转'
        
        # 设置标题默认值为当前日期(YYYYMMDD格式)
        from django.utils import timezone
        if not self.instance.pk and 'title' not in self.data:
            self.fields['title'].initial = timezone.now().strftime('%Y%m%d')
            self.fields['title'].widget.attrs['placeholder'] = timezone.now().strftime('%Y%m%d')
            
        # 设置位置序号默认值为最后一条记录的position+1
        if not self.instance.pk and 'position' not in self.data:
            from .models import QuickAccess
            last_item = QuickAccess.objects.order_by('-position').first()
            default_position = last_item.position + 1 if last_item else 1
            self.fields['position'].initial = default_position
            self.fields['position'].widget.attrs['placeholder'] = str(default_position)