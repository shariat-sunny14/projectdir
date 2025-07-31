from django.db import models
from module_setup.models import module_list, module_type, feature_list
from organizations.models import organizationlst
from class_setup.models import in_class
from groups_setup.models import in_groups
from section_setup.models import in_section
from shift_setup.models import in_shifts
from django.contrib.auth import get_user_model
User = get_user_model()


# Create your models here.
class access_list(models.Model):
    access_id = models.BigAutoField(primary_key=True, default=20000000001, editable=False)
    user_id = models.ForeignKey(User, null=True, blank=True, related_name='user_id2access_list', on_delete=models.DO_NOTHING, editable=False)
    feature_id = models.ForeignKey(feature_list, null=True, blank=True, related_name='feature_id2access_list', on_delete=models.DO_NOTHING, editable=False)
    is_active = models.BooleanField(default=False)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2access_list', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField( null=True, blank=True, default=2000000000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2access_list', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=101110000000, editable=False)

    def save(self, *args, **kwargs):
        access_data = access_list.objects.all()

        if access_data.exists() and self._state.adding:
            last_order = access_data.latest('access_id')
            user_session = access_data.latest('ss_created_session')
            modifier_session = access_data.latest('ss_modified_session')
            self.access_id = int(last_order.access_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(
                modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.access_id)
    

class others_access_list(models.Model):
    other_acc_id = models.BigAutoField(primary_key=True, default=3000000000010, editable=False)
    user_id = models.ForeignKey(User, null=True, blank=True, related_name='user_id2others_access', on_delete=models.DO_NOTHING, editable=False)
    class_id = models.ForeignKey(in_class, null=True, blank=True, related_name='class_id2others_access', on_delete=models.DO_NOTHING)
    section_id = models.ForeignKey(in_section, null=True, blank=True, related_name='section_id2others_access', on_delete=models.DO_NOTHING)
    shifts_id = models.ForeignKey(in_shifts, null=True, blank=True, related_name='shifts_id2others_access', on_delete=models.DO_NOTHING)
    groups_id = models.ForeignKey(in_groups, null=True, blank=True, related_name='groups_id2others_access', on_delete=models.DO_NOTHING)
    is_defaults = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2others_access', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField( null=True, blank=True, default=2300000000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2others_access', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=103330000000, editable=False)

    def save(self, *args, **kwargs):
        access_data = others_access_list.objects.all()

        if access_data.exists() and self._state.adding:
            last_order = access_data.latest('other_acc_id')
            user_session = access_data.latest('ss_created_session')
            modifier_session = access_data.latest('ss_modified_session')
            self.other_acc_id = int(last_order.other_acc_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(
                modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.other_acc_id)


class lookup_values(models.Model):
    lookup_id = models.BigAutoField(primary_key=True, default=1000000001, editable=False)
    identify_code = models.CharField(max_length=50, null=True, blank=True)
    name = models.CharField(max_length=150, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2lookup_values', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1100100010000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2lookup_values', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=1200200020000, editable=False)

    def save(self, *args, **kwargs):
        lookup_data = lookup_values.objects.all()

        if lookup_data.exists() and self._state.adding:
            last_order = lookup_data.latest('lookup_id')
            user_session = lookup_data.latest('ss_created_session')
            modifier_session = lookup_data.latest('ss_modified_session')
            self.lookup_id = int(last_order.lookup_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.lookup_id)