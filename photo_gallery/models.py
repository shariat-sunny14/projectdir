import os
from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()


class photos_gallery(models.Model):
    phgallery_id = models.BigAutoField(primary_key=True, default=1450000000001, editable=False)
    gallery_name = models.CharField(max_length=100, null=True, blank=True)
    thumbnail_title = models.CharField(max_length=100, null=True, blank=True)
    descriptions = models.CharField(max_length=500, null=True, blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2phgallery_id', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1342000010000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2phgallery_id', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=1533000020000, editable=False)

    def save(self, *args, **kwargs):
        last_data = photos_gallery.objects.all()

        if last_data.exists() and self._state.adding:
            last_order = last_data.latest('phgallery_id')
            user_session = last_data.latest('ss_created_session')
            modifier_session = last_data.latest('ss_modified_session')
            self.phgallery_id = int(last_order.phgallery_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.phgallery_id)
    
    

class photos_gallery_dtls(models.Model):
    phgdtls_id = models.BigAutoField(primary_key=True, default=1350000000001, editable=False)
    phgallery_id = models.ForeignKey(photos_gallery, null=True, blank=True, related_name='phgallery2phgdtls', on_delete=models.CASCADE)
    photos_title = models.CharField(max_length=100, null=True, blank=True)
    photos = models.ImageField(upload_to='photos_gallery', max_length=255, null=True, blank=True)
    is_cover_photo = models.BooleanField(default=False)
    is_thumbnail_photo = models.BooleanField(default=False)
    photo_description = models.CharField(max_length=500, null=True, blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2phgdtls', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1232000010000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2phgdtls', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=1351000020000, editable=False)

    def delete(self, *args, **kwargs):
        # Delete the file from storage first
        if self.photos and os.path.isfile(self.photos.path):
            os.remove(self.photos.path)
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        last_data = photos_gallery_dtls.objects.all()

        if last_data.exists() and self._state.adding:
            last_order = last_data.latest('phgdtls_id')
            user_session = last_data.latest('ss_created_session')
            modifier_session = last_data.latest('ss_modified_session')
            self.phgdtls_id = int(last_order.phgdtls_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.phgdtls_id)