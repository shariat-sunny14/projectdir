from django.db import models
from datetime import datetime
from django.utils import timezone
from django.db.models import Max
from organizations.models import branchslist, organizationlst
from store_setup.models import store
from item_setup.models import items
from supplier_setup.models import suppliers
from django.contrib.auth import get_user_model
User = get_user_model()

# Create your models here.
class without_GRN(models.Model):
    wo_grn_id = models.BigAutoField(primary_key=True, default=1901010000000, editable=False, db_index=True)
    wo_grn_no = models.CharField(max_length=15, editable=False, db_index=True)
    transaction_date = models.DateField(null=True, blank=True, db_index=True)
    id_org = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2wo_grn', on_delete=models.DO_NOTHING, db_index=True)
    branch_id = models.ForeignKey(branchslist, null=True, blank=True, related_name='branch_id2wo_grn', on_delete=models.DO_NOTHING, db_index=True)
    store_id = models.ForeignKey(store, null=True, blank=True, related_name='store_id2wo_grn', on_delete=models.DO_NOTHING, editable=False, db_index=True)
    supplier_id = models.ForeignKey(suppliers, null=True, blank=True, related_name='supplier_id2wo_grn', on_delete=models.DO_NOTHING, db_index=True)
    carrying_lifting_cost = models.FloatField(null=True, blank=True)
    is_cash = models.BooleanField(default=False, db_index=True)
    is_credit = models.BooleanField(default=False, db_index=True)
    is_approved = models.BooleanField(default=False, db_index=True)
    is_approved_by = models.ForeignKey(User, null=True, blank=True, related_name='user_id2wo_grn', on_delete=models.DO_NOTHING)
    approved_date = models.CharField(max_length=50, null=True, blank=True)
    invoice_no = models.CharField(max_length=50, null=True, blank=True)
    invoice_date = models.DateField(null=True, blank=True)
    remarks = models.TextField(max_length=300, default="", blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2wo_grn', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True, db_index=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1007000000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2wo_grn', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True, db_index=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=1006100000000, editable=False)

    class Meta:
        indexes = [
            models.Index(fields=['id_org', 'branch_id', 'supplier_id', 'transaction_date', 'store_id', 'is_cash', 'is_approved']),
            models.Index(fields=['id_org', 'branch_id', 'supplier_id', 'transaction_date', 'store_id', 'is_credit', 'is_approved']),
        ]

    def save(self, *args, **kwargs):
        if self._state.adding:
            if self.id_org_id and self.branch_id_id:
                try:
                    # Get the maximum existing wo_grn_id and increment by 1
                    latest_wo_grn_id = without_GRN.objects.aggregate(Max('wo_grn_id'))['wo_grn_id__max']
                    if latest_wo_grn_id is not None:
                        self.wo_grn_id = latest_wo_grn_id + 1
                    else:
                        self.wo_grn_id = 1901010000000  # Initial value if no records exist

                    # Set the wo_grn_no to "WOG" followed by current date and a unique number
                    current_date = datetime.now().strftime("%Y%m%d")
                    latest_wo_grn_no = without_GRN.objects.filter(
                        id_org=self.id_org_id, 
                        branch_id=self.branch_id_id, 
                        wo_grn_no__startswith=f"WOG{current_date}"
                    ).aggregate(Max('wo_grn_no'))['wo_grn_no__max']

                    if latest_wo_grn_no is not None:
                        # Extract the last 4 digits of the wo_grn_no and increment
                        latest_number = int(latest_wo_grn_no[-4:]) + 1
                        wo_grn_no_str = str(latest_number).zfill(4)
                    else:
                        wo_grn_no_str = '0001'

                    self.wo_grn_no = f"WOG{current_date}{wo_grn_no_str}"

                    # Update session fields
                    user_session = without_GRN.objects.latest('ss_created_session')
                    modifier_session = without_GRN.objects.latest('ss_modified_session')

                    self.ss_created_session = user_session.ss_created_session + 1
                    self.ss_modified_session = modifier_session.ss_modified_session + 1

                except without_GRN.DoesNotExist:
                    pass

        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.wo_grn_id)
    


class without_GRNdtl(models.Model):
    wo_grndtl_id = models.BigAutoField(primary_key=True, default=100410000000, editable=False, db_index=True)
    wo_grn_id = models.ForeignKey(without_GRN, null=True, blank=True, related_name='without_grn_id', on_delete=models.DO_NOTHING, editable=False, db_index=True)
    wo_grn_date = models.DateField(blank=True, null=True, db_index=True)
    store_id = models.ForeignKey(store, null=True, blank=True, related_name='store_id2wo_grnDtl', on_delete=models.DO_NOTHING, editable=False, db_index=True)
    supplier_id = models.ForeignKey(suppliers, null=True, blank=True, related_name='supplier_id2wo_grnDtl', on_delete=models.DO_NOTHING, db_index=True)
    item_id = models.ForeignKey(items, null=True, blank=True, related_name='item_id2wo_grnDtl', on_delete=models.DO_NOTHING, editable=False, db_index=True)
    is_approved = models.BooleanField(default=False, db_index=True)
    approved_date = models.CharField(max_length=50, null=True, blank=True)
    wo_grn_qty = models.FloatField(null=True, blank=True)
    bonus_qty = models.FloatField(null=True, blank=True)
    unit_price = models.FloatField(null=True, blank=True)
    dis_percentage = models.FloatField(null=True, blank=True)
    item_batch = models.CharField(max_length=150, null=True, blank=True)
    item_exp_date = models.DateField(null=True, blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2wo_grnDtl', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True, db_index=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1291000000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2wo_grnDtl', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True, db_index=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=112950000000, editable=False)
    
    class Meta:
        indexes = [
            models.Index(fields=['wo_grn_id', 'store_id', 'wo_grn_date', 'supplier_id', 'item_id', 'is_approved']),
        ]
    
    def save(self, *args, **kwargs):
        
        wo_grndtl_data = without_GRNdtl.objects.all()

        if wo_grndtl_data.exists() and self._state.adding:
            last_orderdtl = wo_grndtl_data.latest('wo_grndtl_id')
            user_session = wo_grndtl_data.latest('ss_created_session')
            modifier_session = wo_grndtl_data.latest('ss_modified_session')
            self.wo_grndtl_id = int(last_orderdtl.wo_grndtl_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1

        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.wo_grndtl_id)