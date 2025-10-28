import sys
import json
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from datetime import datetime
from django.db import transaction, IntegrityError
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.db.models import Q, F, Sum, ExpressionWrapper, fields, FloatField
from django.contrib import messages
from item_setup.models import items
from store_setup.models import store
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from organizations.models import branchslist, organizationlst
from stock_list.stock_qty import get_available_qty
from registrations.models import in_registrations
from local_purchase.models import local_purchase, local_purchasedtl
from local_purchase_return.models import lp_return_details
from bank_statement.models import cash_on_hands
from supplier_setup.models import suppliers
from stock_list.models import in_stock, stock_lists
from item_pos.models import invoicedtl_list
from opening_stock.models import opening_stockdtl
from others_setup.models import item_type
from user_auth.utils.notification_data_context import save_notification_data_json
from user_setup.models import access_list
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def lPReturnListManagerAPI(request):
    user = request.user

    if user.is_superuser:
        # If the user is a superuser, retrieve all organizations
        org_list = organizationlst.objects.filter(is_active=True).all()
    elif user.org_id is not None:
        # If the user has an associated organization, retrieve only that organization
        org_list = organizationlst.objects.filter(is_active=True, org_id=user.org_id).all()
    else:
        # If neither a superuser nor associated with an organization, set organizations to an empty list or handle as needed
        org_list = []
    
    billingBtn_access = access_list.objects.filter(
        user_id=user,
        feature_id__feature_page_link='BILLINGFORMACCESSBTN',
        is_active=True
    ).exists()
    
    context = {
        'org_list': org_list,
        'billingBtn_access': billingBtn_access,
    }
    return render(request, 'local_purchase_return/local_purchase_return_list.html', context)


@login_required()
def getLocalPurchaseReturnListAPI(request):
    pol_option = request.GET.get('pol_option')
    org_id_wise_filter = request.GET.get('filter_org', '')
    branch_id_wise_filter = request.GET.get('filter_branch', '')
    po_start = request.GET.get('op_start')
    po_end = request.GET.get('op_end')

    filter_kwargs = Q()  # Initialize an empty Q object

    # Add org_id filter condition only if org_id_wise_filter is not empty
    if org_id_wise_filter:
        filter_kwargs &= Q(id_org=org_id_wise_filter)
    
    if branch_id_wise_filter:
        filter_kwargs &= Q(branch_id=branch_id_wise_filter)

    # Add is_active filter condition based on typeoption
    if pol_option == 'true':
        filter_kwargs &= Q(is_returned=True)
    elif pol_option == 'false':
        filter_kwargs &= Q(is_returned=False)

    # Add date range filter conditions with validation
    try:
        if po_start:
            start_date = datetime.strptime(po_start, '%Y-%m-%d')
            filter_kwargs &= Q(transaction_date__gte=start_date)
        if po_end:
            end_date = datetime.strptime(po_end, '%Y-%m-%d')
            filter_kwargs &= Q(transaction_date__lte=end_date)
    except ValueError as e:
        return JsonResponse({'error': f'Invalid date format: {e}'}, status=400)

    # Query the data
    lp_data = local_purchase.objects.filter(is_approved=True).filter(filter_kwargs)

    # Prepare response data
    data = []
    for lp_list in lp_data:
        org_name = lp_list.id_org.org_name if lp_list.id_org else None
        branch_name = lp_list.branch_id.branch_name if lp_list.branch_id else None
        store_name = lp_list.store_id.store_name if lp_list.store_id else None
        is_returned_by_first = lp_list.is_returned_by.first_name if lp_list.is_returned_by else ""
        is_returned_by_last = lp_list.is_returned_by.last_name if lp_list.is_returned_by else ""
        returned_date = lp_list.returned_date if lp_list.returned_date is not None else ""
        data.append({
            'lp_id': lp_list.lp_id,
            'lp_no': lp_list.lp_no,
            'clients_name': lp_list.reg_id.full_name if lp_list.reg_id else lp_list.cus_clients_name,
            'mobile_number': lp_list.reg_id.mobile_number if lp_list.reg_id else lp_list.cus_mobile_number,
            'transaction_date': lp_list.transaction_date,
            'returned_date': returned_date,
            'org_name': org_name,
            'branch_name': branch_name,
            'store_name': store_name,
            'invoice_no': lp_list.invoice_no,
            'invoice_date': lp_list.invoice_date,
            'is_returned': lp_list.is_returned,
            'is_returned_by_first': is_returned_by_first,
            'is_returned_by_last': is_returned_by_last,
        })

    return JsonResponse({'data': data})


# Local Purchase Return
@login_required()
def localPurchaseReturnManagerAPI(request):
    user = request.user

    if user.is_superuser:
        # If the user is a superuser, retrieve all organizations
        org_list = organizationlst.objects.filter(is_active=True).all()
    elif user.org_id is not None:
        # If the user has an associated organization, retrieve only that organization
        org_list = organizationlst.objects.filter(is_active=True, org_id=user.org_id).all()
    else:
        # If neither a superuser nor associated with an organization, set organizations to an empty list or handle as needed
        org_list = []
        
    context = {
        'org_list': org_list,
    }
    # # Fetch active items and main stores ordered by store_no
    # items_data = items.objects.filter(is_active=True)
    # stores = store.objects.filter(is_main_store=1).order_by('store_no')

    # ops_data = local_purchase.objects.filter(pk=lp_id).first() if lp_id else None
    # ops_details = local_purchasedtl.objects.filter(lp_id=ops_data) if ops_data else []

    # # Exclude the store of the current purchase if it exists
    # if ops_data:
    #     stores = stores.exclude(store_id=ops_data.store_id.store_id)

    # item_with_ops_dtls = []
    # grand_total_qty = grand_po_rec_qty = grand_po_return_qty = grand_is_canceled_qty = 0

    # for item in items_data:
    #     store_instance = ops_data.store_id if ops_data else None
    #     lp_id_instance = ops_data.lp_id if ops_data else None

    #     # Fetch PO received and return quantities
    #     po_rec_qty = (
    #         local_purchasedtl.objects.filter(item_id=item, lp_id=lp_id_instance)
    #         .aggregate(total=Sum(F('lp_rec_qty'), output_field=FloatField()))['total'] or 0
    #     )
    #     po_return_qty = (
    #         lp_return_details.objects.filter(item_id=item, lp_id=lp_id_instance)
    #         .aggregate(total=Sum(F('lp_return_qty'), output_field=FloatField()))['total'] or 0
    #     )

    #     is_canceled_qty = (
    #         lp_return_details.objects.filter(item_id=item, lp_id=lp_id_instance)
    #         .aggregate(total=Sum(F('is_cancel_qty'), output_field=FloatField()))['total'] or 0
    #     )

    #     # Aggregate totals
    #     grand_po_rec_qty += po_rec_qty
    #     grand_po_return_qty += po_return_qty
    #     grand_is_canceled_qty += is_canceled_qty

    #     # Fetch available quantity from helper function
    #     available_qty = get_available_qty(item.item_id, store_instance.store_id, item.org_id) if store_instance else 0
    #     grand_total_qty += available_qty

    #     # Fetch relevant order details for the item
    #     order_detail = next((od for od in ops_details if od.item_id == item), None)

    #     if order_detail:
    #         item_with_ops_dtls.append({
    #             'grandQty': available_qty,
    #             'ops_dtls': order_detail,
    #             'totalPoRecQty': po_rec_qty,
    #             'totalIsCanceledQty': is_canceled_qty,
    #             'totalPoReturnQty': po_return_qty,
    #             'order_qty': order_detail.lp_rec_qty,
    #             'unit_price': order_detail.unit_price,
    #             'ops_Data': ops_data,
    #         })

    # context = {
    #     'item_with_opsDtls': item_with_ops_dtls,
    #     'store_data': stores,
    #     'ops_Data': ops_data,
    #     'total_grandQty': grand_total_qty,
    # }
    return render(request, 'local_purchase_return/local_purchase_return.html', context)


@login_required()
def localPurchaseReturnDetailsManagerAPI(request):
    lp_id = request.GET.get('lp_id')
    if not lp_id:
        return JsonResponse({'data': []}, safe=False)
    
    lp_dataDtls = local_purchase.objects.filter(pk=lp_id).first() if lp_id else None

    # Get purchase master
    ops_data = local_purchase.objects.select_related('store_id').filter(pk=lp_id).first()
    if not ops_data:
        return JsonResponse({'data': []}, safe=False)

    store_id = ops_data.store_id_id
    lp_id_instance = ops_data.lp_id

    # Pre-fetch items used in local_purchasedtl only
    item_ids_in_ops = local_purchasedtl.objects.filter(lp_id=lp_id_instance).values_list('item_id', flat=True)
    items_data = items.objects.filter(item_id__in=item_ids_in_ops, is_active=True).select_related('item_uom_id')

    # Ops Details Map
    ops_details_qs = local_purchasedtl.objects.filter(lp_id=lp_id_instance).select_related('item_id')
    ops_details_map = {d.item_id_id: d for d in ops_details_qs}

    # Return Details Summary
    return_summary = lp_return_details.objects.filter(lp_id=lp_id_instance).values('item_id').annotate(
        returned_qty=Sum('lp_return_qty'),
        is_canceled_qty=Sum('is_cancel_qty'),
    )
    return_map = {
        d['item_id']: {'returned_qty': d['returned_qty'] or 0, 'is_canceled_qty': d['is_canceled_qty'] or 0}
        for d in return_summary
    }

    # Received Quantity Summary
    received_qty = local_purchasedtl.objects.filter(lp_id=lp_id_instance).values('item_id').annotate(
        total=Sum(F('lp_rec_qty'), output_field=FloatField())
    )
    received_qty_map = {d['item_id']: d['total'] or 0 for d in received_qty}

    # Stock Quantity Map
    in_stock_data = in_stock.objects.filter(
        item_id__in=item_ids_in_ops,
        store_id=store_id
    ).values('item_id', 'stock_qty')
    stock_qty_map = {d['item_id']: d['stock_qty'] for d in in_stock_data}

    # Final Output
    result_data = []
    for item in items_data:
        item_id = item.item_id
        od = ops_details_map.get(item_id)
        if not od:
            continue

        result_data.append({
            'item_no': item.item_no,
            'item_id': item_id,
            'item_name': item.item_name,
            'uom_name': item.item_uom_id.item_uom_name if item.item_uom_id else '',
            'stock_qty': stock_qty_map.get(item_id, 0),
            'received_qty': received_qty_map.get(item_id, 0),
            'returned_qty': return_map.get(item_id, {}).get('returned_qty', 0),
            'is_canceled_qty': return_map.get(item_id, {}).get('is_canceled_qty', 0),
            'return_qty': 0,
            'item_batch': od.item_batch,
            'unit_price': od.unit_price,
            'dis_percentage': od.dis_percentage,
            'total_amt': 0,
        })

    return JsonResponse({
        'data': result_data,
        'lp_dataDtls': {
            'lp_id': lp_dataDtls.lp_id,
            'lp_no': lp_dataDtls.lp_no,
            'transaction_date': lp_dataDtls.transaction_date.strftime('%Y-%m-%d') if lp_dataDtls.transaction_date else '',
            'invoice_no': lp_dataDtls.invoice_no,
            'cus_clients_name': lp_dataDtls.cus_clients_name,
            'cus_mobile_number': lp_dataDtls.cus_mobile_number,
            'cus_emrg_person': lp_dataDtls.cus_emrg_person,
            'cus_emrg_mobile': lp_dataDtls.cus_emrg_mobile,
            'cus_address': lp_dataDtls.cus_address,
            'cus_gender': lp_dataDtls.cus_gender,
            'is_cash': lp_dataDtls.is_cash,
            'is_credit': lp_dataDtls.is_credit,
            'store_id': lp_dataDtls.store_id.store_id if lp_dataDtls.store_id else None,
            'org_id': lp_dataDtls.id_org.org_id if lp_dataDtls.id_org else None,
            'branch_id': lp_dataDtls.branch_id.branch_id if lp_dataDtls.branch_id else None,
            'reg_id': lp_dataDtls.reg_id.reg_id if lp_dataDtls.reg_id else None,
            'store_name': lp_dataDtls.store_id.store_name if lp_dataDtls.store_id else '',
            'org_name': lp_dataDtls.id_org.org_name if lp_dataDtls.id_org else '',
            'branch_name': lp_dataDtls.branch_id.branch_name if lp_dataDtls.branch_id else '',
        } if lp_dataDtls else {}
    }, safe=False)



@login_required()
@csrf_exempt
def saveLocalpurchaseReturnedManagerAPI(request):
    if request.method == 'POST':
        try:
            # Parse the incoming JSON data
            data = json.loads(request.body)

            # Extract data for returned invoices and canceled details
            returnInvoiceData = data.get('returnInvoiceData', [])
            cancelDetailData = data.get('cancelDetailData', [])

            if not returnInvoiceData and not cancelDetailData:
                return JsonResponse({'errmsg': 'No data provided to process.'}, status=400)

            # Helper function for validating models
            def get_instance_or_error(model, field_name, field_value, error_message):
                instance = model.objects.filter(**{field_name: field_value}).first()
                if not instance:
                    raise ValueError(error_message)
                return instance

            # Helper function to calculate final amount
            def calculate_final_amount(qty, price, discount):
                total_amt = qty * price
                total_discount_amt = total_amt * (discount / 100)
                return total_amt - total_discount_amt

            # Start a database transaction
            with transaction.atomic():
                # Process Return Invoice Data
                for invoice in returnInvoiceData:
                    # Extract fields
                    lp_id = invoice.get('lp_id')
                    item_id = invoice.get('item_id')
                    lp_return_qty = float(invoice.get('lp_return_qty', 0))
                    item_batch = invoice.get('item_batch', "")
                    id_current_store = invoice.get('id_current_store')
                    returned_date_ind = invoice.get('returned_date_ind', "")
                    user_id_by = invoice.get('user_id_by')
                    returned_remarks = invoice.get('returned_remarks', "")
                    org_id = invoice.get('org_id')
                    branch_id = invoice.get('branch_id')
                    returned_date = invoice.get('returned_date', "")
                    is_returned = invoice.get('is_returned', "")

                    # Validate instances
                    lp_instance = get_instance_or_error(local_purchase, 'lp_id', lp_id, f'Local Purchase with ID {lp_id} not found.')
                    store_instance = get_instance_or_error(store, 'store_id', id_current_store, f'Store with ID {id_current_store} not found.')
                    org_instance = get_instance_or_error(organizationlst, 'org_id', org_id, f'Organization with ID {org_id} not found.')
                    branch_instance = get_instance_or_error(branchslist, 'branch_id', branch_id, f'Branch with ID {branch_id} not found.')
                    item_instance = get_instance_or_error(items, 'item_id', item_id, f'Item with ID {item_id} not found.')
                    user_instance = User.objects.filter(id=user_id_by).first() if user_id_by else None

                    # Fetch purchase details
                    lp_details = local_purchasedtl.objects.filter(lp_id=lp_instance).first()
                    unit_price = lp_details.unit_price if lp_details else 0
                    dis_perc = lp_details.dis_percentage if lp_details else 0

                    # Save returned data
                    lp_return_dtl = lp_return_details.objects.create(
                        lp_id=lp_instance,
                        item_id=item_instance,
                        lp_return_qty=lp_return_qty,
                        is_cancel_qty=0.0,
                        is_returned=True,
                        is_canceled=False,
                        item_batch=item_batch,
                        store_id=store_instance,
                        returned_date=returned_date_ind,
                        is_returned_by=user_instance,
                        returned_remarks=returned_remarks,
                    )

                    final_amt = calculate_final_amount(lp_return_qty, unit_price, dis_perc)
                    finalAmts = float(final_amt)
                    if finalAmts > 0:
                        # Handle cash on hand updates
                        if bool(lp_instance.is_cash):
                            cashOnHands, created = cash_on_hands.objects.get_or_create(
                                org_id=org_instance,
                                branch_id=branch_instance,
                                defaults={'on_hand_cash': 0}
                            )
                            cashOnHands.on_hand_cash = F('on_hand_cash') + finalAmts
                            cashOnHands.save()
                            cashOnHands.refresh_from_db()

                    # Save stock data
                    stock_lists.objects.create(
                        lp_id=lp_instance,
                        lprdtl_id=lp_return_dtl,
                        item_id=item_instance,
                        stock_qty=lp_return_qty,
                        is_cancel_qty=0.0,
                        store_id=store_instance,
                        item_batch=item_batch,
                        is_approved=True,
                        approved_date=returned_date_ind,
                        recon_type=False,
                        ss_creator=request.user,
                        ss_modifier=request.user,
                    )

                    # Update stock quantity in the in_stock model
                    in_stock_obj, _ = in_stock.objects.get_or_create(
                        item_id=item_instance,
                        store_id=store_instance,
                        defaults={'stock_qty': 0}
                    )
                    in_stock_obj.stock_qty -= lp_return_qty
                    in_stock_obj.save()

                    # Update local purchase instance
                    lp_instance.returned_date = returned_date
                    lp_instance.is_returned = is_returned
                    lp_instance.is_returned_by = user_instance
                    lp_instance.ss_modifier = request.user
                    lp_instance.save()

                # Process Cancel Detail Data
                for caninv in cancelDetailData:
                    # Extract fields
                    lp_id = caninv.get('lp_id')
                    item_id = caninv.get('item_id')
                    is_cancel_qty = float(caninv.get('is_cancel_qty', 0))
                    item_batch = caninv.get('item_batch', "")
                    id_current_store = caninv.get('id_current_store')
                    returned_date_ind = caninv.get('returned_date_ind', "")
                    user_id_by = caninv.get('user_id_by')
                    returned_remarks = caninv.get('returned_remarks', "")
                    org_id = invoice.get('org_id')
                    branch_id = invoice.get('branch_id')
                    returned_date = invoice.get('returned_date', "")
                    is_returned = invoice.get('is_returned', "")

                    # Validate instances
                    lp_instance = get_instance_or_error(local_purchase, 'lp_id', lp_id, f'Local Purchase with ID {lp_id} not found.')
                    store_instance = get_instance_or_error(store, 'store_id', id_current_store, f'Store with ID {id_current_store} not found.')
                    org_instance = get_instance_or_error(organizationlst, 'org_id', org_id, f'Organization with ID {org_id} not found.')
                    branch_instance = get_instance_or_error(branchslist, 'branch_id', branch_id, f'Branch with ID {branch_id} not found.')
                    item_instance = get_instance_or_error(items, 'item_id', item_id, f'Item with ID {item_id} not found.')
                    user_instance = User.objects.filter(id=user_id_by).first() if user_id_by else None

                    # Fetch purchase details
                    lp_details = local_purchasedtl.objects.filter(lp_id=lp_instance).first()
                    unit_price = lp_details.unit_price if lp_details else 0
                    dis_perc = lp_details.dis_percentage if lp_details else 0

                    # Save canceled data
                    can_lp_return_dtl = lp_return_details.objects.create(
                        lp_id=lp_instance,
                        item_id=item_instance,
                        lp_return_qty=0.0,
                        is_cancel_qty=is_cancel_qty,
                        is_returned=False,
                        is_canceled=True,
                        item_batch=item_batch,
                        store_id=store_instance,
                        returned_date=returned_date_ind,
                        is_returned_by=user_instance,
                        returned_remarks=returned_remarks,
                    )

                    final_can_amt = calculate_final_amount(is_cancel_qty, unit_price, dis_perc)
                    finalCanAmts = float(final_can_amt)
                    if finalCanAmts > 0:
                        # Handle cash on hand updates
                        if bool(lp_instance.is_cash):
                            cashOnHands, created = cash_on_hands.objects.get_or_create(
                                org_id=org_instance,
                                branch_id=branch_instance,
                                defaults={'on_hand_cash': 0}
                            )
                            cashOnHands.on_hand_cash = F('on_hand_cash') - finalCanAmts
                            cashOnHands.save()
                            cashOnHands.refresh_from_db()

                    # Save stock data
                    stock_lists.objects.create(
                        lp_id=lp_instance,
                        lprdtl_id=can_lp_return_dtl,
                        item_id=item_instance,
                        stock_qty=0.0,
                        is_cancel_qty=is_cancel_qty,
                        store_id=store_instance,
                        item_batch=item_batch,
                        is_approved=True,
                        approved_date=returned_date_ind,
                        recon_type=False,
                        ss_creator=request.user,
                        ss_modifier=request.user,
                    )

                    # Update stock quantity in the in_stock model
                    in_stock_obj, _ = in_stock.objects.get_or_create(
                        item_id=item_instance,
                        store_id=store_instance,
                        defaults={'stock_qty': 0}
                    )
                    in_stock_obj.stock_qty += is_cancel_qty
                    in_stock_obj.save()

                    # Update local purchase instance
                    lp_instance.returned_date = returned_date
                    lp_instance.is_returned = is_returned
                    lp_instance.is_returned_by = user_instance
                    lp_instance.ss_modifier = request.user
                    lp_instance.save()
            
                # Update notification JSON after invoice save
                save_notification_data_json()
                    
                return JsonResponse({'msg': 'LP Return details saved successfully.'})

        except ValueError as ve:
            return JsonResponse({'errmsg': str(ve)}, status=400)
        except Exception as e:
            print(f"Error: {str(e)}")  # For debugging purposes
            return JsonResponse({'errmsg': 'An error occurred while processing your request.'}, status=500)

























    # if request.method == 'POST':
    #     try:
    #         # Extract data from request
    #         lp_id = request.POST.get('lp_id')
    #         current_store_id = request.POST.get('current_store')
    #         returned_date = request.POST.get('returned_date')
    #         is_returned = request.POST.get('is_returned')
    #         is_returned_by = request.POST.get('is_returned_by')
    #         returned_remarks = request.POST.get('returned_remarks')
    #         org_id = request.POST.get('org')
    #         branch_id = request.POST.get('branchs')

    #         item_ids = request.POST.getlist('item_id[]')
    #         return_qtys = request.POST.getlist('return_qty[]')
    #         is_cancel_qtys = request.POST.getlist('is_cancel_qty[]')
    #         item_batchs = request.POST.getlist('item_batchs[]')
    #         is_returned_inds = request.POST.getlist('is_returned_ind[]')
    #         returned_date_ind = request.POST.get('returned_date_ind')

    #         is_canceleds = request.POST.getlist('is_canceled[]')
            

    #         # Debug: Print IDs to verify correctness
    #         print(f"lp_id: {lp_id}, current_store_id: {current_store_id}")

    #         # Start a database transaction
    #         with transaction.atomic():
    #             # Validate and get user instance
    #             user_instance = None
    #             if is_returned_by:
    #                 user_instance = User.objects.filter(user_id=is_returned_by).first()
    #                 if not user_instance:
    #                     return JsonResponse({'errmsg': 'User with the provided ID does not exist.'}, status=400)

    #             # Retrieve local purchase and store instances
    #             lp_instance = local_purchase.objects.filter(lp_id=lp_id).first()
    #             store_instance = store.objects.filter(store_id=current_store_id).first()
    #             org_instance = organizationlst.objects.filter(org_id=org_id).first()
    #             branch_instance = branchslist.objects.filter(branch_id=branch_id).first()

    #             if not lp_instance:
    #                 return JsonResponse({'errmsg': f'Local Purchase with ID {lp_id} not found.'}, status=404)
    #             if not store_instance:
    #                 return JsonResponse({'errmsg': f'Store with ID {current_store_id} not found.'}, status=404)

    #             # Fetch all related purchase details in one query
    #             lp_details = local_purchasedtl.objects.filter(lp_id=lp_id)

    #             # Loop through items and save return details
    #             for item_id, return_qty, is_cancel_qty, is_returned_ind, item_batch in zip(item_ids, return_qtys, is_cancel_qtys, is_returned_inds, item_batchs):
    #                 # Retrieve item instance
    #                 item_instance = items.objects.filter(item_id=item_id).first()
    #                 if not item_instance:
    #                     return JsonResponse({'errmsg': f'Item with ID {item_id} not found.'}, status=404)
                    
    #                 # Extract unit price and discount percentage from the purchase details
    #                 for lpdtls in lp_details:
    #                     unit_price = lpdtls.unit_price
    #                     dis_perc = lpdtls.dis_percentage

    #                 # Save local purchase return details
    #                 lp_return_dtl = lp_return_details(
    #                     lp_id=lp_instance,
    #                     store_id=store_instance,
    #                     item_id=item_instance,
    #                     lp_return_qty=float(return_qty) if float(return_qty) > 0 else 0,
    #                     is_cancel_qty=0.0,
    #                     item_batch=item_batch,
    #                     is_returned=is_returned_ind,
    #                     is_canceled=False,
    #                     returned_date=returned_date_ind,
    #                     returned_remarks=returned_remarks,
    #                     is_returned_by=user_instance,
    #                     ss_creator=request.user,
    #                     ss_modifier=request.user,
    #                 )
    #                 lp_return_dtl.save()

    #                 if is_canceleds:
    #                     lp_return_can_dtl = lp_return_details(
    #                         lp_id=lp_instance,
    #                         store_id=store_instance,
    #                         item_id=item_instance,
    #                         lp_return_qty=0.0,
    #                         is_cancel_qty=float(is_cancel_qty) if float(is_cancel_qty) > 0 else 0,
    #                         item_batch=item_batch,
    #                         is_returned=False,
    #                         is_canceled=is_canceleds,
    #                         returned_date=returned_date_ind,
    #                         returned_remarks=returned_remarks,
    #                         is_returned_by=user_instance,
    #                         ss_creator=request.user,
    #                         ss_modifier=request.user,
    #                     )
    #                     lp_return_can_dtl.save()


    #                 # Save stock data
    #                 stock_data = stock_lists(
    #                     lp_id=lp_instance,
    #                     lprdtl_id=lp_return_dtl,
    #                     item_id=item_instance,
    #                     stock_qty=float(return_qty) if float(return_qty) > 0 else 0,
    #                     is_cancel_qty=float(is_cancel_qty) if float(is_cancel_qty) > 0 else 0,
    #                     store_id=store_instance,
    #                     item_batch=item_batch,
    #                     is_approved=is_returned_ind,
    #                     approved_date=returned_date_ind,
    #                     recon_type=False,
    #                     ss_creator=request.user,
    #                     ss_modifier=request.user,
    #                 )
    #                 stock_data.save()

    #                 #############
    #                 # Get or create the cash_on_hands record
    #                 if lp_instance.is_cash == 1 or True:
    #                     cashOnHands, created = cash_on_hands.objects.get_or_create(
    #                         org_id=org_instance,
    #                         branch_id=branch_instance,
    #                         defaults={'on_hand_cash': 0}
    #                     )

    #                     # Calculate the amount for return or cancellation
    #                     def calculate_final_amount(qty, price, discount):
    #                         total_amt = qty * price
    #                         total_discount_amt = total_amt * (discount / 100)
    #                         return total_amt - total_discount_amt

    #                     # If there is a return quantity
    #                     if float(return_qty) > 0:
    #                         final_amt = calculate_final_amount(float(return_qty), unit_price, dis_perc)
    #                         # Add the final amount to on-hand cash
    #                         cashOnHands.on_hand_cash = F('on_hand_cash') + final_amt

    #                     # If there is a cancel quantity
    #                     elif float(is_cancel_qty) > 0:
    #                         final_amt = calculate_final_amount(float(is_cancel_qty), unit_price, dis_perc)
    #                         # Subtract the final amount from on-hand cash
    #                         cashOnHands.on_hand_cash = F('on_hand_cash') - final_amt

    #                     # Save and refresh the cashOnHands record
    #                     cashOnHands.save()
    #                     cashOnHands.refresh_from_db()

    #                 # Update stock quantity in the in_stock model
    #                 in_stock_obj, _ = in_stock.objects.get_or_create(
    #                     item_id=item_instance, store_id=store_instance, defaults={'stock_qty': 0}
    #                 )
    #                 if float(return_qty) > 0:
    #                     in_stock_obj.stock_qty -= float(return_qty)
    #                 elif float(is_cancel_qty) > 0:
    #                     in_stock_obj.stock_qty += float(is_cancel_qty)
    #                 in_stock_obj.save()

    #             # Update local purchase instance
    #             lp_instance.returned_date = returned_date
    #             lp_instance.is_returned = is_returned
    #             lp_instance.is_returned_by = user_instance
    #             lp_instance.ss_modifier = request.user
    #             lp_instance.save()

    #             return JsonResponse({'msg': 'LP Return details saved successfully.'})

    #     except Exception as e:
    #         # Log the exception for easier debugging
    #         print(f"Error: {str(e)}")
    #         return JsonResponse({'errmsg': str(e)}, status=500)

    # return JsonResponse({'errmsg': 'Invalid request method.'}, status=405)