import os
from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()

class EnrollList(models.Model):
    enroll_id = models.BigAutoField(primary_key=True, default=1750000700001, editable=False)
    enroll_title = models.CharField(max_length=150, null=True, blank=True)
    enroll_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_enroll_price = models.BooleanField(default=False)
    offer_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_offer_price = models.BooleanField(default=False)
    enroll_caption = models.CharField(max_length=1000, null=True, blank=True)
    is_most_popular = models.BooleanField(default=False)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2enroll', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1750000800001, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2enroll', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=1750000900001, editable=False)

    def save(self, *args, **kwargs):
        last_data = EnrollList.objects.all()

        if last_data.exists() and self._state.adding:
            last_order = last_data.latest('enroll_id')
            user_session = last_data.latest('ss_created_session')
            modifier_session = last_data.latest('ss_modified_session')
            self.enroll_id = int(last_order.enroll_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.enroll_id)
    
    class Meta:
        db_table = "enroll_list"
        ordering = ['-enroll_id']



class EnrollDetails(models.Model):
    enrolldtls_id = models.BigAutoField(primary_key=True, default=1678000600001, editable=False)
    enroll_id = models.ForeignKey(EnrollList, null=True, blank=True, related_name='enroll2enrolldtls', on_delete=models.CASCADE)
    order_no = models.IntegerField(null=True, blank=True)
    enroll_dtls = models.CharField(max_length=2500, null=True, blank=True)
    is_published = models.BooleanField(default=False)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2enrolldtls', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1678000700001, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2enrolldtls', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=1678000800001, editable=False)

    def save(self, *args, **kwargs):
        last_data = EnrollDetails.objects.all()

        if last_data.exists() and self._state.adding:
            last_order = last_data.latest('enrolldtls_id')
            user_session = last_data.latest('ss_created_session')
            modifier_session = last_data.latest('ss_modified_session')
            self.enrolldtls_id = int(last_order.enrolldtls_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.enrolldtls_id)
    
    class Meta:
        db_table = "enroll_details"
        ordering = ['-enrolldtls_id']



class EnrollBookingDtls(models.Model):
    booking_id = models.BigAutoField(primary_key=True)

    enroll = models.ForeignKey(
        EnrollList,
        on_delete=models.CASCADE,
        related_name='enroll_bookings'
    )

    full_name = models.CharField(max_length=200)
    mobile_no = models.CharField(max_length=20)
    email = models.EmailField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    
    course_amt = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2enrollbooking', on_delete=models.DO_NOTHING, editable=False)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1678000900001, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2enrollbooking', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} - {self.enroll.enroll_title}"

    class Meta:
        db_table = "enroll_booking_dtls"