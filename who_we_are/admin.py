# admin.py
from django.contrib import admin
from .models import WhoWeAre, StatCard


class StatCardInline(admin.TabularInline):
    model = StatCard
    extra = 1
    fields = ("label", "target_number", "suffix", "is_featured", "order")


@admin.register(WhoWeAre)
class WhoWeAreAdmin(admin.ModelAdmin):
    inlines = [StatCardInline]
    readonly_fields = ("updated_at",)

    fieldsets = (
        ("Kicker / Heading", {
            "fields": ("kicker_text", "subtitle", "title_main",
                       "title_highlight", "title_after")
        }),
        ("Description", {
            "fields": ("description", "note")
        }),
        ("Stats Intro (right side)", {
            "fields": ("stats_intro_label", "stats_intro_text")
        }),
        ("Meta", {
            "fields": ("updated_at",)
        }),
    )

    def has_add_permission(self, request):
        # Ekbar row create hoye gele, admin theke "Add" button hide hoye jabe
        return not WhoWeAre.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Singleton row delete kora jabe na
        return False