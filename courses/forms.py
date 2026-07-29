
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
        fields = ['name', 'description', 'color', 'category', 'heat', 'open_status']
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color'}),
            'category': forms.Select(attrs={'class': 'ant-input'}),
            'heat': forms.NumberInput(attrs={
                'class': 'ant-input',
                'min': 0,
                'max': 10,
                'step': 1,
            }),
            'open_status': forms.Select(attrs={'class': 'ant-input'}),
        }
        labels = {
            'category': '科目分类',
            'heat': '项目热度',
            'open_status': '项目状态',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = SubjectCategory.objects.all().order_by(
            '-display_weight', 'name'
        )
        self.fields['category'].required = False
        self.fields['category'].empty_label = '无分类'
        self.fields['heat'].required = False
        self.fields['heat'].min_value = 0
        self.fields['heat'].max_value = 10
        self.fields['heat'].help_text = '0–10，数值越大在日历/记录选项目时越靠前'
        self.fields['open_status'].required = False
        if self.instance and self.instance.pk is None and 'heat' not in self.data:
            self.fields['heat'].initial = 0
        if self.instance and getattr(self.instance, 'pk', None) is None and 'open_status' not in self.data:
            self.fields['open_status'].initial = Subject.OpenStatus.OPEN

    def clean_heat(self):
        heat = self.cleaned_data.get('heat')
        if heat is None or heat == '':
            return 0
        heat = int(heat)
        if heat < 0 or heat > 10:
            raise forms.ValidationError('项目热度须在 0–10 之间')
        return heat

    def clean_open_status(self):
        status = self.cleaned_data.get('open_status')
        if not status:
            return Subject.OpenStatus.OPEN
        valid = {c[0] for c in Subject.OpenStatus.choices}
        if status not in valid:
            raise forms.ValidationError('无效的项目状态')
        return status
