from django.db import models
from exam_type.models import in_exam_type
from organizations.models import organizationlst
from class_setup.models import in_class
from groups_setup.models import in_groups
from section_setup.models import in_section
from shift_setup.models import in_shifts
from subject_setup.models import in_subjects
from django.contrib.auth import get_user_model
User = get_user_model()


class defaults_exam_modes(models.Model):
    def_mode_id = models.BigAutoField(primary_key=True, default=1880800000000, editable=False)
    order_by = models.IntegerField(default=0, null=True, blank=True)
    short_name = models.CharField(max_length=30, null=True, blank=True)
    is_mode_name = models.CharField(max_length=30, null=True, blank=True)  
    is_active = models.BooleanField(default=False)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2def_mode', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1936900000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2def_mode', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=134891000000, editable=False)

    def save(self, *args, **kwargs):
        last_data = defaults_exam_modes.objects.all()

        if last_data.exists() and self._state.adding:
            last_order = last_data.latest('def_mode_id')
            user_session = last_data.latest('ss_created_session')
            modifier_session = last_data.latest('ss_modified_session')
            self.def_mode_id = int(last_order.def_mode_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.def_mode_id)


class in_exam_modes(models.Model):
    exam_mode_id = models.BigAutoField(primary_key=True, default=1647890000000, editable=False)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2exam_modes', on_delete=models.DO_NOTHING)
    class_id = models.ForeignKey(in_class, null=True, blank=True, related_name='class_id2exam_modes', on_delete=models.DO_NOTHING)
    subjects_id = models.ForeignKey(in_subjects, null=True, blank=True, related_name='subjects_id2exam_modes', on_delete=models.DO_NOTHING)
    exam_type_id = models.ForeignKey(in_exam_type, null=True, blank=True, related_name='exam_type_id2exam_modes', on_delete=models.DO_NOTHING)
    is_exam_modes = models.ForeignKey(defaults_exam_modes, null=True, blank=True, related_name='def_mode_id2exam_modes', on_delete=models.DO_NOTHING)
    is_default_marks = models.IntegerField(default=0, null=True, blank=True)
    is_pass_marks = models.IntegerField(default=0, null=True, blank=True)
    is_english = models.BooleanField(default=False)
    is_bangla = models.BooleanField(default=False)
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
    
    
    
class in_letter_grade_mode(models.Model):
    grade_id = models.BigAutoField(primary_key=True, default=1990990000000, editable=False)
    is_grade_name = models.CharField(max_length=30, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2letter_grade', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1249700000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2letter_grade', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=187634000000, editable=False)

    def save(self, *args, **kwargs):
        last_data = in_letter_grade_mode.objects.all()

        if last_data.exists() and self._state.adding:
            last_order = last_data.latest('grade_id')
            user_session = last_data.latest('ss_created_session')
            modifier_session = last_data.latest('ss_modified_session')
            self.grade_id = int(last_order.grade_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.grade_id)
    
# ===============================================================
class ExamModeTypeMap(models.Model):
    xm_m_t_map_id = models.BigAutoField(primary_key=True, default=1500550000000, editable=False)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2xmmt_map', on_delete=models.DO_NOTHING)
    class_id = models.ForeignKey(in_class, null=True, blank=True, related_name='class_id2xmmt_map', on_delete=models.DO_NOTHING)
    def_mode_id = models.ForeignKey(defaults_exam_modes, null=True, blank=True, related_name='def_mode_id2mmt_map', on_delete=models.DO_NOTHING)
    exam_type_id = models.ForeignKey(in_exam_type, null=True, blank=True, related_name='exam_type_id2mmt_map', on_delete=models.DO_NOTHING)
    is_english = models.BooleanField(default=False)
    is_bangla = models.BooleanField(default=False)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2mmt_map', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1255500000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2mmt_map', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=186666000000, editable=False)

    def save(self, *args, **kwargs):
        last_data = ExamModeTypeMap.objects.all()

        if last_data.exists() and self._state.adding:
            last_order = last_data.latest('xm_m_t_map_id')
            user_session = last_data.latest('ss_created_session')
            modifier_session = last_data.latest('ss_modified_session')
            self.xm_m_t_map_id = int(last_order.xm_m_t_map_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.xm_m_t_map_id)
    

class in_letter_gradeHundredMap(models.Model):
    hundred_map_id = models.BigAutoField(primary_key=True, default=1700770000000, editable=False)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2hundred_map', on_delete=models.DO_NOTHING)
    class_id = models.ForeignKey(in_class, null=True, blank=True, related_name='class_id2hundred_map', on_delete=models.DO_NOTHING)
    grade_id = models.ForeignKey(in_letter_grade_mode, null=True, blank=True, related_name='grade_id2hundred_map', on_delete=models.DO_NOTHING)
    from_marks = models.FloatField(null=True, blank=True)
    to_marks = models.FloatField(null=True, blank=True)
    grade_point = models.FloatField(null=True, blank=True)
    is_english = models.BooleanField(default=False)
    is_bangla = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2hundred_map', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1288900000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2hundred_map', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=185677000000, editable=False)

    def save(self, *args, **kwargs):
        last_data = in_letter_gradeHundredMap.objects.all()

        if last_data.exists() and self._state.adding:
            last_order = last_data.latest('hundred_map_id')
            user_session = last_data.latest('ss_created_session')
            modifier_session = last_data.latest('ss_modified_session')
            self.hundred_map_id = int(last_order.hundred_map_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.hundred_map_id)
    

class in_letter_gradeFiftyMap(models.Model):
    fifty_map_id = models.BigAutoField(primary_key=True, default=1700770000000, editable=False)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2fifty_map', on_delete=models.DO_NOTHING)
    class_id = models.ForeignKey(in_class, null=True, blank=True, related_name='class_id2fifty_map', on_delete=models.DO_NOTHING)
    grade_id = models.ForeignKey(in_letter_grade_mode, null=True, blank=True, related_name='grade_id2fifty_map', on_delete=models.DO_NOTHING)
    from_marks = models.FloatField(null=True, blank=True)
    to_marks = models.FloatField(null=True, blank=True)
    grade_point = models.FloatField(null=True, blank=True)
    is_english = models.BooleanField(default=False)
    is_bangla = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2fifty_map', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1288900000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2fifty_map', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=185677000000, editable=False)

    def save(self, *args, **kwargs):
        last_data = in_letter_gradeFiftyMap.objects.all()

        if last_data.exists() and self._state.adding:
            last_order = last_data.latest('fifty_map_id')
            user_session = last_data.latest('ss_created_session')
            modifier_session = last_data.latest('ss_modified_session')
            self.fifty_map_id = int(last_order.fifty_map_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.fifty_map_id)