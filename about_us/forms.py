from django import forms
from .models import TeamMember, Award, Certificate, AboutUs, LifeAtOur


class AboutUsForm(forms.ModelForm):
    class Meta:
        model = AboutUs
        fields = '__all__'


class LifeAtOurForm(forms.ModelForm):
    class Meta:
        model = LifeAtOur
        fields = '__all__'


class TeamForm(forms.ModelForm):
    class Meta:
        model = TeamMember
        fields = '__all__'


class AwardForm(forms.ModelForm):
    class Meta:
        model = Award
        fields = '__all__'


class CertificateForm(forms.ModelForm):
    class Meta:
        model = Certificate
        fields = '__all__'