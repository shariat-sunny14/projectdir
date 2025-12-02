from django.db import models
from organizations.models import organizationlst
from django.contrib.auth import get_user_model
User = get_user_model()


class in_exam_type(models.Model):
    exam_type_id = models.BigAutoField(primary_key=True, default=1255330000000, editable=False)
    exam_type_no = models.CharField(max_length=50, null=True, blank=True)
    exam_type_name = models.CharField(max_length=100, null=True, blank=True)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2in_exam_type', on_delete=models.DO_NOTHING)
    is_half_yearly = models.BooleanField(default=False)
    is_yearly = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2in_exam_type', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=16631000000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2in_exam_type', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=177710000000, editable=False)

    def save(self, *args, **kwargs):
        last_data = in_exam_type.objects.all()

        if last_data.exists() and self._state.adding:
            last_order = last_data.latest('exam_type_id')
            user_session = last_data.latest('ss_created_session')
            modifier_session = last_data.latest('ss_modified_session')
            self.exam_type_id = int(last_order.exam_type_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.exam_type_id)