# what_we_do/forms.py
from django import forms
from .models import Service, ServiceSection


class ServiceSectionForm(forms.ModelForm):
    """Section এর উপরের kicker/heading/sub_text এডিট করার ফর্ম"""

    class Meta:
        model = ServiceSection
        fields = ['kicker_text', 'heading', 'sub_text']
        widgets = {
            'kicker_text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'যেমন: What we do'
            }),
            'heading': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Section এর মূল heading লিখুন'
            }),
            'sub_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Section এর নিচের ছোট বর্ণনা লিখুন'
            }),
        }


class ServiceForm(forms.ModelForm):
    """UI থেকে সরাসরি নতুন Service card অ্যাড/এডিট করার জন্য ফর্ম"""

    class Meta:
        model = Service
        fields = ['number', 'title', 'description', 'is_active']
        widgets = {
            'number': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'যেমন: 7'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Service Title (যেমন: Studio Portrait)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'সার্ভিসের সংক্ষিপ্ত বিবরণ লিখুন'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_number(self):
        number = self.cleaned_data['number']
        qs = Service.objects.filter(number=number)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("এই নম্বরে ইতিমধ্যে একটা সার্ভিস আছে, অন্য নম্বর দিন।")
        return number