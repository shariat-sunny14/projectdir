from django.db import models
from datetime import datetime, date
from django.db.models import Max
from defaults_exam_mode.models import defaults_exam_modes
from organizations.models import branchslist, organizationlst
from class_setup.models import in_class
from groups_setup.models import in_groups
from section_setup.models import in_section
from shift_setup.models import in_shifts
from registrations.models import in_registrations
from subject_setup.models import in_subjects
from django.contrib.auth import get_user_model
User = get_user_model()



class in_merit_position_approval(models.Model):
    merit_id = models.BigAutoField(primary_key=True, default=1009900900001, editable=False)
    created_date = models.DateField(default=datetime.now, editable=False)
    merit_year = models.IntegerField(default=datetime.now().year, editable=False)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2merit_position', on_delete=models.DO_NOTHING)
    branch_id = models.ForeignKey(branchslist, null=True, blank=True, related_name='branch_id2merit_position', on_delete=models.DO_NOTHING)
    class_id = models.ForeignKey(in_class, null=True, blank=True, related_name='class_id2merit_position', on_delete=models.DO_NOTHING)
    section_id = models.ManyToManyField(in_section, null=True, blank=True, related_name='section_id2merit_position')
    shifts_id = models.ForeignKey(in_shifts, null=True, blank=True, related_name='shifts_id2merit_position', on_delete=models.DO_NOTHING)
    groups_id = models.ForeignKey(in_groups, null=True, blank=True, related_name='groups_id2merit_position', on_delete=models.DO_NOTHING)
    is_half_yearly = models.BooleanField(default=False)
    is_yearly = models.BooleanField(default=False)
    is_english = models.BooleanField(default=False)
    is_bangla = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    is_approved_by = models.ForeignKey(User, null=True, blank=True, related_name='user_id2merit_position', on_delete=models.DO_NOTHING)
    approved_date = models.CharField(max_length=50, null=True, blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2merit_position', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1000450900000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2merit_position', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=1000400506000, editable=False)

    def save(self, *args, **kwargs):
        trans_data = in_merit_position_approval.objects.all()

        if trans_data.exists() and self._state.adding:
            last_order = trans_data.latest('merit_id')
            user_session = trans_data.latest('ss_created_session')
            modifier_session = trans_data.latest('ss_modified_session')
            self.merit_id = int(last_order.merit_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.merit_id)


class in_merit_position_approvaldtls(models.Model):
    meritdtl_id = models.BigAutoField(primary_key=True, default=1005600000001, editable=False)
    created_date = models.DateField(default=datetime.now, editable=False)
    merit_year = models.IntegerField(default=datetime.now().year, editable=False)
    merit_id = models.ForeignKey(in_merit_position_approval, null=True, blank=True, related_name='merit_id2merit_positiondtls', on_delete=models.DO_NOTHING)
    reg_id = models.ForeignKey(in_registrations, null=True, blank=True, related_name='reg_id2merit_positiondtls', on_delete=models.DO_NOTHING)
    roll_no = models.CharField(max_length=20, null=True, blank=True)
    merit_position = models.IntegerField(null=True, blank=True, default=0)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2merit_positiondtls', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=10000900300000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2merit_positiondtls', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=10001036800000, editable=False)

    def save(self, *args, **kwargs):
        trans_data = in_merit_position_approvaldtls.objects.all()

        if trans_data.exists() and self._state.adding:
            last_order = trans_data.latest('meritdtl_id')
            user_session = trans_data.latest('ss_created_session')
            modifier_session = trans_data.latest('ss_modified_session')
            self.meritdtl_id = int(last_order.meritdtl_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.meritdtl_id)