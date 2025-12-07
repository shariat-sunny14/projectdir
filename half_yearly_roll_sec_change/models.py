from django.db import models
from datetime import datetime, date
from django.db.models import Max
from merit_app_card_print.models import in_merit_position_approval
from organizations.models import branchslist, organizationlst
from class_setup.models import in_class
from groups_setup.models import in_groups
from section_setup.models import in_section
from shift_setup.models import in_shifts
from registrations.models import in_registrations
from subject_setup.models import in_subjects
from django.contrib.auth import get_user_model
User = get_user_model()


class in_half_yearly_roll_sec_change_info(models.Model):
    hyrscinfo_id = models.BigAutoField(primary_key=True, default=1234900900001, editable=False)
    created_date = models.DateField(default=datetime.now, editable=False)
    hyrscinfo_year = models.IntegerField(default=datetime.now().year, editable=False)
    merit_id = models.ForeignKey(in_merit_position_approval, null=True, blank=True, related_name='merit_id2hyrscinfo', on_delete=models.DO_NOTHING)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2hyrscinfo', on_delete=models.DO_NOTHING)
    branch_id = models.ForeignKey(branchslist, null=True, blank=True, related_name='branch_id2hyrscinfo', on_delete=models.DO_NOTHING)
    class_id = models.ForeignKey(in_class, null=True, blank=True, related_name='class_id2hyrscinfo', on_delete=models.DO_NOTHING)
    shifts_id = models.ForeignKey(in_shifts, null=True, blank=True, related_name='shifts_id2hyrscinfo', on_delete=models.DO_NOTHING)
    groups_id = models.ForeignKey(in_groups, null=True, blank=True, related_name='groups_id2hyrscinfo', on_delete=models.DO_NOTHING)
    is_half_yearly = models.BooleanField(default=False)
    is_yearly = models.BooleanField(default=False)
    is_english = models.BooleanField(default=False)
    is_bangla = models.BooleanField(default=False)
    # 
    is_changed = models.BooleanField(default=False)
    is_changed_by = models.ForeignKey(User, null=True, blank=True, related_name='user_changed_id2hyrscinfo', on_delete=models.DO_NOTHING)
    is_changed_date = models.CharField(max_length=50, null=True, blank=True)
    # 
    is_rollback = models.BooleanField(default=False)
    is_rollback_by = models.ForeignKey(User, null=True, blank=True, related_name='user_rollback_id2hyrscinfo', on_delete=models.DO_NOTHING)
    is_rollback_date = models.CharField(max_length=50, null=True, blank=True)
    # 
    is_created_by = models.ForeignKey(User, null=True, blank=True, related_name='user_id2hyrscinfo', on_delete=models.DO_NOTHING)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2hyrscinfo', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1468450900000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2hyrscinfo', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=1257400506000, editable=False)

    def save(self, *args, **kwargs):
        trans_data = in_half_yearly_roll_sec_change_info.objects.all()

        if trans_data.exists() and self._state.adding:
            last_order = trans_data.latest('hyrscinfo_id')
            user_session = trans_data.latest('ss_created_session')
            modifier_session = trans_data.latest('ss_modified_session')
            self.hyrscinfo_id = int(last_order.hyrscinfo_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.hyrscinfo_id)


class in_half_yearly_roll_sec_change_history(models.Model):
    hyrschistory_id = models.BigAutoField(primary_key=True, default=1479600000001, editable=False)
    created_date = models.DateField(default=datetime.now, editable=False)
    hyrscinfo_year = models.IntegerField(default=datetime.now().year, editable=False)
    hyrscinfo_id = models.ForeignKey(in_half_yearly_roll_sec_change_info, null=True, blank=True, related_name='hyrscinfo_id2hyrsc_history', on_delete=models.DO_NOTHING)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2hyrsc_history', on_delete=models.DO_NOTHING)
    branch_id = models.ForeignKey(branchslist, null=True, blank=True, related_name='branch_id2hyrsc_history', on_delete=models.DO_NOTHING)
    class_id = models.ForeignKey(in_class, null=True, blank=True, related_name='class_id2hyrsc_history', on_delete=models.DO_NOTHING)
    shifts_id = models.ForeignKey(in_shifts, null=True, blank=True, related_name='shifts_id2hyrsc_history', on_delete=models.DO_NOTHING)
    groups_id = models.ForeignKey(in_groups, null=True, blank=True, related_name='groups_id2hyrsc_history', on_delete=models.DO_NOTHING)
    reg_id = models.ForeignKey(in_registrations, null=True, blank=True, related_name='reg_id2hyrsc_history', on_delete=models.DO_NOTHING)
    is_half_yearly = models.BooleanField(default=False)
    is_yearly = models.BooleanField(default=False)
    is_english = models.BooleanField(default=False)
    is_bangla = models.BooleanField(default=False)
    old_roll_no = models.CharField(max_length=20, null=True, blank=True)
    new_roll_no = models.CharField(max_length=20, null=True, blank=True)
    old_section_id = models.ForeignKey(in_section, null=True, blank=True, related_name='old_section_id2hyrsc_history', on_delete=models.DO_NOTHING)
    new_section_id = models.ForeignKey(in_section, null=True, blank=True, related_name='new_section_id2hyrsc_history', on_delete=models.DO_NOTHING)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2hyrsc_history', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=14700500300000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2hyrsc_history', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=10351076890000, editable=False)

    def save(self, *args, **kwargs):
        trans_data = in_half_yearly_roll_sec_change_history.objects.all()

        if trans_data.exists() and self._state.adding:
            last_order = trans_data.latest('hyrschistory_id')
            user_session = trans_data.latest('ss_created_session')
            modifier_session = trans_data.latest('ss_modified_session')
            self.hyrschistory_id = int(last_order.hyrschistory_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.hyrschistory_id)
    
    
class in_half_yearly_rollsecchange_rollback_history(models.Model):
    hyrscrollbackh_id = models.BigAutoField(primary_key=True, default=1939400000001, editable=False)
    created_date = models.DateField(default=datetime.now, editable=False)
    hyrscinfo_year = models.IntegerField(default=datetime.now().year, editable=False)
    hyrscinfo_id = models.ForeignKey(in_half_yearly_roll_sec_change_info, null=True, blank=True, related_name='hyrscinfo_id2hyrsc_rollback_history', on_delete=models.DO_NOTHING)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2hyrsc_rollback_history', on_delete=models.DO_NOTHING)
    branch_id = models.ForeignKey(branchslist, null=True, blank=True, related_name='branch_id2hyrsc_rollback_history', on_delete=models.DO_NOTHING)
    class_id = models.ForeignKey(in_class, null=True, blank=True, related_name='class_id2hyrsc_rollback_history', on_delete=models.DO_NOTHING)
    shifts_id = models.ForeignKey(in_shifts, null=True, blank=True, related_name='shifts_id2hyrsc_rollback_history', on_delete=models.DO_NOTHING)
    groups_id = models.ForeignKey(in_groups, null=True, blank=True, related_name='groups_id2hyrsc_rollback_history', on_delete=models.DO_NOTHING)
    reg_id = models.ForeignKey(in_registrations, null=True, blank=True, related_name='reg_id2hyrsc_rollback_history', on_delete=models.DO_NOTHING)
    is_half_yearly = models.BooleanField(default=False)
    is_yearly = models.BooleanField(default=False)
    is_english = models.BooleanField(default=False)
    is_bangla = models.BooleanField(default=False)
    new_roll_no = models.CharField(max_length=20, null=True, blank=True)
    rollback_roll_no = models.CharField(max_length=20, null=True, blank=True)
    new_section_id = models.ForeignKey(in_section, null=True, blank=True, related_name='new_section_id2hyrsc_rollback_history', on_delete=models.DO_NOTHING)
    rollback_section_id = models.ForeignKey(in_section, null=True, blank=True, related_name='rollback_section_id2hyrsc_rollback_history', on_delete=models.DO_NOTHING)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2hyrsc_rollback_history', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=14888900300000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2hyrsc_rollback_history', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=10588096810000, editable=False)

    def save(self, *args, **kwargs):
        trans_data = in_half_yearly_rollsecchange_rollback_history.objects.all()

        if trans_data.exists() and self._state.adding:
            last_order = trans_data.latest('hyrscrollbackh_id')
            user_session = trans_data.latest('ss_created_session')
            modifier_session = trans_data.latest('ss_modified_session')
            self.hyrscrollbackh_id = int(last_order.hyrscrollbackh_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.hyrscrollbackh_id)