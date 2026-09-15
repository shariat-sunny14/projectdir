from django import forms
from django.forms import inlineformset_factory
from .models import WhoWeAre, StatCard


class WhoWeAreForm(forms.ModelForm):
    class Meta:
        model = WhoWeAre
        fields = [
            "kicker_text",
            "subtitle",
            "title_main",
            "title_highlight",
            "title_after",
            "description",
            "note",
            "stats_intro_label",
            "stats_intro_text",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "note": forms.Textarea(attrs={"rows": 3}),
            "stats_intro_text": forms.Textarea(attrs={"rows": 2}),
        }


StatCardFormSet = inlineformset_factory(
    WhoWeAre,
    StatCard,
    fields=["label", "target_number", "suffix", "is_featured", "order"],
    extra=1,
    can_delete=True,
)