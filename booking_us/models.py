from django.db import models
from django.db.models import Max
from django.contrib.auth import get_user_model
User = get_user_model()


class Slot_Details(models.Model):
    slot_id = models.BigIntegerField(primary_key=True, editable=False)
    slot_name = models.CharField(max_length=150, null=True, blank=True)
    from_time = models.TimeField(null=True, blank=True)
    to_time = models.TimeField(null=True, blank=True)
    is_full_day = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2slotdtl', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2slotdtl', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, editable=False)

    def save(self, *args, **kwargs):
        if self._state.adding:
            # Calculate next slot_id
            last_slot = Slot_Details.objects.aggregate(max_slot=Max('slot_id'))['max_slot']
            self.slot_id = last_slot + 1 if last_slot else 1780007000001

            # Calculate next session numbers
            last_created_session = Slot_Details.objects.aggregate(max_created=Max('ss_created_session'))['max_created']
            last_modified_session = Slot_Details.objects.aggregate(max_modified=Max('ss_modified_session'))['max_modified']

            self.ss_created_session = (last_created_session + 1) if last_created_session else 1149000010000
            self.ss_modified_session = (last_modified_session + 1) if last_modified_session else 1442000020000

        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.slot_id)

    class Meta:
        db_table = "slot_details"
        ordering = ['-slot_id']


class EventSchedule(models.Model):

    STATUS_CHOICES = (
        ('Free', 'Free'),
        ('Booked', 'Booked'),
    )
    
    schedule_id = models.BigAutoField(primary_key=True, default=1999000000001, editable=False)
    slot_id = models.ForeignKey(Slot_Details, null=True, blank=True, related_name='slot_id2schedule', on_delete=models.CASCADE)
    event_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Free')
    is_active = models.BooleanField(default=True)
    # ===== Tracking Fields (Same as packages_list) =====
    ss_creator = models.ForeignKey( User, null=True, blank=True, related_name='ss_creator2schedule', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=2999000010000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2schedule', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=2999000020000, editable=False)

    # ===== Custom Save (Same Logic Pattern) =====
    def save(self, *args, **kwargs):

        last_data = EventSchedule.objects.all()

        if last_data.exists() and self._state.adding:
            last_order = last_data.latest('schedule_id')
            user_session = last_data.latest('ss_created_session')
            modifier_session = last_data.latest('ss_modified_session')

            self.schedule_id = int(last_order.schedule_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.schedule_id} - {self.event_date} - {self.slot_id.slot_name if self.slot_id else 'No Slot'} - {self.status}"

    class Meta:
        db_table = "event_schedule"
        ordering = ['-event_date']
        unique_together = ('event_date', 'slot_id')