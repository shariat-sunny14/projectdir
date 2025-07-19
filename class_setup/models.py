from django.db import models
from organizations.models import organizationlst
from django.contrib.auth import get_user_model
User = get_user_model()

# Create your models here.
class in_class(models.Model):
    class_id = models.BigAutoField(primary_key=True, default=123020000000, editable=False)
    class_no = models.CharField(max_length=50, null=True, blank=True)
    class_name = models.CharField(max_length=100, null=True, blank=True)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2in_class', on_delete=models.DO_NOTHING)
    allow_groups = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2in_class', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1231000000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2in_class', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=112350000000, editable=False)

    def save(self, *args, **kwargs):
        last_data = in_class.objects.all()

        if last_data.exists() and self._state.adding:
            last_order = last_data.latest('class_id')
            user_session = last_data.latest('ss_created_session')
            modifier_session = last_data.latest('ss_modified_session')
            self.class_id = int(last_order.class_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.class_id)