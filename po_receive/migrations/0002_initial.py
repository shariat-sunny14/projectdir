# Generated by Django 4.1.5 on 2024-10-18 15:24

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('purchase_order', '0001_initial'),
        ('store_setup', '0001_initial'),
        ('po_receive', '0001_initial'),
        ('item_setup', '0003_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='po_receive_details',
            name='is_received_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='user_id2pordtls', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='po_receive_details',
            name='item_id',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='item_id2pordtls', to='item_setup.items'),
        ),
        migrations.AddField(
            model_name='po_receive_details',
            name='po_id',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='po_id2pordtls', to='purchase_order.purchase_order_list'),
        ),
        migrations.AddField(
            model_name='po_receive_details',
            name='ss_creator',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='ss_creator2pordtls', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='po_receive_details',
            name='ss_modifier',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='ss_modifier2pordtls', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='po_receive_details',
            name='store_id',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='store_id2pordtls', to='store_setup.store'),
        ),
    ]
