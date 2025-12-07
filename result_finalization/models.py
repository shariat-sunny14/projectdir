from django.db import models
from datetime import datetime
from organizations.models import branchslist, organizationlst
from class_setup.models import in_class
from groups_setup.models import in_groups
from section_setup.models import in_section
from shift_setup.models import in_shifts
from exam_type.models import in_exam_type
from subject_setup.models import in_subjects
from defaults_exam_mode.models import defaults_exam_modes, in_exam_modes
from registrations.models import in_registrations
from django.contrib.auth import get_user_model
User = get_user_model()

class in_result_finalization(models.Model):
    res_fin_id = models.BigAutoField(primary_key=True, editable=False)
    created_date = models.DateField(default=datetime.now, editable=False)
    finalize_year = models.IntegerField(default=datetime.now().year, editable=False)
    exam_date = models.DateField(null=True, blank=True)
    names_of_exam = models.CharField(max_length=250, null=True, blank=True)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2in_res_final', on_delete=models.DO_NOTHING)
    branch_id = models.ForeignKey(branchslist, null=True, blank=True, related_name='branch_id2in_res_final', on_delete=models.DO_NOTHING)
    class_id = models.ForeignKey(in_class, null=True, blank=True, related_name='class_id2in_res_final', on_delete=models.DO_NOTHING)
    section_id = models.ForeignKey(in_section, null=True, blank=True, related_name='section_id2in_res_final', on_delete=models.DO_NOTHING)
    shifts_id = models.ForeignKey(in_shifts, null=True, blank=True, related_name='shifts_id2in_res_final', on_delete=models.DO_NOTHING)
    groups_id = models.ForeignKey(in_groups, null=True, blank=True, related_name='groups_id2in_res_final', on_delete=models.DO_NOTHING)
    subject_id = models.ForeignKey(in_subjects, null=True, blank=True, related_name='subject_id2in_res_final', on_delete=models.DO_NOTHING)
    exam_type_id = models.ForeignKey(in_exam_type, null=True, blank=True, related_name='exam_type_id2in_res_final', on_delete=models.DO_NOTHING)
    is_half_yearly = models.BooleanField(default=False)
    is_yearly = models.BooleanField(default=False)
    is_english = models.BooleanField(default=False)
    is_bangla = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    is_approved_by = models.ForeignKey(User, null=True, blank=True, related_name='user_id2in_res_final', on_delete=models.DO_NOTHING)
    approved_date = models.CharField(max_length=50, null=True, blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2in_res_final', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=10000600600000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2in_res_final', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=100090090000, editable=False)

    def save(self, *args, **kwargs):
        last_data = in_result_finalization.objects.all()

        if last_data.exists() and self._state.adding:
            user_session = last_data.latest('ss_created_session')
            modifier_session = last_data.latest('ss_modified_session')
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.res_fin_id)
    


class in_result_finalizationdtls(models.Model):
    res_findtl_id = models.BigAutoField(primary_key=True, editable=False)
    created_date = models.DateField(default=datetime.now, editable=False)
    finalize_year = models.IntegerField(default=datetime.now().year, editable=False)
    res_fin_id = models.ForeignKey(in_result_finalization, null=True, blank=True, related_name='res_fin_id2in_res_finaldtl', on_delete=models.DO_NOTHING)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2in_res_finaldtl', on_delete=models.DO_NOTHING)
    branch_id = models.ForeignKey(branchslist, null=True, blank=True, related_name='branch_id2in_res_finaldtl', on_delete=models.DO_NOTHING)
    class_id = models.ForeignKey(in_class, null=True, blank=True, related_name='class_id2in_res_finaldtl', on_delete=models.DO_NOTHING)
    section_id = models.ForeignKey(in_section, null=True, blank=True, related_name='section_id2in_res_finaldtl', on_delete=models.DO_NOTHING)
    shifts_id = models.ForeignKey(in_shifts, null=True, blank=True, related_name='shifts_id2in_res_finaldtl', on_delete=models.DO_NOTHING)
    groups_id = models.ForeignKey(in_groups, null=True, blank=True, related_name='groups_id2in_res_finaldtl', on_delete=models.DO_NOTHING)
    subject_id = models.ForeignKey(in_subjects, null=True, blank=True, related_name='subject_id2in_res_finaldtl', on_delete=models.DO_NOTHING)
    exam_type_id = models.ForeignKey(in_exam_type, null=True, blank=True, related_name='exam_type_id2in_res_finaldtl', on_delete=models.DO_NOTHING)
    reg_id = models.ForeignKey(in_registrations, null=True, blank=True, related_name='reg_id2in_res_finaldtl', on_delete=models.DO_NOTHING)
    roll_no = models.CharField(max_length=20, null=True, blank=True)
    class_name = models.CharField(max_length=20, null=True, blank=True)
    section_name = models.CharField(max_length=20, null=True, blank=True)
    shift_name = models.CharField(max_length=20, null=True, blank=True)
    groups_name = models.CharField(max_length=20, null=True, blank=True)
    def_mode_id = models.ForeignKey(defaults_exam_modes, null=True, blank=True, related_name='def_mode_id2in_res_finaldtl', on_delete=models.DO_NOTHING)
    is_mode_name = models.CharField(max_length=20, null=True, blank=True)
    is_default_marks = models.IntegerField(default=0, null=True, blank=True)
    is_pass_marks = models.IntegerField(default=0, null=True, blank=True)
    is_actual_marks = models.FloatField(default=0, null=True, blank=True)
    is_absent_present = models.BooleanField(default=False)
    sms_status = models.BooleanField(default=False)
    sms_send_date = models.DateField(null=True, blank=True)
    is_half_yearly = models.BooleanField(default=False)
    is_yearly = models.BooleanField(default=False)
    is_english = models.BooleanField(default=False)
    is_bangla = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    is_approved_by = models.ForeignKey(User, null=True, blank=True, related_name='user_id2in_res_finaldtl', on_delete=models.DO_NOTHING)
    approved_date = models.CharField(max_length=50, null=True, blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2in_res_finaldtl', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=10000700700000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2in_res_finaldtl', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=1000800800000, editable=False)

    def save(self, *args, **kwargs):
        lastdtl_data = in_result_finalizationdtls.objects.all()

        if lastdtl_data.exists() and self._state.adding:
            user_session = lastdtl_data.latest('ss_created_session')
            modifier_session = lastdtl_data.latest('ss_modified_session')
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.res_findtl_id)
    
    
    
    
    
    
    
    
    
# class in_result_finalization(models.Model):
#     res_fin_id = models.BigAutoField(primary_key=True, default=1004040404000, editable=False)
#     created_date = models.DateField(default=datetime.now, editable=False)
#     finalize_year = models.IntegerField(default=datetime.now().year, editable=False)
#     exam_date = models.DateField(null=True, blank=True)
#     names_of_exam = models.CharField(max_length=150, null=True, blank=True)
#     org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2in_res_final', on_delete=models.DO_NOTHING)
#     branch_id = models.ForeignKey(branchslist, null=True, blank=True, related_name='branch_id2in_res_final', on_delete=models.DO_NOTHING)
#     class_id = models.ForeignKey(in_class, null=True, blank=True, related_name='class_id2in_res_final', on_delete=models.DO_NOTHING)
#     section_id = models.ForeignKey(in_section, null=True, blank=True, related_name='section_id2in_res_final', on_delete=models.DO_NOTHING)
#     shifts_id = models.ForeignKey(in_shifts, null=True, blank=True, related_name='shifts_id2in_res_final', on_delete=models.DO_NOTHING)
#     groups_id = models.ForeignKey(in_groups, null=True, blank=True, related_name='groups_id2in_res_final', on_delete=models.DO_NOTHING)
#     subject_id = models.ForeignKey(in_subjects, null=True, blank=True, related_name='subject_id2in_res_final', on_delete=models.DO_NOTHING)
#     exam_type_id = models.ForeignKey(in_exam_type, null=True, blank=True, related_name='exam_type_id2in_res_final', on_delete=models.DO_NOTHING)
#     is_cq_check = models.BooleanField(default=False)
#     is_cq = models.IntegerField(default=0, null=True, blank=True)
#     is_cq_pass_marks = models.IntegerField(default=0, null=True, blank=True)
#     is_mcq_check = models.BooleanField(default=False)
#     is_mcq = models.IntegerField(default=0, null=True, blank=True)
#     is_mcq_pass_marks = models.IntegerField(default=0, null=True, blank=True)
#     is_written_check = models.BooleanField(default=False)
#     is_written = models.IntegerField(default=0, null=True, blank=True)
#     is_written_pass_marks = models.IntegerField(default=0, null=True, blank=True)
#     is_practical_check = models.BooleanField(default=False)
#     is_practical = models.IntegerField(default=0, null=True, blank=True)
#     is_practical_pass_marks = models.IntegerField(default=0, null=True, blank=True)
#     is_oral_check = models.BooleanField(default=False)
#     is_oral = models.IntegerField(default=0, null=True, blank=True)
#     is_oral_pass_marks = models.IntegerField(default=0, null=True, blank=True)
#     is_half_yearly = models.BooleanField(default=False)
#     is_yearly = models.BooleanField(default=False)
#     is_english = models.BooleanField(default=False)
#     is_bangla = models.BooleanField(default=False)
#     is_approved = models.BooleanField(default=False)
#     is_approved_by = models.ForeignKey(User, null=True, blank=True, related_name='user_id2in_res_final', on_delete=models.DO_NOTHING)
#     approved_date = models.CharField(max_length=50, null=True, blank=True)
#     ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2in_res_final', on_delete=models.DO_NOTHING, editable=False)
#     ss_created_on = models.DateTimeField(auto_now_add=True)
#     ss_created_session = models.BigIntegerField(null=True, blank=True, default=10000600600000, editable=False)
#     ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2in_res_final', on_delete=models.DO_NOTHING)
#     ss_modified_on = models.DateTimeField(auto_now=True)
#     ss_modified_session = models.BigIntegerField(null=True, blank=True, default=100090090000, editable=False)

#     def save(self, *args, **kwargs):
#         last_data = in_result_finalization.objects.all()

#         if last_data.exists() and self._state.adding:
#             last_order = last_data.latest('res_fin_id')
#             user_session = last_data.latest('ss_created_session')
#             modifier_session = last_data.latest('ss_modified_session')
#             self.res_fin_id = int(last_order.res_fin_id) + 1
#             self.ss_created_session = int(user_session.ss_created_session) + 1
#             self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
#         super().save(*args, **kwargs)

#     def __str__(self):
#         return str(self.res_fin_id)    
    

# class in_result_finalizationdtls(models.Model):
#     res_findtl_id = models.BigAutoField(primary_key=True, default=1000500505000, editable=False)
#     created_date = models.DateField(default=datetime.now, editable=False)
#     finalize_year = models.IntegerField(default=datetime.now().year, editable=False)
#     res_fin_id = models.ForeignKey(in_result_finalization, null=True, blank=True, related_name='res_fin_id2in_res_finaldtl', on_delete=models.DO_NOTHING)
#     org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2in_res_finaldtl', on_delete=models.DO_NOTHING)
#     branch_id = models.ForeignKey(branchslist, null=True, blank=True, related_name='branch_id2in_res_finaldtl', on_delete=models.DO_NOTHING)
#     class_id = models.ForeignKey(in_class, null=True, blank=True, related_name='class_id2in_res_finaldtl', on_delete=models.DO_NOTHING)
#     section_id = models.ForeignKey(in_section, null=True, blank=True, related_name='section_id2in_res_finaldtl', on_delete=models.DO_NOTHING)
#     shifts_id = models.ForeignKey(in_shifts, null=True, blank=True, related_name='shifts_id2in_res_finaldtl', on_delete=models.DO_NOTHING)
#     groups_id = models.ForeignKey(in_groups, null=True, blank=True, related_name='groups_id2in_res_finaldtl', on_delete=models.DO_NOTHING)
#     subject_id = models.ForeignKey(in_subjects, null=True, blank=True, related_name='subject_id2in_res_finaldtl', on_delete=models.DO_NOTHING)
#     exam_type_id = models.ForeignKey(in_exam_type, null=True, blank=True, related_name='exam_type_id2in_res_finaldtl', on_delete=models.DO_NOTHING)
#     reg_id = models.ForeignKey(in_registrations, null=True, blank=True, related_name='reg_id2in_res_finaldtl', on_delete=models.DO_NOTHING)
#     roll_no = models.CharField(max_length=20, null=True, blank=True)
#     class_name = models.CharField(max_length=20, null=True, blank=True)
#     section_name = models.CharField(max_length=20, null=True, blank=True)
#     shift_name = models.CharField(max_length=20, null=True, blank=True)
#     groups_name = models.CharField(max_length=20, null=True, blank=True)
#     is_cq_marks = models.IntegerField(default=0, null=True, blank=True)
#     is_cq_apval = models.BooleanField(default=False)
#     is_cq_pass_marks = models.IntegerField(default=0, null=True, blank=True)
#     is_mcq_marks = models.IntegerField(default=0, null=True, blank=True)
#     is_mcq_apval = models.BooleanField(default=False)
#     is_mcq_pass_marks = models.IntegerField(default=0, null=True, blank=True)
#     is_written_marks = models.IntegerField(default=0, null=True, blank=True)
#     is_written_apval = models.BooleanField(default=False)
#     is_written_pass_marks = models.IntegerField(default=0, null=True, blank=True)
#     is_practical_marks = models.IntegerField(default=0, null=True, blank=True)
#     is_practical_apval = models.BooleanField(default=False)
#     is_practical_pass_marks = models.IntegerField(default=0, null=True, blank=True)
#     is_oral_marks = models.IntegerField(default=0, null=True, blank=True)
#     is_oral_apval = models.BooleanField(default=False)
#     is_oral_pass_marks = models.IntegerField(default=0, null=True, blank=True)
#     grand_total_marks = models.IntegerField(default=0, null=True, blank=True)
#     sms_status = models.BooleanField(default=False)
#     sms_send_date = models.DateField(null=True, blank=True)
#     is_half_yearly = models.BooleanField(default=False)
#     is_yearly = models.BooleanField(default=False)
#     is_english = models.BooleanField(default=False)
#     is_bangla = models.BooleanField(default=False)
#     is_approved = models.BooleanField(default=False)
#     is_approved_by = models.ForeignKey(User, null=True, blank=True, related_name='user_id2in_res_finaldtl', on_delete=models.DO_NOTHING)
#     approved_date = models.CharField(max_length=50, null=True, blank=True)
#     ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2in_res_finaldtl', on_delete=models.DO_NOTHING, editable=False)
#     ss_created_on = models.DateTimeField(auto_now_add=True)
#     ss_created_session = models.BigIntegerField(null=True, blank=True, default=10000700700000, editable=False)
#     ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2in_res_finaldtl', on_delete=models.DO_NOTHING)
#     ss_modified_on = models.DateTimeField(auto_now=True)
#     ss_modified_session = models.BigIntegerField(null=True, blank=True, default=1000800800000, editable=False)

#     def save(self, *args, **kwargs):
#         lastdtl_data = in_result_finalizationdtls.objects.all()

#         if lastdtl_data.exists() and self._state.adding:
#             last_order = lastdtl_data.latest('res_findtl_id')
#             user_session = lastdtl_data.latest('ss_created_session')
#             modifier_session = lastdtl_data.latest('ss_modified_session')
#             self.res_findtl_id = int(last_order.res_findtl_id) + 1
#             self.ss_created_session = int(user_session.ss_created_session) + 1
#             self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
#         super().save(*args, **kwargs)

#     def __str__(self):
#         return str(self.res_findtl_id)