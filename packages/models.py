import os
from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()
# Create your models here.

class packages_items(models.Model):
    pitem_id = models.BigAutoField(primary_key=True, default=1550005000001, editable=False)
    pitem_name = models.CharField(max_length=150, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2pitem', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1135000010000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2pitem', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=1575000020000, editable=False)

    def save(self, *args, **kwargs):
        last_data = packages_items.objects.all()

        if last_data.exists() and self._state.adding:
            last_order = last_data.latest('pitem_id')
            user_session = last_data.latest('ss_created_session')
            modifier_session = last_data.latest('ss_modified_session')
            self.pitem_id = int(last_order.pitem_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.pitem_id)
    
    

class packages_head_body(models.Model):
    phb_id = models.BigAutoField(primary_key=True, default=1900000000001, editable=False)
    head_name = models.CharField(max_length=150, null=True, blank=True)
    body_text = models.CharField(max_length=1000, null=True, blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2phb', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1192000010000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2phb', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=1293000020000, editable=False)

    def save(self, *args, **kwargs):
        last_data = packages_head_body.objects.all()

        if last_data.exists() and self._state.adding:
            last_order = last_data.latest('phb_id')
            user_session = last_data.latest('ss_created_session')
            modifier_session = last_data.latest('ss_modified_session')
            self.phb_id = int(last_order.phb_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.phb_id)
    
    

class packages_list(models.Model):
    package_id = models.BigAutoField(primary_key=True, default=1550000000001, editable=False)
    package_title = models.CharField(max_length=150, null=True, blank=True)
    package_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_package_price = models.BooleanField(default=False)
    offer_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_offer_price = models.BooleanField(default=False)
    title_caption = models.CharField(max_length=1000, null=True, blank=True)
    title_img = models.ImageField(upload_to='title_imgage', max_length=255, null=True, blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2package', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1772000010000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2package', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=1255000020000, editable=False)

    def save(self, *args, **kwargs):
        last_data = packages_list.objects.all()

        if last_data.exists() and self._state.adding:
            last_order = last_data.latest('package_id')
            user_session = last_data.latest('ss_created_session')
            modifier_session = last_data.latest('ss_modified_session')
            self.package_id = int(last_order.package_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.package_id)



class packages_dtls(models.Model):
    packagedtls_id = models.BigAutoField(primary_key=True, default=1482000000001, editable=False)
    package_id = models.ForeignKey(packages_list, null=True, blank=True, related_name='packages2packagedtls', on_delete=models.CASCADE)
    pitem_id = models.ForeignKey(packages_items, null=True, blank=True, related_name='pitem_id2packagedtls', on_delete=models.CASCADE)
    order_no = models.IntegerField(null=True, blank=True)
    elements_drescription = models.CharField(max_length=2500, null=True, blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2packagedtls', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1568000010000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2packagedtls', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=1176000020000, editable=False)

    def save(self, *args, **kwargs):
        last_data = packages_dtls.objects.all()

        if last_data.exists() and self._state.adding:
            last_order = last_data.latest('packagedtls_id')
            user_session = last_data.latest('ss_created_session')
            modifier_session = last_data.latest('ss_modified_session')
            self.packagedtls_id = int(last_order.packagedtls_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.packagedtls_id)