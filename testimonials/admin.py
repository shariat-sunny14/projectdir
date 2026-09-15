from django.contrib import admin
from .models import Testimonial


@admin.action(description="Mark selected testimonials as Approved")
def approve_testimonials(modeladmin, request, queryset):
    queryset.update(is_approved=True)


@admin.action(description="Mark selected testimonials as Unapproved")
def unapprove_testimonials(modeladmin, request, queryset):
    queryset.update(is_approved=False)


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ("couple_name", "is_approved", "created_at")
    list_filter = ("is_approved", "created_at")
    search_fields = ("couple_name", "message")
    actions = [approve_testimonials, unapprove_testimonials]