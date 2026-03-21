
from django import forms
from django.forms import Textarea
from .models import Exercise, Chapter, Subject, MethodSummary

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
        fields = [ 'title', 'description', 'estimated_hours','process_description','order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'description', 'color']
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color'}),
        }

class MethodSummaryForm(forms.ModelForm):
    class Meta:
        model = MethodSummary
        fields = ['name', 'description', 'note', 'difficulty_level', 'important_level']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),

        }
        labels = {
            'name': '方法名称',
            'description': '方法描述',
            'note': '备注'
        }

class MethodSummaryCreateForm(forms.ModelForm):
    class Meta:
        model = MethodSummary
        fields = ['name', 'exercises']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'exercises': forms.CheckboxSelectMultiple(),
        }
        labels = {
            'name': '方法名称',
            'exercises': '选择习题'
        }
           


class ExerciseForm(forms.ModelForm):
    class Meta:
        model = Exercise
        fields = [
            'title', 'chapter', 'question_type', 'content', 
            'options', 'answer', 'analysis',
            'difficulty', 'memory_level', 'mastery_level',
            'parent_id', 'answer_time', 'wrong_count'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入习题标题'
            }),
            'content': Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'analysis': Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'difficulty': forms.NumberInput(attrs={
                'min': 1, 'max': 5, 'class': 'form-control'
            }),
            'memory_level': forms.NumberInput(attrs={
                'min': 1, 'max': 5, 'class': 'form-control'
            }),
            'mastery_level': forms.NumberInput(attrs={
                'min': 1, 'max': 5, 'class': 'form-control'
            }),
            'question_type': forms.Select(attrs={'class': 'form-control'}),
            'chapter': forms.Select(attrs={'class': 'form-control'}),
            'parent_id': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '非阅读完形子题不填写'
            }),
            'answer_time': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '默认300秒'
            }),
            'wrong_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '默认0次,可不填写'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['options'].required = False
        self.fields['analysis'].required = False
        self.fields['content'].required = False
        self.fields['title'].required = True
        self.fields['parent_id'].required = False
        self.fields['answer_time'].required = False
        self.fields['wrong_count'].required = False
