import os
from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()


PHOTOS_TYPE_CHOICES = [
    ('wedding', 'Wedding'),
    ('pre_post_wedding', 'Pre -Post Wedding'),
    ('fashion', 'Fashion'),
    ('commercial', 'Commercial'),
    ('corporate', 'Corporate'),
    ('portrait', 'Portrait'),
    ('conceptual_art_theme', 'Conceptual Art / Theme base'),
    ('maternity_family', 'Maternity & Family'),
    ('real_estate_architecture', 'Real Estate & Architecture'),
    ('food_beverage', 'Food & Beverage'),
    ('events', 'Events'),
    ('specialized_photography', 'Specialized Photography'),
    ('aerial_advanced_production', 'Aerial & Advanced Production'),
]


class photos_gallery(models.Model):
    phgallery_id = models.BigAutoField(primary_key=True, editable=False)
    photo_type = models.CharField(max_length=150, choices=PHOTOS_TYPE_CHOICES, default='photography')
    title = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(max_length=10000, null=True, blank=True)
    is_service = models.BooleanField(default=False)
    is_recent_work = models.BooleanField(default=False)
    is_album = models.BooleanField(default=False)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2phgallery_id', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2phgallery_id', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.phgallery_id)


class photos_gallery_dtls(models.Model):
    phgdtls_id = models.BigAutoField(primary_key=True, editable=False)
    phgallery_id = models.ForeignKey(photos_gallery, null=True, blank=True, related_name='phgallery2phgdtls', on_delete=models.CASCADE)
    photos_title = models.CharField(max_length=100, null=True, blank=True)
    photos = models.ImageField(upload_to='photos_gallery', max_length=255, null=True, blank=True)
    is_cover_photo = models.BooleanField(default=False)
    is_thumbnail_photo = models.BooleanField(default=False)
    photo_description = models.CharField(max_length=500, null=True, blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2phgdtls', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2phgdtls', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)

    def delete(self, *args, **kwargs):
        # Delete the file from storage first, if it actually exists
        if self.photos and self.photos.name:
            try:
                if os.path.isfile(self.photos.path):
                    os.remove(self.photos.path)
            except (ValueError, FileNotFoundError):
                pass
        super().delete(*args, **kwargs)

    def __str__(self):
        return str(self.phgdtls_id)