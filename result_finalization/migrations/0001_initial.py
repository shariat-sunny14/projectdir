# Generated by Django 4.1.5 on 2025-05-20 16:57

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('subject_setup', '0002_in_subjects_is_marks'),
        ('class_setup', '0002_in_class_allow_groups'),
        ('groups_setup', '0001_initial'),
        ('registrations', '0006_in_registrations_branch_id'),
        ('section_setup', '0001_initial'),
        ('organizations', '0002_initial'),
        ('exam_type', '0001_initial'),
        ('shift_setup', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='in_result_finalization',
            fields=[
                ('res_fin_id', models.BigAutoField(default=1004040404000, editable=False, primary_key=True, serialize=False)),
                ('created_date', models.DateField(default=datetime.datetime.now, editable=False)),
                ('exam_date', models.DateField(blank=True, null=True)),
                ('names_of_exam', models.CharField(blank=True, max_length=150, null=True)),
                ('is_cq_check', models.BooleanField(default=False)),
                ('is_cq', models.IntegerField(blank=True, default=0, null=True)),
                ('is_mcq_check', models.BooleanField(default=False)),
                ('is_mcq', models.IntegerField(blank=True, default=0, null=True)),
                ('is_written_check', models.BooleanField(default=False)),
                ('is_written', models.IntegerField(blank=True, default=0, null=True)),
                ('is_practical_check', models.BooleanField(default=False)),
                ('is_practical', models.IntegerField(blank=True, default=0, null=True)),
                ('is_oral_check', models.BooleanField(default=False)),
                ('is_oral', models.IntegerField(blank=True, default=0, null=True)),
                ('is_approved', models.BooleanField(default=False)),
                ('approved_date', models.CharField(blank=True, max_length=50, null=True)),
                ('ss_created_on', models.DateTimeField(auto_now_add=True)),
                ('ss_created_session', models.BigIntegerField(blank=True, default=10000600600000, editable=False, null=True)),
                ('ss_modified_on', models.DateTimeField(auto_now=True)),
                ('ss_modified_session', models.BigIntegerField(blank=True, default=100090090000, editable=False, null=True)),
                ('branch_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='branch_id2in_res_final', to='organizations.branchslist')),
                ('class_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='class_id2in_res_final', to='class_setup.in_class')),
                ('exam_type_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='exam_type_id2in_res_final', to='exam_type.in_exam_type')),
                ('groups_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='groups_id2in_res_final', to='groups_setup.in_groups')),
                ('is_approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='user_id2in_res_final', to=settings.AUTH_USER_MODEL)),
                ('org_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='org_id2in_res_final', to='organizations.organizationlst')),
                ('section_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='section_id2in_res_final', to='section_setup.in_section')),
                ('shifts_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='shifts_id2in_res_final', to='shift_setup.in_shifts')),
                ('ss_creator', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='ss_creator2in_res_final', to=settings.AUTH_USER_MODEL)),
                ('ss_modifier', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='ss_modifier2in_res_final', to=settings.AUTH_USER_MODEL)),
                ('subject_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='subject_id2in_res_final', to='subject_setup.in_subjects')),
            ],
        ),
        migrations.CreateModel(
            name='in_result_finalizationdtls',
            fields=[
                ('res_findtl_id', models.BigAutoField(default=1000500505000, editable=False, primary_key=True, serialize=False)),
                ('created_date', models.DateField(default=datetime.datetime.now, editable=False)),
                ('roll_no', models.CharField(blank=True, max_length=20, null=True)),
                ('class_name', models.CharField(blank=True, max_length=20, null=True)),
                ('section_name', models.CharField(blank=True, max_length=20, null=True)),
                ('shift_name', models.CharField(blank=True, max_length=20, null=True)),
                ('groups_name', models.CharField(blank=True, max_length=20, null=True)),
                ('is_cq_marks', models.IntegerField(blank=True, default=0, null=True)),
                ('is_cq_apval', models.BooleanField(default=False)),
                ('is_mcq_marks', models.IntegerField(blank=True, default=0, null=True)),
                ('is_mcq_apval', models.BooleanField(default=False)),
                ('is_written_marks', models.IntegerField(blank=True, default=0, null=True)),
                ('is_written_apval', models.BooleanField(default=False)),
                ('is_practical_marks', models.IntegerField(blank=True, default=0, null=True)),
                ('is_practical_apval', models.BooleanField(default=False)),
                ('is_oral_marks', models.IntegerField(blank=True, default=0, null=True)),
                ('is_oral_apval', models.BooleanField(default=False)),
                ('grand_total_marks', models.IntegerField(blank=True, default=0, null=True)),
                ('ss_created_on', models.DateTimeField(auto_now_add=True)),
                ('ss_created_session', models.BigIntegerField(blank=True, default=10000700700000, editable=False, null=True)),
                ('ss_modified_on', models.DateTimeField(auto_now=True)),
                ('ss_modified_session', models.BigIntegerField(blank=True, default=1000800800000, editable=False, null=True)),
                ('reg_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='reg_id2in_res_finaldtl', to='registrations.in_registrations')),
                ('res_fin_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='res_fin_id2in_res_finaldtl', to='result_finalization.in_result_finalization')),
                ('ss_creator', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='ss_creator2in_res_finaldtl', to=settings.AUTH_USER_MODEL)),
                ('ss_modifier', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='ss_modifier2in_res_finaldtl', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
