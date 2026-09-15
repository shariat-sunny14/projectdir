from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model
from booking_us.models import EventSchedule
from packages.models import packages_list

User = get_user_model()


class OrderList(models.Model):
    # =============================
    # Primary key & session tracking
    # =============================
    order_id = models.BigAutoField(primary_key=True, default=3999000000001, editable=False)
    order_date = models.DateField(auto_now_add=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2order', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=3999000010000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2order', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=3999000020000, editable=False)

    # =============================
    # Step 1: Shoot Types (multiple choice)
    # =============================
    shoot_type = models.JSONField(default=list)

    # =============================
    # Step 2: Selected Schedule (Many schedules possible)
    # =============================
    schedule_id = models.ManyToManyField(EventSchedule, blank=True, related_name='schedule_id2orderlst')

    # =============================
    # Step 3–10: Venue, guest number, about, name, email, phone, plans
    # =============================
    venue_name = models.CharField(max_length=255)
    guest_number = models.CharField(max_length=50)
    about_you = models.TextField(blank=True, null=True)
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone_number = models.CharField(max_length=50)
    your_planned = models.TextField(blank=True, null=True)

    # =============================
    # Step 11: Other photographer
    # =============================
    is_other_photographer = models.BooleanField(default=False)

    # =============================
    # Step 12: How did you discover
    # =============================
    discover_type = models.JSONField(default=list)

    # =============================
    # Step 13: Comments
    # =============================
    comments = models.TextField(blank=True, null=True)

    # =============================
    # Packages (ManyToMany through)
    # =============================
    package_id = models.ManyToManyField(packages_list, blank=True, related_name='package_id2orderlst', through='OrderPackagePrice')

    class Meta:
        db_table = "order_list"
        ordering = ['-ss_created_on']

    def __str__(self):
        return f"{self.full_name} - Order #{self.order_id}"

    def save(self, *args, **kwargs):
        if self._state.adding:
            last_order = OrderList.objects.all().order_by('-order_id').first()
            if last_order:
                self.order_id = int(last_order.order_id) + 1
                self.ss_created_session = int(last_order.ss_created_session) + 1
                self.ss_modified_session = int(last_order.ss_modified_session) + 1
        super().save(*args, **kwargs)

    @property
    def total_package_price(self):
        total = Decimal('0.00')
        for op in self.orderpackageprice_set.all():
            if op.package_price:
                total += op.package_price
        return total


class OrderPackagePrice(models.Model):
    """
    Through model to store individual package price for each order.
    """
    order_id = models.ForeignKey(OrderList, on_delete=models.DO_NOTHING)
    package_id = models.ForeignKey(packages_list, on_delete=models.DO_NOTHING)
    package_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "order_package_price"