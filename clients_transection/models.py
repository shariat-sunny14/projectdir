from django.db import models
from organizations.models import branchslist, organizationlst
from registrations.models import in_registrations
from django.contrib.auth import get_user_model
User = get_user_model()

# credit opening balance models
class opening_balance(models.Model):
    opb_id = models.BigAutoField(primary_key=True, default=3088000000000, editable=False)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2opbalance', on_delete=models.DO_NOTHING)
    branch_id = models.ForeignKey(branchslist, null=True, blank=True, related_name='branch_id2opbalance', on_delete=models.DO_NOTHING)
    reg_id = models.ForeignKey(in_registrations, null=True, blank=True, related_name='reg_id2opbalance', on_delete=models.DO_NOTHING)
    opb_amount = models.FloatField(null=True, blank=True)
    is_debited = models.BooleanField(default=False)
    is_credited = models.BooleanField(default=False)
    descriptions = models.CharField(max_length=255, null=True, blank=True)
    opb_date = models.DateField(auto_now_add=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2opbalance', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1099990000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2opbalance', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=1077778000000, editable=False)

    
    def save(self, *args, **kwargs):
        opb_data = opening_balance.objects.all()

        if opb_data.exists() and self._state.adding:
            last_order = opb_data.latest('opb_id')
            user_session = opb_data.latest('ss_created_session')
            modifier_session = opb_data.latest('ss_modified_session')
            self.opb_id = int(last_order.opb_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)
    

    def __str__(self):
        return str(self.opb_id)