# Generated by Django 4.1.5 on 2025-05-07 06:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('class_setup', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='in_class',
            name='allow_groups',
            field=models.BooleanField(default=False),
        ),
    ]
