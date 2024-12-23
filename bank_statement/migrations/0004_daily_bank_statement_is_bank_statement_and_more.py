# Generated by Django 4.1.5 on 2024-10-25 05:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bank_statement', '0003_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='daily_bank_statement',
            name='is_bank_statement',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='daily_bank_statement',
            name='is_branch_deposit',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='daily_bank_statement',
            name='is_branch_deposit_receive',
            field=models.BooleanField(default=False),
        ),
    ]
