from django.db import models
from django.db.models import Max
from django.contrib.auth import get_user_model
User = get_user_model()

class InquiresList(models.Model):

    inquire_id = models.BigAutoField(primary_key=True, default=4999000000001, editable=False)
    inquire_date = models.DateField(auto_now_add=True)
    
    ss_creator = models.ForeignKey(
        User, null=True, blank=True,
        related_name='ss_creator2inquire',
        on_delete=models.DO_NOTHING,
        editable=False
    )

    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=4999000010000)

    ss_modifier = models.ForeignKey(
        User, null=True, blank=True,
        related_name='ss_modifier2inquire',
        on_delete=models.DO_NOTHING
    )

    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=4999000020000)

    # FORM DATA
    inquire_type = models.JSONField(default=list)  # inquire_type[]
    your_questions = models.TextField(blank=True, null=True)
    your_planned = models.TextField(blank=True, null=True)

    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone_number = models.CharField(max_length=50)

    discover_type = models.JSONField(default=list)

    comments = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "inquires_list"
        ordering = ['-ss_created_on']

    def __str__(self):
        return f"{self.full_name} - {self.inquire_id}"

    def save(self, *args, **kwargs):

        if self._state.adding:
            last = InquiresList.objects.order_by('-inquire_id').first()

            if last:
                self.inquire_id = int(last.inquire_id) + 1
                self.ss_created_session = int(last.ss_created_session) + 1
                self.ss_modified_session = int(last.ss_modified_session) + 1

        super().save(*args, **kwargs)