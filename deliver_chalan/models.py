from django.db import models
from datetime import datetime
from django.utils import timezone
from pytz import timezone as tz
from organizations.models import branchslist, organizationlst
from item_pos.models import invoice_list, invoicedtl_list
from store_setup.models import store
from item_setup.models import items
from drivers_setup.models import drivers_list
from registrations.models import in_registrations
from django.contrib.auth import get_user_model
User = get_user_model()


# Create your models here.
class delivery_Chalan_list(models.Model):
    chalan_id = models.BigAutoField(primary_key=True, default=1000000011000, editable=False)
    create_date = models.DateField(default=datetime.now, editable=False)
    inv_id = models.ForeignKey(invoice_list, null=True, blank=True, related_name='inv_id2chalan', on_delete=models.DO_NOTHING)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2chalan', on_delete=models.DO_NOTHING)
    branch_id = models.ForeignKey(branchslist, null=True, blank=True, related_name='branch_id2chalan', on_delete=models.DO_NOTHING)
    is_created = models.BooleanField(default=False)
    is_update = models.BooleanField(default=False)
    is_modified_item = models.BooleanField(default=False)
    is_out_sourceing = models.BooleanField(default=False)
    is_direct_or_hold = models.BooleanField(default=False)
    is_hold_approve = models.BooleanField(default=False)
    is_manual_chalan = models.BooleanField(default=False)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2chalan', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(editable=False, null=True, blank=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1277800008000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2chalan', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=112888001000, editable=False)

    def save(self, *args, **kwargs):
        if self._state.adding:
            dhaka_tz = tz('Asia/Dhaka')
            self.ss_created_on = timezone.now().astimezone(dhaka_tz)

            # Autoincrement IDs and session fields
            last_order = delivery_Chalan_list.objects.latest('chalan_id') if delivery_Chalan_list.objects.exists() else None
            last_user_session = delivery_Chalan_list.objects.latest('ss_created_session') if delivery_Chalan_list.objects.exists() else None
            last_modifier_session = delivery_Chalan_list.objects.latest('ss_modified_session') if delivery_Chalan_list.objects.exists() else None

            self.chalan_id = last_order.chalan_id + 1 if last_order else 1000000011000
            self.ss_created_session = last_user_session.ss_created_session + 1 if last_user_session else 1277800008000
            self.ss_modified_session = last_modifier_session.ss_modified_session + 1 if last_modifier_session else 112888001000

        super().save(*args, **kwargs)

    
    def __str__(self):
        return str(self.chalan_id)


# delivery_Chalandtl_list table
class delivery_Chalandtl_list(models.Model):
    chanaldtl_id = models.BigAutoField(primary_key=True, default=2223400000000, editable=False)
    del_chalan_date = models.DateField(null=True, blank=True)
    chalan_id = models.ForeignKey(delivery_Chalan_list, null=True, blank=True, on_delete=models.DO_NOTHING)
    inv_id = models.ForeignKey(invoice_list, null=True, blank=True, related_name='inv_id2chalandtl', on_delete=models.DO_NOTHING)
    invdtl_id = models.ForeignKey(invoicedtl_list, null=True, blank=True, related_name='invdtl_id2chalandtl', on_delete=models.DO_NOTHING)
    item_id = models.ForeignKey(items, null=True, blank=True, related_name='item_id2chalandtl', on_delete=models.DO_NOTHING, editable=False)
    deliver_store = models.ForeignKey(store, null=True, blank=True, related_name='deliver_store2chalandtl', on_delete=models.DO_NOTHING, editable=False)
    deliver_qty = models.FloatField(default=0, blank=True)
    is_cancel_qty = models.FloatField(default=0, blank=True)
    is_out_sourceing = models.BooleanField(default=False, blank=True)
    is_direct_or_hold = models.BooleanField(default=False, blank=True)
    is_hold_approve = models.BooleanField(default=False, blank=True)
    is_extra_item = models.BooleanField(default=False, null=True, blank=True)
    is_update = models.BooleanField(default=False)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2chalandtl', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(editable=False, null=True, blank=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1667900000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2chalandtl', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=778910000000, editable=False)


    def save(self, *args, **kwargs):

        if self._state.adding:
            dhaka_tz = tz('Asia/Dhaka')
            self.ss_created_on = timezone.now().astimezone(dhaka_tz)

            # Autoincrement IDs and session fields
            last_order = delivery_Chalandtl_list.objects.latest('chanaldtl_id') if delivery_Chalandtl_list.objects.exists() else None
            last_user_session = delivery_Chalandtl_list.objects.latest('ss_created_session') if delivery_Chalandtl_list.objects.exists() else None
            last_modifier_session = delivery_Chalandtl_list.objects.latest('ss_modified_session') if delivery_Chalandtl_list.objects.exists() else None

            self.chanaldtl_id = last_order.chanaldtl_id + 1 if last_order else 2223400000000
            self.ss_created_session = last_user_session.ss_created_session + 1 if last_user_session else 1667900000000
            self.ss_modified_session = last_modifier_session.ss_modified_session + 1 if last_modifier_session else 778910000000

        # Ensure 'is_extra_item' always has a value (set to False if not provided)
        if self.is_extra_item is None:
            self.is_extra_item = False

        if self.is_update is None:
            self.is_update = False

        super().save(*args, **kwargs)

    
    def __str__(self):
        return str(self.chanaldtl_id)


# manual delivery client info table
class manual_delivery_info(models.Model):
    del_info_id = models.BigAutoField(primary_key=True, default=9990101000000, editable=False)
    delivery_date = models.DateField(default=datetime.now, editable=False)
    is_non_register = models.BooleanField(default=False)
    is_register = models.BooleanField(default=False)
    chalan_id = models.ForeignKey(delivery_Chalan_list, null=True, blank=True, related_name='chalan_id2mdeli_info', on_delete=models.DO_NOTHING)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2mdeli_info', on_delete=models.DO_NOTHING)
    branch_id = models.ForeignKey(branchslist, null=True, blank=True, related_name='branch_id2mdeli_info', on_delete=models.DO_NOTHING)
    cash_point = models.ForeignKey(store, null=True, blank=True, related_name='store_id2mdeli_info', on_delete=models.DO_NOTHING, editable=False)
    reg_id = models.ForeignKey(in_registrations, null=True, blank=True, related_name='reg_id2mdeli_info', on_delete=models.DO_NOTHING, editable=False)
    driver_id = models.ForeignKey(drivers_list, null=True, blank=True, related_name='driver_id2mdeli_info', on_delete=models.DO_NOTHING, editable=False)
    driver_name = models.CharField(max_length=100, null=True, blank=True)
    driver_mobile = models.CharField(max_length=20, null=True, blank=True)
    customer_name = models.CharField(max_length=100, null=True, blank=True)
    gender = models.CharField(max_length=20, null=True, blank=True)
    mobile_number = models.CharField(max_length=50, null=True, blank=True)
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
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2mdeli_info', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(editable=False, null=True, blank=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1999000000100, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2mdeli_info', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=1999000000110, editable=False)


    def save(self, *args, **kwargs):
        if self._state.adding:
            dhaka_tz = tz('Asia/Dhaka')
            self.ss_created_on = timezone.now().astimezone(dhaka_tz)

            # Autoincrement IDs and session fields
            last_order = manual_delivery_info.objects.latest('del_info_id') if manual_delivery_info.objects.exists() else None
            last_user_session = manual_delivery_info.objects.latest('ss_created_session') if manual_delivery_info.objects.exists() else None
            last_modifier_session = manual_delivery_info.objects.latest('ss_modified_session') if manual_delivery_info.objects.exists() else None

            self.del_info_id = last_order.del_info_id + 1 if last_order else 9990101000000
            self.ss_created_session = last_user_session.ss_created_session + 1 if last_user_session else 1999000000100
            self.ss_modified_session = last_modifier_session.ss_modified_session + 1 if last_modifier_session else 1999000000110

        super().save(*args, **kwargs)

    
    def __str__(self):
        return str(self.del_info_id)