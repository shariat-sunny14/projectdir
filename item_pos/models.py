from django.db import models
from datetime import datetime
from django.utils import timezone
from pytz import timezone as tz
from organizations.models import branchslist, organizationlst
from drivers_setup.models import drivers_list
from registrations.models import in_registrations
from others_setup.models import item_uom
from supplier_setup.models import suppliers
from store_setup.models import store
from item_setup.models import items
from stock_list.models import stock_lists
from django.contrib.auth import get_user_model
User = get_user_model()

# invoice_lists table
class invoice_list(models.Model):
    inv_id = models.BigAutoField(primary_key=True, default=1000110010000, editable=False, db_index=True)
    invoice_date = models.DateField(default=datetime.now, editable=False, db_index=True)
    # bill type button
    is_general_bill = models.BooleanField(default=False, db_index=True)
    is_b2b_clients = models.BooleanField(default=False, db_index=True)
    is_non_register = models.BooleanField(default=False)
    is_register = models.BooleanField(default=False)
    is_cancel = models.BooleanField(default=False, db_index=True)
    is_carrcost_notapp = models.BooleanField(default=False)
    is_update = models.BooleanField(default=False)
    is_modified_item = models.BooleanField(default=False)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2invoice', on_delete=models.DO_NOTHING, db_index=True)
    branch_id = models.ForeignKey(branchslist, null=True, blank=True, related_name='branch_id2invoice', on_delete=models.DO_NOTHING, db_index=True)
    cash_point = models.ForeignKey(store, null=True, blank=True, related_name='store_id2invoice', on_delete=models.DO_NOTHING, editable=False, db_index=True)
    # b2b client refferance id
    supplier_id = models.ForeignKey(suppliers, null=True, blank=True, related_name='supplier_id2invoice', on_delete=models.DO_NOTHING, editable=False, db_index=True)
    # registrations refferance id
    reg_id = models.ForeignKey(in_registrations, null=True, blank=True, related_name='reg_id2invoice', on_delete=models.DO_NOTHING, editable=False, db_index=True)
    driver_id = models.ForeignKey(drivers_list, null=True, blank=True, related_name='driver_id2invoice', on_delete=models.DO_NOTHING, editable=False, db_index=True)
    driver_name = models.CharField(max_length=100, null=True, blank=True)
    driver_mobile = models.CharField(max_length=20, null=True, blank=True, db_index=True)
    customer_name = models.CharField(max_length=100, null=True, blank=True)
    gender = models.CharField(max_length=20, null=True, blank=True)
    mobile_number = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    house_no = models.CharField(max_length=50, null=True, blank=True)
    floor_no = models.CharField(max_length=50, null=True, blank=True)
    road_no = models.CharField(max_length=50, null=True, blank=True)
    sector_no = models.CharField(max_length=50, null=True, blank=True)
    area = models.CharField(max_length=50, null=True, blank=True)
    order_no = models.CharField(max_length=50, null=True, blank=True)
    side_office_factory = models.CharField(max_length=150, null=True, blank=True)
    address = models.CharField(max_length=250, null=True, blank=True)
    remarks = models.CharField(max_length=250, null=True, blank=True)
    emergency_person = models.CharField(max_length=150, null=True, blank=True)
    emergency_phone = models.CharField(max_length=20, null=True, blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2invoice', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(editable=False, null=True, blank=True, db_index=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1266000000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2invoice', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True, db_index=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=112670000000, editable=False)


    class Meta:
        indexes = [
            models.Index(fields=['org_id', 'branch_id', 'invoice_date']),
            models.Index(fields=['mobile_number']),
            models.Index(fields=['is_cancel']),
        ]
        index_together = [('org_id', 'branch_id', 'invoice_date')]

    def save(self, *args, **kwargs):
        if self._state.adding:
            dhaka_tz = tz('Asia/Dhaka')
            self.ss_created_on = timezone.now().astimezone(dhaka_tz)

            # Autoincrement IDs and session fields
            last_order = invoice_list.objects.latest('inv_id') if invoice_list.objects.exists() else None
            last_user_session = invoice_list.objects.latest('ss_created_session') if invoice_list.objects.exists() else None
            last_modifier_session = invoice_list.objects.latest('ss_modified_session') if invoice_list.objects.exists() else None

            self.inv_id = last_order.inv_id + 1 if last_order else 1000110010000
            self.ss_created_session = last_user_session.ss_created_session + 1 if last_user_session else 1266000000000
            self.ss_modified_session = last_modifier_session.ss_modified_session + 1 if last_modifier_session else 112670000000

        super().save(*args, **kwargs)

    
    def __str__(self):
        return str(self.inv_id)

# invoicedtl_lists table
class invoicedtl_list(models.Model):
    invdtl_id = models.BigAutoField(primary_key=True, default=1100000000000, editable=False, db_index=True)
    invoice_date = models.DateField(default=datetime.now, db_index=True)
    inv_id = models.ForeignKey(invoice_list, null=True, blank=True, on_delete=models.DO_NOTHING, db_index=True)
    item_id = models.ForeignKey(items, null=True, blank=True, related_name='item_id2invoicedtl', on_delete=models.DO_NOTHING, editable=False, db_index=True)
    store_id = models.ForeignKey(store, null=True, blank=True, related_name='store_id2invoicedtl', on_delete=models.DO_NOTHING, editable=False, db_index=True)
    stock_id = models.ForeignKey(stock_lists, null=True, blank=True, related_name='stock_id2invoicedtl', on_delete=models.DO_NOTHING, editable=False, db_index=True)
    item_name = models.CharField(max_length=200, blank=True, null=True)
    qty = models.FloatField(default=0, blank=True)
    item_uom_id = models.ForeignKey(item_uom, null=True, blank=True, related_name='item_uom_id2invoicedtl', on_delete=models.DO_NOTHING, editable=False, db_index=True)
    sales_rate = models.FloatField(default=0, blank=True)
    item_w_dis = models.FloatField(default=0, blank=True)
    gross_dis = models.FloatField(default=0, blank=True)
    gross_vat_tax = models.FloatField(default=0, blank=True)
    is_cancel = models.BooleanField(default=False, db_index=True)
    is_cancel_qty = models.FloatField(default=0, blank=True)
    cancel_reason = models.CharField(max_length=200, default='', blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2invoicedtl', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(editable=False, null=True, blank=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1268000000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2invoicedtl', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=112690000000, editable=False)

    class Meta:
        indexes = [
            models.Index(fields=['inv_id', 'item_id', 'store_id', 'stock_id', 'item_uom_id']),
        ]

    def save(self, *args, **kwargs):
        if self._state.adding:
            dhaka_tz = tz('Asia/Dhaka')
            self.ss_created_on = timezone.now().astimezone(dhaka_tz)

            # Autoincrement IDs and session fields
            last_order = invoicedtl_list.objects.latest('invdtl_id') if invoicedtl_list.objects.exists() else None
            last_user_session = invoicedtl_list.objects.latest('ss_created_session') if invoicedtl_list.objects.exists() else None
            last_modifier_session = invoicedtl_list.objects.latest('ss_modified_session') if invoicedtl_list.objects.exists() else None

            self.invdtl_id = last_order.invdtl_id + 1 if last_order else 1100000000000
            self.ss_created_session = last_user_session.ss_created_session + 1 if last_user_session else 1268000000000
            self.ss_modified_session = last_modifier_session.ss_modified_session + 1 if last_modifier_session else 112690000000

        super().save(*args, **kwargs)

    
    def __str__(self):
        return str(self.invdtl_id)

# payment_lists table
class payment_list(models.Model):
    pay_id = models.BigAutoField(primary_key=True, default=1110000000000, editable=False, db_index=True)
    inv_id = models.ForeignKey(invoice_list, null=True, blank=True, on_delete=models.DO_NOTHING, db_index=True)
    pay_date = models.DateField(default=datetime.now, editable=False, db_index=True)
    pay_mode = models.CharField(max_length=10, null=True, blank=True, db_index=True)
    collection_mode = models.CharField(max_length=10, null=True, blank=True, db_index=True)
    pay_amt = models.FloatField(default=0, blank=True)
    given_amt = models.FloatField(default=0, blank=True)
    change_amt = models.FloatField(default=0, blank=True)
    card_info = models.CharField(max_length=50, null=True, blank=True)
    pay_mob_number = models.CharField(max_length=50, null=True, blank=True)
    pay_reference = models.CharField(max_length=50, null=True, blank=True)
    bank_name = models.CharField(max_length=50, null=True, blank=True)
    remarks = models.CharField(max_length=150, null=True, blank=True)
    descriptions = models.CharField(max_length=150, null=True, blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2payment', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(editable=False, null=True, blank=True, db_index=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1271000000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2payment', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True, db_index=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=112720000000, editable=False)
    
    class Meta:
        indexes = [
            models.Index(fields=['inv_id', 'pay_date']),
            models.Index(fields=['pay_mode']),
        ]
    
    def save(self, *args, **kwargs):
        if self._state.adding:
            dhaka_tz = tz('Asia/Dhaka')
            self.ss_created_on = timezone.now().astimezone(dhaka_tz)

            # Autoincrement IDs and session fields
            last_order = payment_list.objects.latest('pay_id') if payment_list.objects.exists() else None
            last_user_session = payment_list.objects.latest('ss_created_session') if payment_list.objects.exists() else None
            last_modifier_session = payment_list.objects.latest('ss_modified_session') if payment_list.objects.exists() else None

            self.pay_id = last_order.pay_id + 1 if last_order else 1110000000000
            self.ss_created_session = last_user_session.ss_created_session + 1 if last_user_session else 1271000000000
            self.ss_modified_session = last_modifier_session.ss_modified_session + 1 if last_modifier_session else 112720000000

        super().save(*args, **kwargs)


    def __str__(self):
        return str(self.pay_id)

# Rent/Others Exps table
class rent_others_exps(models.Model):
    other_exps_id = models.BigAutoField(primary_key=True, default=1321000000000, editable=False, db_index=True)
    inv_id = models.ForeignKey(invoice_list, null=True, blank=True, on_delete=models.DO_NOTHING, db_index=True)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2other_exps', on_delete=models.DO_NOTHING, db_index=True)
    branch_id = models.ForeignKey(branchslist, null=True, blank=True, related_name='branch_id2other_exps', on_delete=models.DO_NOTHING, db_index=True)
    other_exps_reason = models.CharField(max_length=100, null=True, blank=True)
    other_exps_date = models.DateField(default=datetime.now, editable=False, db_index=True)
    is_seller = models.BooleanField(default=False)
    is_buyer = models.BooleanField(default=False)
    other_exps_amt = models.FloatField(default=0, blank=True)
    is_carrying_cost = models.BooleanField(default=False)
    is_canceled = models.BooleanField(default=False)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2other_exps', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(editable=False, null=True, blank=True, db_index=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1575000000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2other_exps', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True, db_index=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=137720000000, editable=False)

    class Meta:
        indexes = [
            models.Index(fields=['org_id', 'branch_id', 'other_exps_date']),
        ]
        
    def save(self, *args, **kwargs):
        if self._state.adding:
            dhaka_tz = tz('Asia/Dhaka')
            self.ss_created_on = timezone.now().astimezone(dhaka_tz)

            # Autoincrement IDs and session fields
            last_order = rent_others_exps.objects.latest('other_exps_id') if rent_others_exps.objects.exists() else None
            last_user_session = rent_others_exps.objects.latest('ss_created_session') if rent_others_exps.objects.exists() else None
            last_modifier_session = rent_others_exps.objects.latest('ss_modified_session') if rent_others_exps.objects.exists() else None

            self.other_exps_id = last_order.other_exps_id + 1 if last_order else 1321000000000
            self.ss_created_session = last_user_session.ss_created_session + 1 if last_user_session else 1575000000000
            self.ss_modified_session = last_modifier_session.ss_modified_session + 1 if last_modifier_session else 137720000000

        super().save(*args, **kwargs)


    def __str__(self):
        return str(self.other_exps_id)

# carrying cost payment table
class carrying_cost_payments(models.Model):
    c_cost_id = models.BigAutoField(primary_key=True, default=4411220000000, editable=False, db_index=True)
    c_cost_date = models.DateField(default=datetime.now, editable=False, db_index=True)
    pay_inv_date = models.DateField(null=True, blank=True, db_index=True)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2c_cost_pay', on_delete=models.DO_NOTHING, db_index=True)
    branch_id = models.ForeignKey(branchslist, null=True, blank=True, related_name='branch_id2c_cost_pay', on_delete=models.DO_NOTHING, db_index=True)
    driver_id = models.ForeignKey(drivers_list, null=True, blank=True, related_name='driver_id2c_cost_pay', on_delete=models.DO_NOTHING, db_index=True)
    c_cost_amt = models.FloatField(default=0, blank=True)
    is_canceled = models.BooleanField(default=False)
    descriptions = models.CharField(max_length=100, null=True, blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2c_cost_pay', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(editable=False, null=True, blank=True, db_index=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=5577880000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2c_cost_pay', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True, db_index=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=6688990000000, editable=False)

    class Meta:
        indexes = [
            models.Index(fields=['org_id', 'branch_id', 'c_cost_date']),
        ]
    
    def save(self, *args, **kwargs):
        if self._state.adding:
            dhaka_tz = tz('Asia/Dhaka')
            self.ss_created_on = timezone.now().astimezone(dhaka_tz)

            # Autoincrement IDs and session fields
            last_order = carrying_cost_payments.objects.latest('c_cost_id') if carrying_cost_payments.objects.exists() else None
            last_user_session = carrying_cost_payments.objects.latest('ss_created_session') if carrying_cost_payments.objects.exists() else None
            last_modifier_session = carrying_cost_payments.objects.latest('ss_modified_session') if carrying_cost_payments.objects.exists() else None

            self.c_cost_id = last_order.c_cost_id + 1 if last_order else 4411220000000
            self.ss_created_session = last_user_session.ss_created_session + 1 if last_user_session else 5577880000000
            self.ss_modified_session = last_modifier_session.ss_modified_session + 1 if last_modifier_session else 6688990000000

        super().save(*args, **kwargs)


    def __str__(self):
        return str(self.c_cost_id)

# item_fav_list table
class item_fav_list(models.Model):
    fav_id = models.BigAutoField(primary_key=True, default=129120000000, editable=False, db_index=True)
    item_id = models.ForeignKey(items, null=True, blank=True, related_name='item_id2item_fav_list', on_delete=models.DO_NOTHING, editable=False, db_index=True)
    user_id = models.ForeignKey(User, null=True, blank=True, related_name='user_id2item_fav_list', on_delete=models.DO_NOTHING, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['item_id', 'user_id']),
        ]

    def __str__(self):
        return str(self.fav_id)
    
    def save(self, *args, **kwargs):
        
        fav_data = item_fav_list.objects.all()

        if fav_data.exists() and self._state.adding:
            last_orderdtl = fav_data.latest('fav_id')
            self.fav_id = int(last_orderdtl.fav_id) + 1
            
        super().save(*args, **kwargs)

# reward_points table
class reward_points(models.Model):
    reward_id = models.BigAutoField(primary_key=True, default=2412000000000, editable=False, db_index=True)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2reward_point', on_delete=models.DO_NOTHING, db_index=True)
    branch_id = models.ForeignKey(branchslist, null=True, blank=True, related_name='branch_id2reward_point', on_delete=models.DO_NOTHING, db_index=True)
    reg_id = models.ForeignKey(in_registrations, null=True, blank=True, related_name='reg_id2reward_point', on_delete=models.DO_NOTHING, editable=False, db_index=True)
    reward_balance = models.FloatField(default=0, blank=True)
    is_canceled = models.BooleanField(default=False, db_index=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2reward_point', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(editable=False, null=True, blank=True, db_index=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1285300000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2reward_point', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True, db_index=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=1296400000000, editable=False)


    class Meta:
        indexes = [
            models.Index(fields=['org_id', 'branch_id', 'reg_id']),
        ]
    
    def save(self, *args, **kwargs):
        if self._state.adding:
            dhaka_tz = tz('Asia/Dhaka')
            self.ss_created_on = timezone.now().astimezone(dhaka_tz)

            # Autoincrement IDs and session fields
            last_order = reward_points.objects.latest('reward_id') if reward_points.objects.exists() else None
            last_user_session = reward_points.objects.latest('ss_created_session') if reward_points.objects.exists() else None
            last_modifier_session = reward_points.objects.latest('ss_modified_session') if reward_points.objects.exists() else None

            self.reward_id = last_order.reward_id + 1 if last_order else 2412000000000
            self.ss_created_session = last_user_session.ss_created_session + 1 if last_user_session else 1285300000000
            self.ss_modified_session = last_modifier_session.ss_modified_session + 1 if last_modifier_session else 1296400000000

        super().save(*args, **kwargs)


    def __str__(self):
        return str(self.reward_id)

# reward_pointsdtls table
class reward_pointsdtls(models.Model):
    rewarddtls_id = models.BigAutoField(primary_key=True, default=3312000000000, editable=False, db_index=True)
    inv_id = models.ForeignKey(invoice_list, null=True, blank=True, on_delete=models.DO_NOTHING, db_index=True)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2reward_dtls_point', on_delete=models.DO_NOTHING, db_index=True)
    branch_id = models.ForeignKey(branchslist, null=True, blank=True, related_name='branch_id2reward_dtls_point', on_delete=models.DO_NOTHING, db_index=True)
    reg_id = models.ForeignKey(in_registrations, null=True, blank=True, related_name='reg_id2reward_dtls_point', on_delete=models.DO_NOTHING, editable=False, db_index=True)
    reward_dtls_date = models.DateField(default=datetime.now, editable=False, db_index=True)
    reward_dtls_balance = models.FloatField(default=0, blank=True)
    is_canceled = models.BooleanField(default=False, db_index=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2reward_dtls_point', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(editable=False, null=True, blank=True, db_index=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=2335300000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2reward_dtls_point', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True, db_index=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=3576400000000, editable=False)

    class Meta:
        indexes = [
            models.Index(fields=['org_id', 'branch_id', 'reward_dtls_date']),
        ]
    
    def save(self, *args, **kwargs):
        if self._state.adding:
            dhaka_tz = tz('Asia/Dhaka')
            self.ss_created_on = timezone.now().astimezone(dhaka_tz)

            # Autoincrement IDs and session fields
            last_order = reward_pointsdtls.objects.latest('rewarddtls_id') if reward_pointsdtls.objects.exists() else None
            last_user_session = reward_pointsdtls.objects.latest('ss_created_session') if reward_pointsdtls.objects.exists() else None
            last_modifier_session = reward_pointsdtls.objects.latest('ss_modified_session') if reward_pointsdtls.objects.exists() else None

            self.rewarddtls_id = last_order.rewarddtls_id + 1 if last_order else 3312000000000
            self.ss_created_session = last_user_session.ss_created_session + 1 if last_user_session else 2335300000000
            self.ss_modified_session = last_modifier_session.ss_modified_session + 1 if last_modifier_session else 3576400000000

        super().save(*args, **kwargs)


    def __str__(self):
        return str(self.rewarddtls_id)
    
# without_invoice_collection table
class without_invoice_collection(models.Model):
    wo_coll_id = models.BigAutoField(primary_key=True, default=2000220020000, editable=False, db_index=True)
    coll_date = models.DateField(default=datetime.now, editable=False, db_index=True)
    collection_mode = models.CharField(max_length=10, null=True, blank=True, db_index=True)
    collection_type = models.CharField(max_length=10, null=True, blank=True, db_index=True)
    collection_amt = models.FloatField(default=0, blank=True)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2wo_inv_coll', on_delete=models.DO_NOTHING, db_index=True)
    branch_id = models.ForeignKey(branchslist, null=True, blank=True, related_name='branch_id2wo_inv_coll', on_delete=models.DO_NOTHING, db_index=True)
    reg_id = models.ForeignKey(in_registrations, null=True, blank=True, related_name='reg_id2wo_inv_coll', on_delete=models.DO_NOTHING, editable=False, db_index=True)
    customer_name = models.CharField(max_length=100, null=True, blank=True)
    gender = models.CharField(max_length=20, null=True, blank=True)
    customer_mobile = models.CharField(max_length=50, null=True, blank=True)
    house_no = models.CharField(max_length=50, null=True, blank=True)
    floor_no = models.CharField(max_length=50, null=True, blank=True)
    road_no = models.CharField(max_length=50, null=True, blank=True)
    sector_no = models.CharField(max_length=50, null=True, blank=True)
    area = models.CharField(max_length=50, null=True, blank=True)
    order_no = models.CharField(max_length=50, null=True, blank=True)
    side_office_factory = models.CharField(max_length=150, null=True, blank=True)
    address = models.CharField(max_length=250, null=True, blank=True)
    emergency_person = models.CharField(max_length=150, null=True, blank=True)
    emergency_phone = models.CharField(max_length=20, null=True, blank=True)
    descriptions = models.CharField(max_length=150, null=True, blank=True)
    comments = models.CharField(max_length=150, null=True, blank=True)
    card_info = models.CharField(max_length=50, null=True, blank=True)
    mobile_number = models.CharField(max_length=50, null=True, blank=True)
    reference = models.CharField(max_length=50, null=True, blank=True)
    bank_name = models.CharField(max_length=50, null=True, blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2wo_inv_coll', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(editable=False, null=True, blank=True, db_index=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=2344000000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2wo_inv_coll', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True, db_index=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=334560000000, editable=False)


    class Meta:
        indexes = [
            models.Index(fields=['org_id', 'branch_id', 'reg_id', 'coll_date']),
        ]

    def save(self, *args, **kwargs):
        if self._state.adding:
            dhaka_tz = tz('Asia/Dhaka')
            self.ss_created_on = timezone.now().astimezone(dhaka_tz)

            # Autoincrement IDs and session fields
            last_order = without_invoice_collection.objects.latest('wo_coll_id') if without_invoice_collection.objects.exists() else None
            last_user_session = without_invoice_collection.objects.latest('ss_created_session') if without_invoice_collection.objects.exists() else None
            last_modifier_session = without_invoice_collection.objects.latest('ss_modified_session') if without_invoice_collection.objects.exists() else None

            self.wo_coll_id = last_order.wo_coll_id + 1 if last_order else 2000220020000
            self.ss_created_session = last_user_session.ss_created_session + 1 if last_user_session else 2344000000000
            self.ss_modified_session = last_modifier_session.ss_modified_session + 1 if last_modifier_session else 334560000000

        super().save(*args, **kwargs)

    
    def __str__(self):
        return str(self.wo_coll_id)