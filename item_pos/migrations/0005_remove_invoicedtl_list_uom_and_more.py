# Generated by Django 4.1.5 on 2024-10-28 09:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('others_setup', '0002_initial'),
        ('item_pos', '0004_invoice_list_remarks_invoicedtl_list_uom'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='invoicedtl_list',
            name='uom',
        ),
        migrations.AddField(
            model_name='invoicedtl_list',
            name='item_uom_id',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='item_uom_id2invoicedtl', to='others_setup.item_uom'),
        ),
    ]
