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
class stock_transfer_list(models.Model):
    stock_trans_id = models.BigAutoField(primary_key=True, default=1009090000000, editable=False)
    stock_trans_no = models.CharField(max_length=15, editable=False)
    transaction_date = models.DateField(null=True, blank=True)
    id_org = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2stock_transfer', on_delete=models.DO_NOTHING)
    branch_id = models.ForeignKey(branchslist, null=True, blank=True, related_name='branch_id2stock_transfer', on_delete=models.DO_NOTHING)
    from_store = models.ForeignKey(store, null=True, blank=True, related_name='from_store2stock_transfer', on_delete=models.DO_NOTHING, editable=False)
    to_store = models.ForeignKey(store, null=True, blank=True, related_name='to_store2stock_transfer', on_delete=models.DO_NOTHING, editable=False)
    is_approved = models.BooleanField(default=False)
    is_approved_by = models.ForeignKey(User, null=True, blank=True, related_name='user_id2stock_transfer', on_delete=models.DO_NOTHING)
    approved_date = models.CharField(max_length=50, null=True, blank=True)
    remarks = models.TextField(max_length=300, default="", blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2stock_transfer', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1009900900000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2stock_transfer', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=1008800090000, editable=False)


    def save(self, *args, **kwargs):
        if self._state.adding:
            if self.id_org_id and self.branch_id_id:
                try:
                    # Get the maximum existing stock_trans_id and increment by 1
                    latest_stock_trans_id = stock_transfer_list.objects.aggregate(Max('stock_trans_id'))['stock_trans_id__max']
                    if latest_stock_trans_id is not None:
                        self.stock_trans_id = latest_stock_trans_id + 1
                    else:
                        self.stock_trans_id = 1009090000000  # Initial value if no records exist

                    # Set the stock_trans_no to "STR" followed by current date and a unique number
                    current_date = datetime.now().strftime("%Y%m%d")
                    latest_stock_trans_no = stock_transfer_list.objects.filter(
                        id_org=self.id_org_id, 
                        branch_id=self.branch_id_id, 
                        stock_trans_no__startswith=f"STI{current_date}"
                    ).aggregate(Max('stock_trans_no'))['stock_trans_no__max']

                    if latest_stock_trans_no is not None:
                        # Extract the last 4 digits of the stock_trans_no and increment
                        latest_number = int(latest_stock_trans_no[-4:]) + 1
                        stock_trans_no_str = str(latest_number).zfill(4)
                    else:
                        stock_trans_no_str = '0001'

                    self.stock_trans_no = f"STR{current_date}{stock_trans_no_str}"

                    # Update session fields
                    user_session = stock_transfer_list.objects.latest('ss_created_session')
                    modifier_session = stock_transfer_list.objects.latest('ss_modified_session')

                    self.ss_created_session = user_session.ss_created_session + 1
                    self.ss_modified_session = modifier_session.ss_modified_session + 1

                except stock_transfer_list.DoesNotExist:
                    pass

        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.stock_trans_id)
    

class stock_transfer_listdtl(models.Model):
    stock_transdtl_id = models.BigAutoField(primary_key=True, default=1007800900000, editable=False)
    stock_trans_id = models.ForeignKey(stock_transfer_list, null=True, blank=True, related_name='transfer_id2transferDtl', on_delete=models.DO_NOTHING, editable=False)
    transaction_date = models.DateField(blank=True, null=True)
    from_store = models.ForeignKey(store, null=True, blank=True, related_name='from_store2transferDtl', on_delete=models.DO_NOTHING, editable=False)
    to_store = models.ForeignKey(store, null=True, blank=True, related_name='to_store2transferDtl', on_delete=models.DO_NOTHING, editable=False)
    item_id = models.ForeignKey(items, null=True, blank=True, related_name='item_id2transferDtl', on_delete=models.DO_NOTHING, editable=False)
    is_approved = models.BooleanField(default=False)
    approved_date = models.CharField(max_length=50, null=True, blank=True)
    transfer_qty = models.FloatField(null=True, blank=True)
    item_batch = models.CharField(max_length=150, null=True, blank=True)
    item_exp_date = models.DateField(null=True, blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2transferDtl', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1299900000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2transferDtl', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=112999000000, editable=False)
    
    
    
    def save(self, *args, **kwargs):
        
        wo_grndtl_data = stock_transfer_listdtl.objects.all()

        if wo_grndtl_data.exists() and self._state.adding:
            last_orderdtl = wo_grndtl_data.latest('stock_transdtl_id')
            user_session = wo_grndtl_data.latest('ss_created_session')
            modifier_session = wo_grndtl_data.latest('ss_modified_session')
            self.stock_transdtl_id = int(last_orderdtl.stock_transdtl_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1

        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.stock_transdtl_id)