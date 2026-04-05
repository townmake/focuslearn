from django import forms

from .models import QuickAccess, QuickAccessLibraryIcon


class QuickAccessForm(forms.ModelForm):
    library_icon = forms.ModelChoiceField(
        label="图标",
        queryset=QuickAccessLibraryIcon.objects.all(),
        required=False,
    )

    class Meta:
        model = QuickAccess
        fields = ["title", "subtitle", "library_icon", "link", "description", "position"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["library_icon"].queryset = QuickAccessLibraryIcon.objects.all().order_by(
            "sort_order", "id"
        )
        self.fields["link"].required = False
        self.fields["link"].widget.attrs["placeholder"] = "可选，留空将无法直接跳转"
        self.fields["subtitle"].required = False
        self.fields["subtitle"].widget = forms.Textarea(
            attrs={
                "rows": 2,
                "placeholder": "一句话说明用途，将显示在列表卡片标题下方（可选）",
            }
        )

        from django.utils import timezone

        if not self.instance.pk and "title" not in self.data:
            self.fields["title"].initial = timezone.now().strftime("%Y%m%d")
            self.fields["title"].widget.attrs["placeholder"] = timezone.now().strftime("%Y%m%d")

        if not self.instance.pk and "position" not in self.data:
            last_item = QuickAccess.objects.order_by("-position").first()
            default_position = last_item.position + 1 if last_item else 1
            self.fields["position"].initial = default_position
            self.fields["position"].widget.attrs["placeholder"] = str(default_position)
