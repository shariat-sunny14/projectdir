from django import forms
from .models import Testimonial


class TestimonialForm(forms.ModelForm):
    class Meta:
        model = Testimonial
        fields = ["couple_name", "message", "image"]
        widgets = {
            "couple_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Your Name (e.g. Morsheda & Saquib)"
            }),
            "message": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Write your experience with us...",
                "rows": 5
            }),
            "image": forms.ClearableFileInput(attrs={
                "class": "form-control"
            }),
        }