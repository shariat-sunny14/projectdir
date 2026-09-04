from django import forms
from .models import YouTubeVideo

class YouTubeVideoForm(forms.ModelForm):
    class Meta:
        model = YouTubeVideo
        fields = ['title', 'iframe_code']
        widgets = {
            'iframe_code': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': '<iframe src="..."></iframe>'
            })
        }