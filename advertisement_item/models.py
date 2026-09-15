from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()
# Create your models here.

class banner_list(models.Model):
    banner_id = models.BigAutoField(primary_key=True, default=1300000000001, editable=False)
    title_name = models.CharField(max_length=50, null=True, blank=True)
    banner_text = models.CharField(max_length=150, null=True, blank=True)
    startup_price = models.CharField(max_length=20, null=True, blank=True)
    banner_img = models.ImageField(upload_to='banner', max_length=255, null=True, blank=True)
    is_publist = models.BooleanField(default=False)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2banner', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1102000010000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2banner', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=1203000020000, editable=False)

    def save(self, *args, **kwargs):
        banner_data = banner_list.objects.all()

        if banner_data.exists() and self._state.adding:
            last_order = banner_data.latest('banner_id')
            user_session = banner_data.latest('ss_created_session')
            modifier_session = banner_data.latest('ss_modified_session')
            self.banner_id = int(last_order.banner_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.banner_id)
