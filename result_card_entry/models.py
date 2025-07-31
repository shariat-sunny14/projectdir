from django.db import models
from datetime import datetime, date
from django.db.models import Max
from organizations.models import branchslist, organizationlst
from class_setup.models import in_class
from groups_setup.models import in_groups
from section_setup.models import in_section
from shift_setup.models import in_shifts
from registrations.models import in_registrations
from subject_setup.models import in_subjects
from django.contrib.auth import get_user_model
User = get_user_model()


class in_results_card_entry(models.Model):
    res_card_id = models.BigAutoField(primary_key=True, default=1003300000001, editable=False)
    trans_date = models.DateField(default=datetime.now, editable=False)
    create_date = models.IntegerField(default=0, editable=False, null=True, blank=True)
    date_of_publication = models.DateField(null=True, blank=True)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2res_card', on_delete=models.DO_NOTHING)
    branch_id = models.ForeignKey(branchslist, null=True, blank=True, related_name='branch_id2res_card', on_delete=models.DO_NOTHING)
    reg_id = models.ForeignKey(in_registrations, null=True, blank=True, related_name='reg_id2res_card', on_delete=models.DO_NOTHING)
    class_id = models.ForeignKey(in_class, null=True, blank=True, related_name='class_id2res_card', on_delete=models.DO_NOTHING)
    section_id = models.ForeignKey(in_section, null=True, blank=True, related_name='section_id2res_card', on_delete=models.DO_NOTHING)
    shift_id = models.ForeignKey(in_shifts, null=True, blank=True, related_name='shift_id2res_card', on_delete=models.DO_NOTHING)
    groups_id = models.ForeignKey(in_groups, null=True, blank=True, related_name='groups_id2res_card', on_delete=models.DO_NOTHING)
    is_half_year = models.BooleanField(default=True)
    is_annual = models.BooleanField(default=True)
    is_average_gpa = models.CharField(max_length=10, null=True, blank=True)
    average_letter_grade = models.CharField(max_length=10, null=True, blank=True)
    result_status = models.CharField(max_length=15, null=True, blank=True)
    total_defaults_marks = models.IntegerField(null=True, blank=True, default=0)
    is_grand_total_marks = models.IntegerField(null=True, blank=True, default=0)
    is_grand_pass_marks = models.IntegerField(null=True, blank=True, default=0)
    merit_position = models.IntegerField(null=True, blank=True, default=0)
    total_working_days = models.IntegerField(null=True, blank=True, default=0)
    total_present_days = models.IntegerField(null=True, blank=True, default=0)
    is_remarks = models.CharField(max_length=150, null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    is_approved_by = models.ForeignKey(User, null=True, blank=True, related_name='user_id2res_card', on_delete=models.DO_NOTHING)
    approved_date = models.CharField(max_length=50, null=True, blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2res_card', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1366700000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2res_card', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=1407360000000, editable=False)

    def save(self, *args, **kwargs):
        trans_data = in_results_card_entry.objects.all()

        if trans_data.exists() and self._state.adding:
            last_order = trans_data.latest('res_card_id')
            user_session = trans_data.latest('ss_created_session')
            modifier_session = trans_data.latest('ss_modified_session')
            self.res_card_id = int(last_order.res_card_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.res_card_id)
    

class in_results_card_entry_dtls(models.Model):
    res_carddtls_id = models.BigAutoField(primary_key=True, default=1204404000001, editable=False)
    res_card_id = models.ForeignKey(in_results_card_entry, null=True, blank=True, related_name='res_card_id2res_carddtls', on_delete=models.DO_NOTHING)
    subjects_id = models.ForeignKey(in_subjects, null=True, blank=True, related_name='subjects_id2res_carddtls', on_delete=models.DO_NOTHING)
    sub_defaults_marks = models.IntegerField(null=True, blank=True, default=0)
    sub_pass_marks = models.IntegerField(null=True, blank=True, default=0)
    is_cq = models.IntegerField(null=True, blank=True, default=0)
    is_mcq = models.IntegerField(null=True, blank=True, default=0)
    is_written = models.IntegerField(null=True, blank=True, default=0)
    is_practical = models.IntegerField(null=True, blank=True, default=0)
    total_inv_marks = models.IntegerField(null=True, blank=True, default=0)
    sub_letter_grade = models.CharField(max_length=10, null=True, blank=True)
    is_sub_gp = models.CharField(max_length=10, null=True, blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2res_carddtls', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1388090000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2res_carddtls', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=1884369000000, editable=False)

    def save(self, *args, **kwargs):
        last_data = in_results_card_entry_dtls.objects.all()

        if last_data.exists() and self._state.adding:
            last_order = last_data.latest('res_carddtls_id')
            user_session = last_data.latest('ss_created_session')
            modifier_session = last_data.latest('ss_modified_session')
            self.res_carddtls_id = int(last_order.res_carddtls_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.res_carddtls_id)