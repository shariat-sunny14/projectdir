from django.db import models
from datetime import datetime
from organizations.models import branchslist, organizationlst
from class_setup.models import in_class
from groups_setup.models import in_groups
from section_setup.models import in_section
from shift_setup.models import in_shifts
from exam_type.models import in_exam_type
from registrations.models import in_registrations
from django.contrib.auth import get_user_model
User = get_user_model()


class in_student_attendant(models.Model):
    attendant_id = models.BigAutoField(primary_key=True, default=1003030303000, editable=False)
    trans_date = models.DateField(default=datetime.now, editable=False)
    attendant_year = models.IntegerField(default=datetime.now().year, editable=False)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2in_student_att', on_delete=models.DO_NOTHING)
    branch_id = models.ForeignKey(branchslist, null=True, blank=True, related_name='branch_id2in_student_att', on_delete=models.DO_NOTHING)
    class_id = models.ForeignKey(in_class, null=True, blank=True, related_name='class_id2in_student_att', on_delete=models.DO_NOTHING)
    section_id = models.ForeignKey(in_section, null=True, blank=True, related_name='section_id2in_student_att', on_delete=models.DO_NOTHING)
    shifts_id = models.ForeignKey(in_shifts, null=True, blank=True, related_name='shifts_id2in_student_att', on_delete=models.DO_NOTHING)
    groups_id = models.ForeignKey(in_groups, null=True, blank=True, related_name='groups_id2in_student_att', on_delete=models.DO_NOTHING)
    exam_type_id = models.ForeignKey(in_exam_type, null=True, blank=True, related_name='exam_type_id2in_student_att', on_delete=models.DO_NOTHING)
    working_days = models.IntegerField(default=0, null=True, blank=True)
    is_half_yearly = models.BooleanField(default=False)
    is_yearly = models.BooleanField(default=False)
    is_english = models.BooleanField(default=False)
    is_bangla = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    is_approved_by = models.ForeignKey(User, null=True, blank=True, related_name='user_id2in_student_att', on_delete=models.DO_NOTHING)
    approved_date = models.CharField(max_length=50, null=True, blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2in_student_att', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=10040400400000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2in_student_att', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=1000500505000, editable=False)

    def save(self, *args, **kwargs):
        last_data = in_student_attendant.objects.all()

        if last_data.exists() and self._state.adding:
            last_order = last_data.latest('attendant_id')
            user_session = last_data.latest('ss_created_session')
            modifier_session = last_data.latest('ss_modified_session')
            self.attendant_id = int(last_order.attendant_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.attendant_id)
    


class in_student_attendantdtls(models.Model):
    attendantdtl_id = models.BigAutoField(primary_key=True, default=1000220202000, editable=False)
    trans_date = models.DateField(default=datetime.now, editable=False)
    attendant_year = models.IntegerField(default=datetime.now().year, editable=False)
    attendant_id = models.ForeignKey(in_student_attendant, null=True, blank=True, related_name='attendant_id2in_student_attdtl', on_delete=models.DO_NOTHING)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2in_student_attdtl', on_delete=models.DO_NOTHING)
    branch_id = models.ForeignKey(branchslist, null=True, blank=True, related_name='branch_id2in_student_attdtl', on_delete=models.DO_NOTHING)
    class_id = models.ForeignKey(in_class, null=True, blank=True, related_name='class_id2in_student_attdtl', on_delete=models.DO_NOTHING)
    section_id = models.ForeignKey(in_section, null=True, blank=True, related_name='section_id2in_student_attdtl', on_delete=models.DO_NOTHING)
    shifts_id = models.ForeignKey(in_shifts, null=True, blank=True, related_name='shifts_id2in_student_attdtl', on_delete=models.DO_NOTHING)
    groups_id = models.ForeignKey(in_groups, null=True, blank=True, related_name='groups_id2in_student_attdtl', on_delete=models.DO_NOTHING)
    exam_type_id = models.ForeignKey(in_exam_type, null=True, blank=True, related_name='exam_type_id2in_student_attdtl', on_delete=models.DO_NOTHING)
    reg_id = models.ForeignKey(in_registrations, null=True, blank=True, related_name='reg_id2in_student_attdtl', on_delete=models.DO_NOTHING)
    roll_no = models.CharField(max_length=20, null=True, blank=True)
    class_name = models.CharField(max_length=20, null=True, blank=True)
    section_name = models.CharField(max_length=20, null=True, blank=True)
    shift_name = models.CharField(max_length=20, null=True, blank=True)
    groups_name = models.CharField(max_length=20, null=True, blank=True)
    attendant_qty = models.IntegerField(default=0, null=True, blank=True)
    is_half_yearly = models.BooleanField(default=False)
    is_yearly = models.BooleanField(default=False)
    is_english = models.BooleanField(default=False)
    is_bangla = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    is_approved_by = models.ForeignKey(User, null=True, blank=True, related_name='user_id2in_student_attdtl', on_delete=models.DO_NOTHING)
    approved_date = models.CharField(max_length=50, null=True, blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2in_student_attdtl', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=10000100303000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2in_student_attdtl', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=1000400400400, editable=False)

    def save(self, *args, **kwargs):
        lastdtl_data = in_student_attendantdtls.objects.all()

        if lastdtl_data.exists() and self._state.adding:
            last_order = lastdtl_data.latest('attendantdtl_id')
            user_session = lastdtl_data.latest('ss_created_session')
            modifier_session = lastdtl_data.latest('ss_modified_session')
            self.attendantdtl_id = int(last_order.attendantdtl_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.attendantdtl_id)