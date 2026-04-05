
from django import forms
from django.forms import Textarea
from .models import Chapter, Subject, SubjectCategory

class ChapterForm(forms.ModelForm):
    class Meta:
        model = Chapter
        fields = [ 'title', 'description', 'order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class ChapterForm_detail(forms.ModelForm):
    class Meta:
        model = Chapter
        fields = ["title", "description", "estimated_hours", "progress_status", "order"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "progress_status": forms.Select(attrs={"class": "ant-input-chapter"}),
        }
        labels = {
            "progress_status": "进度状态",
        }

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'description', 'color', 'category']
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color'}),
            'category': forms.Select(attrs={'class': 'ant-input'}),
        }
        labels = {
            'category': '科目分类',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = SubjectCategory.objects.all().order_by(
            '-display_weight', 'name'
        )
        self.fields['category'].required = False
        self.fields['category'].empty_label = '无分类'
