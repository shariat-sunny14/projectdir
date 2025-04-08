from django.db import models
from organizations.models import organizationlst
from django.contrib.auth import get_user_model
User = get_user_model()

# Create your models here.
class in_apps_templates(models.Model):
    temp_id = models.BigAutoField(primary_key=True, default=1099900000000, editable=False)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2bill_temp', on_delete=models.DO_NOTHING)
    billing_temp = models.CharField(max_length=100, null=True, blank=True)
    due_coll_temp = models.CharField(max_length=100, null=True, blank=True)
    inv_can_temp = models.CharField(max_length=100, null=True, blank=True)
    item_can_temp = models.CharField(max_length=100, null=True, blank=True)
    refund_coll_temp = models.CharField(max_length=100, null=True, blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2bill_temp', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1088400000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2bill_temp', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=107750000000, editable=False)

    def save(self, *args, **kwargs):
        temp_data = in_apps_templates.objects.all()

        if temp_data.exists() and self._state.adding:
            last_order = temp_data.latest('temp_id')
            user_session = temp_data.latest('ss_created_session')
            modifier_session = temp_data.latest('ss_modified_session')
            self.temp_id = int(last_order.temp_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
            
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.temp_id)