import sys
import json
import os
from django.conf import settings
from datetime import date, timedelta
from django.forms.models import model_to_dict
from django.db.models import Q, Sum, F, ExpressionWrapper, FloatField, Count
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from G_R_N_with_without.models import without_GRN
from item_pos.models import invoice_list, invoicedtl_list
from local_purchase.models import local_purchase
from manual_return_receive.models import manual_return_receive
from deliver_chalan.models import delivery_Chalandtl_list
from organizations.models import organizationlst
from stock_reconciliation.models import item_reconciliation
from store_transfers.models import stock_transfer_list


def save_notification_data_json():
    today = date.today()
    seven_days_ago = today - timedelta(days=7)
    org_branch_data = {}
    total_data_count_map = {}

    # ✅ Fetch active organizations and their feature flags
    org_flags = organizationlst.objects.filter(is_active=True).values(
        'org_id', 'is_delivery_chalan', 'is_grn', 'is_lp', 'is_mrr', 'is_store_trans', 'is_stock_recon'
    )

    org_feature_map = {
        str(org['org_id']): {
            'is_delivery_chalan': org['is_delivery_chalan'],
            'is_grn': org['is_grn'],
            'is_lp': org['is_lp'],
            'is_mrr': org['is_mrr'],
            'is_store_trans': org['is_store_trans'],
            'is_stock_recon': org['is_stock_recon'],
        }
        for org in org_flags
    }

    # ✅ Extract all org_id + branch_id combinations (regardless of delivery_chalan flag)
    inv_queryset = invoice_list.objects.filter(
        invoice_date__range=(seven_days_ago, today))
    inv_group = inv_queryset.values('org_id', 'branch_id').distinct()

    for group in inv_group:
        org_id = group['org_id']
        branch_id = group['branch_id']
        org_id_str = str(org_id)
        key = f"{org_id}_{branch_id}"

        # Always initialize total_data_count_map with 0
        total_data_count_map[key] = 0

        # ✅ Only collect invoice data if delivery_chalan flag is True
        if org_feature_map.get(org_id_str, {}).get('is_delivery_chalan', False):
            inv_list = invoice_list.objects.filter(
                org_id=org_id, branch_id=branch_id,
                invoice_date__range=(seven_days_ago, today)
            )
            pen_del_chalan_count = 0
            invoice_details = []

            for inv in inv_list:
                inv_dtls = invoicedtl_list.objects.filter(inv_id=inv).annotate(
                    effective_qty=ExpressionWrapper(
                        F('qty') - F('is_cancel_qty'), output_field=FloatField())
                )
                total_qty = inv_dtls.aggregate(
                    total=Sum('effective_qty'))['total'] or 0

                chalan_dtls = delivery_Chalandtl_list.objects.filter(inv_id=inv).annotate(
                    effective_deliver_qty=ExpressionWrapper(
                        F('deliver_qty') - F('is_cancel_qty'), output_field=FloatField())
                )
                delivered_qty = chalan_dtls.aggregate(
                    total=Sum('effective_deliver_qty'))['total'] or 0

                if total_qty > delivered_qty:
                    pen_del_chalan_count += 1
                    invoice_details.append({
                        'inv_id': inv.inv_id,
                        'invoice_date': str(inv.invoice_date),
                        'customer_name': inv.customer_name,
                        'mobile_number': inv.mobile_number,
                        'branch_name': inv.branch_id.branch_name,
                    })

            org_branch_data[key] = {
                'org_id': org_id,
                'branch_id': branch_id,
                'pen_del_chalan_count': pen_del_chalan_count,
                'details': invoice_details
            }

            total_data_count_map[key] += pen_del_chalan_count

    # ---------------------- Helper Function ----------------------
    def group_by_org_with_check(model, flag_name, detail_fields=None):
        grouped = {}
        if detail_fields is None:
            detail_fields = []

        # qs = model.objects.all().select_related('store_id', 'branch_id')
        # Use custom select_related fields based on model
        if model == stock_transfer_list:
            qs = model.objects.select_related('from_store', 'to_store', 'branch_id')
        else:
            qs = model.objects.select_related('store_id', 'branch_id')
            
        org_groups = qs.values('id_org').distinct()

        for group in org_groups:
            org_id = group['id_org']
            org_id_str = str(org_id)

            if not org_feature_map.get(org_id_str, {}).get(flag_name, False):
                continue

            key = str(org_id)
            records = qs.filter(id_org=org_id, is_approved=False)
            unapproved_count = records.count()

            detail_data = []
            for record in records:
                detail = {}
                for field in detail_fields:
                    parts = field.split('.')
                    if len(parts) == 2:
                        related_obj = getattr(record, parts[0], None)
                        value = getattr(
                            related_obj, parts[1], None) if related_obj else None
                    else:
                        value = getattr(record, field, None)
                    detail[field] = value
                detail['status'] = 'Unapprove'
                detail_data.append(detail)

            grouped[key] = {
                'unapproved_count': unapproved_count,
                'details': detail_data
            }

            # ✅ Update all matching org_id_branch_id combinations
            for k in total_data_count_map.keys():
                if k.startswith(f"{key}_"):
                    total_data_count_map[k] += unapproved_count

        return grouped

    # ---------------------- GRN, LP, MRR, Stock Transfer ----------------------
    grn_data = group_by_org_with_check(
        without_GRN, 'is_grn',
        detail_fields=[
            'wo_grn_id', 'wo_grn_no', 'transaction_date',
            'invoice_no', 'invoice_date',
            'supplier_id.supplier_name', 'store_id.store_name',
            'branch_id.branch_name'
        ]
    )

    lp_data = group_by_org_with_check(
        local_purchase, 'is_lp',
        detail_fields=[
            'lp_id', 'lp_no', 'reg_id.full_name', 'store_id.store_name',
            'invoice_no', 'invoice_date', 'transaction_date',
            'branch_id.branch_name'
        ]
    )

    mretrec_data = group_by_org_with_check(
        manual_return_receive, 'is_mrr',
        detail_fields=[
            'manu_ret_rec_id', 'manu_ret_rec_no', 'reg_id.full_name', 'store_id.store_name',
            'invoice_no', 'invoice_date', 'transaction_date',
            'branch_id.branch_name'
        ]
    )
    
    trans_data = group_by_org_with_check(
        stock_transfer_list, 'is_store_trans',
        detail_fields=[
            'stock_trans_id', 'stock_trans_no', 'transaction_date',
            'from_store.store_name', 'to_store.store_name',
            'branch_id.branch_name'
        ]
    )
    
    
    stock_recon_data = group_by_org_with_check(
        item_reconciliation, 'is_stock_recon',
        detail_fields=[
            'recon_id', 'recon_no', 'recon_date', 'recon_type',
            'store_id.store_name', 'branch_id.branch_name'
        ]
    )

    # ---------------------- Final JSON Save ----------------------
    response = {
        'grouped_invoice': org_branch_data,
        'grouped_grn': grn_data,
        'grouped_lp': lp_data,
        'grouped_mretrec': mretrec_data,
        'grouped_trans': trans_data,
        'grouped_stock_recon': stock_recon_data,
        'total_data_count': total_data_count_map,
    }

    try:
        folder_path = os.path.join(settings.BASE_DIR, 'notification_data')
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, 'notification_data.json')
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(response, f, ensure_ascii=False, indent=4, default=str)
    except Exception as e:
        print("Error saving notification JSON:", e)

    # # No more filtering by today
    # org_branch_data = {}
    # inv_queryset = invoice_list.objects.all()
    # inv_group = inv_queryset.values('org_id', 'branch_id').distinct()

    # for group in inv_group:
    #     org_id = group['org_id']
    #     branch_id = group['branch_id']
    #     key = f"{org_id}_{branch_id}"

    #     inv_list = invoice_list.objects.filter(org_id=org_id, branch_id=branch_id)
    #     pen_del_chalan_count = 0

    #     for inv in inv_list:
    #         inv_dtls = invoicedtl_list.objects.filter(inv_id=inv).annotate(
    #             effective_qty=ExpressionWrapper(F('qty') - F('is_cancel_qty'), output_field=FloatField())
    #         )
    #         total_qty = inv_dtls.aggregate(total=Sum('effective_qty'))['total'] or 0

    #         chalan_dtls = delivery_Chalandtl_list.objects.filter(inv_id=inv).annotate(
    #             effective_deliver_qty=ExpressionWrapper(F('deliver_qty') - F('is_cancel_qty'), output_field=FloatField())
    #         )
    #         delivered_qty = chalan_dtls.aggregate(total=Sum('effective_deliver_qty'))['total'] or 0

    #         if total_qty > delivered_qty:
    #             pen_del_chalan_count += 1

    #     org_branch_data[key] = {
    #         'org_id': org_id,
    #         'branch_id': branch_id,
    #         'pen_del_chalan_count': pen_del_chalan_count or 0
    #     }

    # def group_by_org(model, org_field='id_org', approved_field='is_approved'):
    #     data = {}
    #     qs = model.objects.all().values(org_field).annotate(
    #         unapproved_count=Count(org_field, filter=Q(**{approved_field: False}))
    #     )
    #     for row in qs:
    #         org_key = str(row[org_field])
    #         data[org_key] = row['unapproved_count']
    #     return data

    # grn_data = group_by_org(without_GRN)
    # lp_data = group_by_org(local_purchase)
    # mretrec_data = group_by_org(manual_return_receive)

    # response = {
    #     'grouped_invoice': org_branch_data,
    #     'grouped_grn': grn_data,
    #     'grouped_lp': lp_data,
    #     'grouped_mretrec': mretrec_data,
    # }

    # try:
    #     folder_path = os.path.join(settings.BASE_DIR, 'notification_data')
    #     os.makedirs(folder_path, exist_ok=True)
    #     file_path = os.path.join(folder_path, 'notification_data.json')
    #     with open(file_path, 'w', encoding='utf-8') as f:
    #         json.dump(response, f, ensure_ascii=False, indent=4)
    # except Exception as e:
    #     print("Error saving notification JSON:", e)


# def save_notification_data_json():
#     today = date.today()

#     # Grouping delivery chalans by org_id and branch_id
#     org_branch_data = {}
#     inv_queryset = invoice_list.objects.filter(invoice_date=today)
#     inv_group = inv_queryset.values('org_id', 'branch_id').distinct()

#     for group in inv_group:
#         org_id = group['org_id']
#         branch_id = group['branch_id']
#         key = f"{org_id}_{branch_id}"

#         inv_list = invoice_list.objects.filter(invoice_date=today, org_id=org_id, branch_id=branch_id)
#         pen_del_chalan_count = 0

#         for inv in inv_list:
#             inv_dtls = invoicedtl_list.objects.filter(inv_id=inv).annotate(
#                 effective_qty=ExpressionWrapper(F('qty') - F('is_cancel_qty'), output_field=FloatField())
#             )
#             total_qty = inv_dtls.aggregate(total=Sum('effective_qty'))['total'] or 0

#             chalan_dtls = delivery_Chalandtl_list.objects.filter(inv_id=inv).annotate(
#                 effective_deliver_qty=ExpressionWrapper(F('deliver_qty') - F('is_cancel_qty'), output_field=FloatField())
#             )
#             delivered_qty = chalan_dtls.aggregate(total=Sum('effective_deliver_qty'))['total'] or 0

#             if total_qty > delivered_qty:
#                 pen_del_chalan_count += 1

#         org_branch_data[key] = {
#             'org_id': org_id,
#             'branch_id': branch_id,
#             'pen_del_chalan_count': pen_del_chalan_count or 0
#         }

#     # Grouping GRN/LP/MRetRec by org_id
#     def group_by_org(model, org_field='id_org', approved_field='is_approved'):
#         data = {}
#         qs = model.objects.filter(transaction_date=today).values(org_field).annotate(
#             unapproved_count=Count(org_field, filter=Q(**{approved_field: False}))
#         )
#         for row in qs:
#             org_key = str(row[org_field])
#             data[org_key] = row['unapproved_count']
#         return data

#     grn_data = group_by_org(without_GRN)
#     lp_data = group_by_org(local_purchase)
#     mretrec_data = group_by_org(manual_return_receive)

#     response = {
#         'grouped_invoice': org_branch_data,
#         'grouped_grn': grn_data,
#         'grouped_lp': lp_data,
#         'grouped_mretrec': mretrec_data,
#     }

#     # Save as JSON
#     try:
#         folder_path = os.path.join(settings.BASE_DIR, 'notification_data')
#         os.makedirs(folder_path, exist_ok=True)  # ensure folder exists

#         file_path = os.path.join(folder_path, 'notification_data.json')
#         with open(file_path, 'w', encoding='utf-8') as f:
#             json.dump(response, f, ensure_ascii=False, indent=4)
#     except Exception as e:
#         print("Error saving notification JSON:", e)
