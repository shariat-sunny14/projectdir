from django.db import models
from organizations.models import organizationlst
from class_setup.models import in_class
from groups_setup.models import in_groups
from django.contrib.auth import get_user_model
User = get_user_model()


class in_subjects(models.Model):
    subjects_id = models.BigAutoField(primary_key=True, default=1266440000000, editable=False)
    short_name = models.CharField(max_length=50, null=True, blank=True)
    subjects_no = models.CharField(max_length=50, null=True, blank=True)
    subjects_name = models.CharField(max_length=100, null=True, blank=True)
    is_marks = models.IntegerField(null=True, blank=True)
    is_pass_marks = models.IntegerField(default=0, null=True, blank=True)
    class_id = models.ForeignKey(in_class, null=True, blank=True, related_name='class_id2in_subjects', on_delete=models.DO_NOTHING)
    groups_id = models.ForeignKey(in_groups, null=True, blank=True, related_name='groups_id2in_subjects', on_delete=models.DO_NOTHING)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2in_subjects', on_delete=models.DO_NOTHING)
    is_optional = models.BooleanField(default=False)
    is_not_countable = models.BooleanField(default=False)
    is_applicable_pass_marks = models.BooleanField(default=False)
    is_optional_wise_grade_cal = models.BooleanField(default=False)
    # for optional subject wise grade calculation hobe ki na. jodi true hoy tahole avarage grade show hobe r jodi false hoy tahole show hobe na
    is_english = models.BooleanField(default=False)
    is_bangla = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2in_subjects', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=17741000000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2in_subjects', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=188810000000, editable=False)

    def save(self, *args, **kwargs):
        last_data = in_subjects.objects.all()

        if last_data.exists() and self._state.adding:
            last_order = last_data.latest('subjects_id')
            user_session = last_data.latest('ss_created_session')
            modifier_session = last_data.latest('ss_modified_session')
            self.subjects_id = int(last_order.subjects_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.subjects_id)