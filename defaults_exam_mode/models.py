from django.db import models
from organizations.models import organizationlst
from class_setup.models import in_class
from groups_setup.models import in_groups
from section_setup.models import in_section
from shift_setup.models import in_shifts
from subject_setup.models import in_subjects
from django.contrib.auth import get_user_model
User = get_user_model()

# Create your models here.
class in_exam_modes(models.Model):
    exam_mode_id = models.BigAutoField(primary_key=True, default=1647890000000, editable=False)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2exam_modes', on_delete=models.DO_NOTHING)
    class_id = models.ForeignKey(in_class, null=True, blank=True, related_name='class_id2exam_modes', on_delete=models.DO_NOTHING)
    is_exam_modes = models.CharField(max_length=20, null=True, blank=True)
    is_default_marks = models.IntegerField(default=0, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    is_common = models.BooleanField(default=False)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2in_exam_modes', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1936900000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2in_exam_modes', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=134891000000, editable=False)

    def save(self, *args, **kwargs):
        last_data = in_exam_modes.objects.all()

        if last_data.exists() and self._state.adding:
            last_order = last_data.latest('exam_mode_id')
            user_session = last_data.latest('ss_created_session')
            modifier_session = last_data.latest('ss_modified_session')
            self.exam_mode_id = int(last_order.exam_mode_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.exam_mode_id)