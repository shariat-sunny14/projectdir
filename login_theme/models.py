from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()

# Create your models here.
class login_themes(models.Model):
    login_theme_id = models.BigAutoField(primary_key=True, default=1339710000000, editable=False)
    login_theme_name = models.CharField(max_length=150, null=True, blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2login_themes', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1456700000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2login_themes', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=189670000000, editable=False)

    def save(self, *args, **kwargs):
        login_theme_data = login_themes.objects.all()

        if login_theme_data.exists() and self._state.adding:
            last_order = login_theme_data.latest('login_theme_id')
            user_session = login_theme_data.latest('ss_created_session')
            modifier_session = login_theme_data.latest('ss_modified_session')
            self.login_theme_id = int(last_order.login_theme_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
            
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.login_theme_id)