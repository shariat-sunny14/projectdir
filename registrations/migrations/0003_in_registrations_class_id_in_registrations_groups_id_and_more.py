# Generated by Django 4.1.5 on 2025-05-13 09:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('section_setup', '0001_initial'),
        ('class_setup', '0002_in_class_allow_groups'),
        ('shift_setup', '0001_initial'),
        ('groups_setup', '0001_initial'),
        ('registrations', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='in_registrations',
            name='class_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='class_id2in_reg', to='class_setup.in_class'),
        ),
        migrations.AddField(
            model_name='in_registrations',
            name='groups_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='groups_id2in_reg', to='groups_setup.in_groups'),
        ),
        migrations.AddField(
            model_name='in_registrations',
            name='section_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='section_id2in_reg', to='section_setup.in_section'),
        ),
        migrations.AddField(
            model_name='in_registrations',
            name='shift_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='shift_id2in_reg', to='shift_setup.in_shifts'),
        ),
    ]
