# Generated by Django 4.1.5 on 2024-11-24 16:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('item_pos', '0009_remove_reward_points_reward_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment_list',
            name='descriptions',
            field=models.CharField(blank=True, max_length=150, null=True),
        ),
    ]
