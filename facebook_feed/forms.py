from django import forms
from .models import FacebookSettings

class FacebookSettingsForm(forms.ModelForm):
    class Meta:
        model = FacebookSettings
        fields = ['page_id', 'access_token']
        widgets = {
            'access_token': forms.Textarea(attrs={'rows': 3}),
        }