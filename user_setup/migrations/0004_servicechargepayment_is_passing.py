# Generated by Django 4.1.5 on 2025-06-17 07:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_setup', '0003_servicechargepayment_reference_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='servicechargepayment',
            name='is_passing',
            field=models.BooleanField(default=False),
        ),
    ]
