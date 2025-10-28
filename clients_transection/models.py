from django.db import models
from organizations.models import branchslist, organizationlst
from registrations.models import in_registrations
from supplier_setup.models import suppliers
from django.contrib.auth import get_user_model
User = get_user_model()

# credit opening balance models
class opening_balance(models.Model):
    opb_id = models.BigAutoField(primary_key=True, default=3088000000000, editable=False, db_index=True)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2opbalance', on_delete=models.DO_NOTHING, db_index=True)
    branch_id = models.ForeignKey(branchslist, null=True, blank=True, related_name='branch_id2opbalance', on_delete=models.DO_NOTHING, db_index=True)
    reg_id = models.ForeignKey(in_registrations, null=True, blank=True, related_name='reg_id2opbalance', on_delete=models.DO_NOTHING, db_index=True)
    opb_amount = models.FloatField(null=True, blank=True)
    is_debited = models.BooleanField(default=False, db_index=True)
    is_credited = models.BooleanField(default=False, db_index=True)
    descriptions = models.CharField(max_length=255, null=True, blank=True)
    opb_date = models.DateField(auto_now_add=True, db_index=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2opbalance', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True, db_index=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1099990000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2opbalance', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True, db_index=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=1077778000000, editable=False)

    class Meta:
        indexes = [
            models.Index(fields=['org_id', 'branch_id', 'reg_id', 'is_debited', 'opb_date']),
            models.Index(fields=['org_id', 'branch_id', 'reg_id', 'is_credited', 'opb_date']),
        ]
        
        
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



class paymentsdtls(models.Model):
    pay_id = models.BigAutoField(primary_key=True, default=1142340000000, editable=False, db_index=True)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2paydtls', on_delete=models.DO_NOTHING, db_index=True)
    branch_id = models.ForeignKey(branchslist, null=True, blank=True, related_name='branch_id2paydtls', on_delete=models.DO_NOTHING, db_index=True)
    reg_id = models.ForeignKey(in_registrations, null=True, blank=True, related_name='reg_id2paydtls', on_delete=models.DO_NOTHING, db_index=True)
    supplier_id = models.ForeignKey(suppliers, null=True, blank=True, related_name='supplier_id2paydtls', on_delete=models.DO_NOTHING, db_index=True)
    pay_date = models.DateField(auto_now_add=True, db_index=True)
    is_reg_client = models.BooleanField(default=False, db_index=True)
    is_supplier_party = models.BooleanField(default=False, db_index=True)
    pay_amount = models.FloatField(null=True, blank=True)
    descriptions = models.CharField(max_length=255, null=True, blank=True)
    pay_mode = models.CharField(max_length=4, null=True, blank=True)
    pay_type = models.CharField(max_length=4, null=True, blank=True)
    comments = models.CharField(max_length=100, null=True, blank=True)
    card_info = models.CharField(max_length=50, null=True, blank=True)
    pay_mob_number = models.CharField(max_length=15, null=True, blank=True)
    pay_reference = models.CharField(max_length=100, null=True, blank=True)
    bank_name = models.CharField(max_length=50, null=True, blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2paydtls', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True, db_index=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1030950000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2paydtls', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True, db_index=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=1025875000000, editable=False)

    class Meta:
        indexes = [
            # For client payments
            models.Index(fields=['org_id', 'branch_id', 'reg_id', 'pay_date', 'is_reg_client']),
            # For supplier payments
            models.Index(fields=['org_id', 'branch_id', 'reg_id', 'pay_date', 'is_supplier_party']),
            # Optional index for supplier_id searches
            models.Index(fields=['supplier_id', 'pay_date', 'is_supplier_party']),
            # Single field index
            models.Index(fields=['pay_mode']),
        ]
    
    
    def save(self, *args, **kwargs):
        pay_data = paymentsdtls.objects.all()

        if pay_data.exists() and self._state.adding:
            last_order = pay_data.latest('pay_id')
            user_session = pay_data.latest('ss_created_session')
            modifier_session = pay_data.latest('ss_modified_session')
            self.pay_id = int(last_order.pay_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)
    

    def __str__(self):
        return str(self.pay_id)