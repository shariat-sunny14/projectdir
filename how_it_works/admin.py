from django.contrib import admin

from .models import ProcessSection, ProcessStep


@admin.register(ProcessSection)
class ProcessSectionAdmin(admin.ModelAdmin):
    list_display = ("kicker", "heading", "is_active", "updated_at")

    def has_add_permission(self, request):
        # singleton — নতুন row add করা যাবে না
        return not ProcessSection.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ProcessStep)
class ProcessStepAdmin(admin.ModelAdmin):
    list_display = (
        "formatted_step_number",
        "title",
        "order",
        "is_active",
        "updated_at",
    )
    list_editable = ("order", "is_active")
    search_fields = ("title", "description")
    ordering = ("order", "step_number")
