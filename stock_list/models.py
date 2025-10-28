from django.db import models
from datetime import datetime
from purchase_order.models import purchase_order_list
from store_setup.models import store
from item_setup.models import items
from opening_stock.models import opening_stock, opening_stockdtl
from G_R_N_with_without.models import without_GRN, without_GRNdtl
from po_receive.models import po_receive_details
from po_return_receive.models import po_return_received_details
from po_return.models import po_return_details
from stock_reconciliation.models import item_reconciliation, item_reconciliationdtl
from local_purchase.models import local_purchase, local_purchasedtl
from organizations.models import organizationlst
from manual_return_receive.models import manual_return_receive, manual_return_receivedtl
from local_purchase_return.models import lp_return_details
from django.contrib.auth import get_user_model

from store_transfers.models import stock_transfer_list, stock_transfer_listdtl
User = get_user_model()

# Create your models here.
class stock_lists(models.Model):
    stock_id = models.BigAutoField(primary_key=True, default=112300000000, editable=False)
    op_st_id = models.ForeignKey(opening_stock, null=True, blank=True, related_name='op_st_id2stock_lists', on_delete=models.DO_NOTHING, editable=False)
    op_stdtl_id = models.ForeignKey(opening_stockdtl, null=True, blank=True, related_name='op_stdtl_id2stock_lists', on_delete=models.DO_NOTHING, editable=False)
    wo_grn_id = models.ForeignKey(without_GRN, null=True, blank=True, related_name='wo_grn_id2stock_lists', on_delete=models.DO_NOTHING, editable=False)
    wo_grndtl_id = models.ForeignKey(without_GRNdtl, null=True, blank=True, related_name='wo_grndtl_id2stock_lists', on_delete=models.DO_NOTHING, editable=False)
    po_id = models.ForeignKey(purchase_order_list, null=True, blank=True, related_name='po_id2stock_lists', on_delete=models.DO_NOTHING, editable=False)
    pordtl_id = models.ForeignKey(po_receive_details, null=True, blank=True, related_name='pordtl_id2stock_lists', on_delete=models.DO_NOTHING, editable=False)
    poretdtl_id = models.ForeignKey(po_return_details, null=True, blank=True, related_name='poretdtl_id2stock_lists', on_delete=models.DO_NOTHING, editable=False)
    porrecdtl_id = models.ForeignKey(po_return_received_details, null=True, blank=True, related_name='porrecdtl_id2stock_lists', on_delete=models.DO_NOTHING, editable=False)
    recon_id = models.ForeignKey(item_reconciliation, null=True, blank=True, related_name='recon_id2stock_lists', on_delete=models.DO_NOTHING, editable=False)
    recondtl_id = models.ForeignKey(item_reconciliationdtl, null=True, blank=True, related_name='recondtl_id2stock_lists', on_delete=models.DO_NOTHING, editable=False)
    lp_id = models.ForeignKey(local_purchase, null=True, blank=True, related_name='lp_id2stock_lists', on_delete=models.DO_NOTHING, editable=False)
    lp_dtl_id = models.ForeignKey(local_purchasedtl, null=True, blank=True, related_name='lp_dtl_id2stock_lists', on_delete=models.DO_NOTHING, editable=False)
    lprdtl_id = models.ForeignKey(lp_return_details, null=True, blank=True, related_name='lprdtl_id2stock_lists', on_delete=models.DO_NOTHING, editable=False)
    item_id = models.ForeignKey(items, null=True, blank=True, related_name='item_id2stock_lists', on_delete=models.DO_NOTHING, editable=False)
    store_id = models.ForeignKey(store, null=True, blank=True, related_name='store_id2stock_lists', on_delete=models.DO_NOTHING, editable=False)
    manu_ret_rec_id = models.ForeignKey(manual_return_receive, null=True, blank=True, related_name='manu_ret_rec_id2stock_lists', on_delete=models.DO_NOTHING, editable=False)
    manu_ret_rec_dtl_id = models.ForeignKey(manual_return_receivedtl, null=True, blank=True, related_name='manu_ret_rec_dtl_id2stock_lists', on_delete=models.DO_NOTHING, editable=False)
    stock_trans_id = models.ForeignKey(stock_transfer_list, null=True, blank=True, related_name='stock_trans_id2stock_lists', on_delete=models.DO_NOTHING, editable=False)
    stock_transdtl_id = models.ForeignKey(stock_transfer_listdtl, null=True, blank=True, related_name='stock_transdtl_id2stock_lists', on_delete=models.DO_NOTHING, editable=False)
    recon_type = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    approved_date = models.CharField(max_length=50, null=True, blank=True)
    stock_qty = models.FloatField(default=0, blank=True)
    is_cancel_qty = models.FloatField(default=0, blank=True)
    item_batch = models.CharField(max_length=150, null=True, blank=True)
    item_exp_date = models.DateField(null=True, blank=True)
    stock_date = models.DateField(auto_now=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2stock_lists', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1291000000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2stock_lists', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=112950000000, editable=False)

    def __str__(self):
        return str(self.stock_id)
    
    def save(self, *args, **kwargs):
        
        data = stock_lists.objects.all()

        if data.exists() and self._state.adding:
            last_orderdtl = data.latest('stock_id')
            user_session = data.latest('ss_created_session')
            modifier_session = data.latest('ss_modified_session')
            self.stock_id = int(last_orderdtl.stock_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1

        super().save(*args, **kwargs)



class in_stock(models.Model):
    in_stock_id = models.BigAutoField(primary_key=True, default=111011000000, editable=False)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2in_stock', on_delete=models.DO_NOTHING, editable=False)
    item_id = models.ForeignKey(items, null=True, blank=True, related_name='item_id2in_stock', on_delete=models.DO_NOTHING, editable=False)
    store_id = models.ForeignKey(store, null=True, blank=True, related_name='store_id2in_stock', on_delete=models.DO_NOTHING, editable=False)
    stock_qty = models.FloatField(default=0, blank=True)


    def __str__(self):
        return str(self.in_stock_id)
    
    def save(self, *args, **kwargs):
        
        in_stock_data = in_stock.objects.all()

        if in_stock_data.exists() and self._state.adding:
            last_orderdtl = in_stock_data.latest('in_stock_id')
            self.in_stock_id = int(last_orderdtl.in_stock_id) + 1
            
        super().save(*args, **kwargs)