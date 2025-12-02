from django.db import models
from datetime import datetime, date
from class_setup.models import in_class
from groups_setup.models import in_groups
from organizations.models import branchslist, organizationlst
from django.contrib.auth import get_user_model
from section_setup.models import in_section
from shift_setup.models import in_shifts
from subject_setup.models import in_subjects
User = get_user_model()

# Create your models here.
class in_class_wise_merit_policy(models.Model):
    clsswisep_id = models.BigAutoField(primary_key=True, default=1234014000000, editable=False)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2clsswisepm', on_delete=models.DO_NOTHING)
    class_id = models.ForeignKey(in_class, null=True, blank=True, related_name='class_id2clsswisepm', on_delete=models.DO_NOTHING)
    # policy fields with serial number (lower = higher priority)
    is_average_gpa_priority = models.IntegerField(blank=True, null=True, help_text="Sorting priority for GPA")
    total_obtained_marks_priority = models.IntegerField(blank=True, null=True, help_text="Sorting priority for Total Marks")
    roll_no_priority = models.IntegerField(blank=True, null=True, help_text="Sorting priority for Roll No")
    is_english = models.BooleanField(default=False)
    is_bangla = models.BooleanField(default=False)
    is_fail_sub_count = models.BooleanField(default=False)
    is_gross_merit_position = models.BooleanField(default=False)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2clsswisepm', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1135700000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2clsswisepm', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=145780000000, editable=False)

    def save(self, *args, **kwargs):
        last_data = in_class_wise_merit_policy.objects.all()

        if last_data.exists() and self._state.adding:
            last_order = last_data.latest('clsswisep_id')
            user_session = last_data.latest('ss_created_session')
            modifier_session = last_data.latest('ss_modified_session')
            self.clsswisep_id = int(last_order.clsswisep_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.clsswisep_id)
    


class in_subject_wise_merit_policy(models.Model):
    subswisep_id = models.BigAutoField(primary_key=True, default=1333014000000, editable=False)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2subswisepm', on_delete=models.DO_NOTHING)
    class_id = models.ForeignKey(in_class, null=True, blank=True, related_name='class_id2subswisepm', on_delete=models.DO_NOTHING)
    groups_id = models.ForeignKey(in_groups, null=True, blank=True, related_name='groups_id2subswisepm', on_delete=models.DO_NOTHING)
    subjects_id = models.ForeignKey(in_subjects, null=True, blank=True, related_name='subjects_id2subswisepm', on_delete=models.DO_NOTHING)
    # policy fields with serial number (lower = higher priority)
    subject_priority = models.IntegerField(blank=True, null=True, help_text="Sorting priority for Subject")
    is_english = models.BooleanField(default=False)
    is_bangla = models.BooleanField(default=False)
    is_sub_groups = models.BooleanField(default=False)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2subswisepm', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1235700000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2subswisepm', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=155580000000, editable=False)

    def save(self, *args, **kwargs):
        last_data = in_subject_wise_merit_policy.objects.all()

        if last_data.exists() and self._state.adding:
            last_order = last_data.latest('subswisep_id')
            user_session = last_data.latest('ss_created_session')
            modifier_session = last_data.latest('ss_modified_session')
            self.subswisep_id = int(last_order.subswisep_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.subswisep_id)
    
    

class classSectionGroupingMap(models.Model):
    clss_sec_map_id = models.BigAutoField(primary_key=True, default=1110340000000, editable=False)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2clss_sec_map', on_delete=models.DO_NOTHING)
    class_id = models.ForeignKey(in_class, null=True, blank=True, related_name='class_id2clss_sec_map', on_delete=models.DO_NOTHING)
    section_id = models.ForeignKey(in_section, null=True, blank=True, related_name='section_id2clss_sec_map', on_delete=models.DO_NOTHING)
    is_order_by = models.IntegerField(default=0, blank=True, null=True, help_text="Sorting priority for Section")
    is_group_no = models.IntegerField(default=0, blank=True, null=True, help_text="Group Number")
    is_group_name = models.CharField(max_length=255, blank=True, null=True, help_text="Group Name")
    is_grouping_flag = models.BooleanField(default=False)
    is_individual_flag = models.BooleanField(default=False)
    is_english = models.BooleanField(default=False)
    is_bangla = models.BooleanField(default=False)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2clss_sec_map', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1354600000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2clss_sec_map', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=1365789000000, editable=False)

    def save(self, *args, **kwargs):
        last_data = classSectionGroupingMap.objects.all()

        if last_data.exists() and self._state.adding:
            last_order = last_data.latest('clss_sec_map_id')
            user_session = last_data.latest('ss_created_session')
            modifier_session = last_data.latest('ss_modified_session')
            self.clss_sec_map_id = int(last_order.clss_sec_map_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.clss_sec_map_id)
    
    
    
# =============================================================================
# half year roll sec change policy model
# =============================================================================
class half_year_roll_section_change_policy(models.Model):
    hyrscp_id = models.BigAutoField(primary_key=True, default=1225240000000, editable=False)
    hyrscp_year = models.IntegerField(default=datetime.now().year, editable=False)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2hyrscp_policy', on_delete=models.DO_NOTHING)
    class_id = models.ForeignKey(in_class, null=True, blank=True, related_name='class_id2hyrscp_policy', on_delete=models.DO_NOTHING)
    groups_id = models.ForeignKey(in_groups, null=True, blank=True, related_name='groups_id2hyrscp_policy', on_delete=models.DO_NOTHING)
    section_id = models.ForeignKey(in_section, null=True, blank=True, related_name='section_id2hyrscp_policy', on_delete=models.DO_NOTHING)
    shift_id = models.ForeignKey(in_shifts, null=True, blank=True, related_name='shift_id2hyrscp_policy', on_delete=models.DO_NOTHING)
    is_english = models.BooleanField(default=False)
    is_bangla = models.BooleanField(default=False)
    from_roll = models.CharField(max_length=20, null=True, blank=True)
    to_roll = models.CharField(max_length=20, null=True, blank=True)
    is_invd_flag = models.BooleanField(default=False)
    is_group_flag = models.BooleanField(default=False)
    group_serials = models.CharField(max_length=20, null=True, blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2hyrscp_policy', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1424600000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2hyrscp_policy', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=1572789000000, editable=False)

    def save(self, *args, **kwargs):
        last_data = half_year_roll_section_change_policy.objects.all()

        if last_data.exists() and self._state.adding:
            last_order = last_data.latest('hyrscp_id')
            user_session = last_data.latest('ss_created_session')
            modifier_session = last_data.latest('ss_modified_session')
            self.hyrscp_id = int(last_order.hyrscp_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.hyrscp_id)
    
    
# =============================================================================
# Annual Exam Percentance model
# =============================================================================
class annual_exam_percentance_policy(models.Model):
    aexperpo_id = models.BigAutoField(primary_key=True, default=1554691000000, editable=False)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2aexperpolicy', on_delete=models.DO_NOTHING)
    aexperpo_year = models.IntegerField(default=datetime.now().year, editable=False)
    class_id = models.ForeignKey(in_class, null=True, blank=True, related_name='class_id2aexperpolicy', on_delete=models.DO_NOTHING)
    half_yearly_per = models.IntegerField(blank=True, null=True)
    annual_per = models.IntegerField(blank=True, null=True)
    is_english = models.BooleanField(default=False)
    is_bangla = models.BooleanField(default=False)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2aexperpolicy', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1555780200000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2aexperpolicy', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=1558890000000, editable=False)

    def save(self, *args, **kwargs):
        last_data = annual_exam_percentance_policy.objects.all()

        if last_data.exists() and self._state.adding:
            last_order = last_data.latest('aexperpo_id')
            user_session = last_data.latest('ss_created_session')
            modifier_session = last_data.latest('ss_modified_session')
            self.aexperpo_id = int(last_order.aexperpo_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.aexperpo_id)
