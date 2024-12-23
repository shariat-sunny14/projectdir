# Generated by Django 4.1.5 on 2024-10-18 15:24

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('stock_list', '0002_initial'),
        ('organizations', '0002_initial'),
        ('store_setup', '0001_initial'),
        ('G_R_N_with_without', '0003_initial'),
        ('item_setup', '0003_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='stock_lists',
            name='ss_creator',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='ss_creator2stock_lists', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='stock_lists',
            name='ss_modifier',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='ss_modifier2stock_lists', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='stock_lists',
            name='store_id',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='store_id2stock_lists', to='store_setup.store'),
        ),
        migrations.AddField(
            model_name='stock_lists',
            name='wo_grn_id',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='wo_grn_id2stock_lists', to='G_R_N_with_without.without_grn'),
        ),
        migrations.AddField(
            model_name='stock_lists',
            name='wo_grndtl_id',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='wo_grndtl_id2stock_lists', to='G_R_N_with_without.without_grndtl'),
        ),
        migrations.AddField(
            model_name='in_stock',
            name='item_id',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='item_id2in_stock', to='item_setup.items'),
        ),
        migrations.AddField(
            model_name='in_stock',
            name='org_id',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='org_id2in_stock', to='organizations.organizationlst'),
        ),
        migrations.AddField(
            model_name='in_stock',
            name='store_id',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='store_id2in_stock', to='store_setup.store'),
        ),
    ]
