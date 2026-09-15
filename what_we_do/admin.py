# what_we_do/admin.py
from django.contrib import admin
from .models import Service, ServiceSection


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('display_number', 'title', 'is_active', 'updated_at')
    list_editable = ('is_active',)
    list_filter = ('is_active',)
    search_fields = ('title', 'description')
    ordering = ('number',)


@admin.register(ServiceSection)
class ServiceSectionAdmin(admin.ModelAdmin):
    list_display = ('kicker_text', 'heading')

    def has_add_permission(self, request):
        return not ServiceSection.objects.exists()