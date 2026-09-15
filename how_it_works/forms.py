from django import forms

from .models import ProcessSection, ProcessStep


class ProcessSectionForm(forms.ModelForm):
    class Meta:
        model = ProcessSection
        fields = ["kicker", "heading", "is_active"]
        widgets = {
            "kicker": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "How it works"}
            ),
            "heading": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "From first message to final gallery",
                }
            ),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class ProcessStepForm(forms.ModelForm):
    class Meta:
        model = ProcessStep
        fields = ["step_number", "title", "description", "order", "is_active"]
        widgets = {
            "step_number": forms.NumberInput(
                attrs={"class": "form-control", "min": 1}
            ),
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Inquiry & date check"}
            ),
            "description": forms.Textarea(
                attrs={"class": "form-control", "rows": 4}
            ),
            "order": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
