# Generated by Django 4.1.5 on 2025-05-18 07:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('class_setup', '0002_in_class_allow_groups'),
        ('organizations', '0002_initial'),
        ('defaults_exam_mode', '0003_rename_is_cq_active_in_exam_modes_is_active_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='in_exam_modes',
            name='class_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='class_id2exam_modes', to='class_setup.in_class'),
        ),
        migrations.AddField(
            model_name='in_exam_modes',
            name='org_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='org_id2exam_modes', to='organizations.organizationlst'),
        ),
    ]
