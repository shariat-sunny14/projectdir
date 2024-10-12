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
from supplier_setup.models import suppliers
from stock_list.models import in_stock, stock_lists
from item_pos.models import invoicedtl_list
from opening_stock.models import opening_stockdtl
from others_setup.models import item_type
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def localPurchaselistManagerAPI(request):
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
    return render(request, 'local_purchase/local_purchase_list.html', context)


@login_required()
def getLocalPurchaseListAPI(request):
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
        filter_kwargs &= Q(is_approved=True)
    elif pol_option == 'false':
        filter_kwargs &= Q(is_approved=False)

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
    lp_data = local_purchase.objects.filter(filter_kwargs)

    # Prepare response data
    data = []
    for lp_list in lp_data:
        org_name = lp_list.id_org.org_name if lp_list.id_org else None
        branch_name = lp_list.branch_id.branch_name if lp_list.branch_id else None
        store_name = lp_list.store_id.store_name if lp_list.store_id else None
        is_approved_by_first = lp_list.is_approved_by.first_name if lp_list.is_approved_by else ""
        is_approved_by_last = lp_list.is_approved_by.last_name if lp_list.is_approved_by else ""
        data.append({
            'lp_id': lp_list.lp_id,
            'lp_no': lp_list.lp_no,
            'transaction_date': lp_list.transaction_date,
            'approved_date': lp_list.approved_date,
            'org_name': org_name,
            'branch_name': branch_name,
            'store_name': store_name,
            'invoice_no': lp_list.invoice_no,
            'invoice_date': lp_list.invoice_date,
            'is_approved': lp_list.is_approved,
            'is_approved_by_first': is_approved_by_first,
            'is_approved_by_last': is_approved_by_last,
        })

    return JsonResponse({'data': data})


# receive stock local purchase form
@login_required()
def receiveStockLocalPurchaseManagerAPI(request):
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

    return render(request, 'local_purchase/add_local_purchase.html', context)


# edit/update Local Purchase
@login_required()
def editUpdateLocalPurchaseManagerAPI(request, lp_id=None):
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
    
    
    # Get all active items
    item_data = items.objects.filter(is_active=True).all()

    lp_Data = local_purchase.objects.get(pk=lp_id) if lp_id else None

    # Query local_purchasedtl records related to the lpdtl_data
    lpdtl_data = local_purchasedtl.objects.filter(lp_id=lp_Data).all()

    item_with_lpDtls = []

    for item in item_data:
        store_instance = lp_Data.store_id if lp_Data else None
        org_instance = lp_Data.id_org if lp_Data else None
        
        available_qty = get_available_qty(item_id=item, store_id=store_instance, org_id=org_instance)
        
        # Find the associated lpdtl_data for this item
        lp_dtls = None
        for dtls in lpdtl_data:
            if dtls.item_id == item:
                lp_dtls = dtls
                break
        if lp_dtls:
            item_with_lpDtls.append({
                'grandQty': available_qty,
                'lp_dtls': lp_dtls,
            })

    context = {
        'org_list': org_list,
        'item_with_lpDtls': item_with_lpDtls,
        'lp_Data': lp_Data,
    }

    return render(request, 'local_purchase/edit_local_purchase.html', context)


@login_required()
def receiveLocalPurchaseStockAPI(request):
    resp = {'status': 'failed', 'errmsg': 'Failed ...'}
    data = request.POST

    id_org = data.get("org")
    branch_id = data.get("branchs")
    store_id =data.get("current_store")
    reg_id = data.get("reg_id")
    if reg_id == '' or reg_id is None:
        reg_id = None  # Handle empty or missing reg_id
    is_approved_by_user = data.get('is_approved_by_user_id')
    is_credit = data.get('is_credit', False)
    is_cash = data.get('is_cash', False)

    item_ids = data.getlist('item_id[]')
    item_qtys = data.getlist('item_qty[]')
    item_prices = data.getlist('item_price[]')
    dis_percentages = data.getlist('dis_percentage[]')
    item_batchs = data.getlist('item_batchs[]')
    item_exp_dates = data.getlist('item_exp_dates[]')
    is_approved = data['is_approved']

    clients_name = data['clients_name']
    cus_mobile_number = data['cus_mobile_number']
    cus_gender = data['cus_gender']
    cus_emrg_person = data['cus_emrg_person']
    cus_emrg_mobile = data['cus_emrg_mobile']
    cus_address = data['cus_address']
    
    # Handle invoice_no and invoice_date with fallback to None
    invoice_no = data.get('invoice_no') or None
    invoice_date = data.get('invoice_date') or None
    if invoice_date == '':
        invoice_date = None  # Set empty string to None

    store_instance = store.objects.get(store_id=store_id)
    
    # Create a list to store error messages for existing items
    existing_items_err_msgs = []

    for item_id, item_batch_value in zip(item_ids, item_batchs):
        # Fetch the item associated with the item_id
        item_instance = items.objects.get(item_id=item_id, org_id=id_org)

        # Check if an item with the same item_id exists in opening_stockdtl
        if local_purchasedtl.objects.filter(Q(item_id=item_instance) & Q(store_id=store_instance) & Q(item_batch__iexact=item_batch_value)).exists():
            errmsg = f"This Item: '{item_instance.item_name}' is already exists in this Batch No: '{item_batch_value}' and Store: '{store_instance.store_name}' Please.. Change the 'Batch No' ..."
            existing_items_err_msgs.append(errmsg)

    # Check if there are any existing items
    if existing_items_err_msgs:
        # If there are existing items, return an error response
        return JsonResponse({'success': False, 'errmsg': ', '.join(existing_items_err_msgs)})

    try:
        with transaction.atomic():
            try:
                user_instance = None
                if is_approved_by_user:
                    user_instance = User.objects.get(user_id=is_approved_by_user)
            except User.DoesNotExist:
                return JsonResponse({'errmsg': 'User with the provided ID does not exist.'}, status=400)

            org_instance = organizationlst.objects.get(org_id=id_org)
            branch_instance = branchslist.objects.get(branch_id=branch_id)

            reg_instance = None
            if reg_id:
                try:
                    reg_instance = in_registrations.objects.get(reg_id=reg_id)
                except in_registrations.DoesNotExist:
                    reg_instance = None  # Set reg_instance to None if not found

            receiveLP = local_purchase(
                id_org=org_instance,
                branch_id=branch_instance,
                reg_id=reg_instance,  # Save reg_instance as None if not found
                is_cash=is_cash,
                is_credit=is_credit,
                store_id=store_instance,
                transaction_date=data['transaction_date'],
                invoice_no=invoice_no,
                invoice_date=invoice_date,
                cus_clients_name=clients_name,
                cus_mobile_number=cus_mobile_number,
                cus_gender=cus_gender,
                cus_emrg_person=cus_emrg_person,
                cus_emrg_mobile=cus_emrg_mobile,
                cus_address=cus_address,
                is_approved=is_approved,
                is_approved_by=user_instance,
                approved_date=data['approved_date'],
                remarks=data['remarks'],
                ss_creator=request.user
            )
            receiveLP.save()

            for item_id, qty, item_price, dis_percentage, batch, exp_dates in zip(item_ids, item_qtys, item_prices, dis_percentages, item_batchs, item_exp_dates):
                item_instance = items.objects.get(item_id=item_id)

                # Handle null or empty expiration dates
                if exp_dates in [None, '']:
                    exp_dates = None  # Set to None for empty values

                rec_qty = float(qty)
                rec_dis_perc = float(dis_percentage)

                receiveLPDtl = local_purchasedtl(
                    lp_rec_qty=rec_qty,
                    unit_price=item_price,
                    dis_percentage=rec_dis_perc,
                    item_batch=batch,
                    item_exp_date=exp_dates,
                    item_id=item_instance,
                    lp_id=receiveLP,
                    store_id=store_instance,
                    reg_id=reg_instance,  # Save reg_instance as None if not found
                    lp_rec_date=receiveLP.transaction_date,
                    is_approved=receiveLP.is_approved,
                    approved_date=receiveLP.approved_date,
                    ss_creator=request.user
                )
                receiveLPDtl.save()

                stock_data = stock_lists(
                    lp_id=receiveLP,
                    lp_dtl_id=receiveLPDtl,
                    stock_qty=rec_qty,
                    item_batch=batch,
                    item_exp_date=exp_dates,
                    item_id=item_instance,
                    store_id=store_instance,
                    recon_type=True, #recon_type=True is adding item in stock list
                    is_approved=receiveLP.is_approved,
                    approved_date=receiveLP.approved_date,
                    ss_creator=request.user
                )
                stock_data.save()

                # Check if item and store combination exists in in_stock
                approved_status = receiveLP.is_approved
                        
                if approved_status == '1':
                    in_stock_obj, created = in_stock.objects.get_or_create(
                        item_id=item_instance,
                        store_id=store_instance,
                        defaults={
                            'stock_qty': rec_qty,
                        }
                    )
                    if not created:
                        # If the record exists, update the stock_qty
                        in_stock_obj.stock_qty += rec_qty
                        in_stock_obj.save()

            resp['status'] = 'success'
            return JsonResponse({'success': True, 'msg': 'Successful'})

    except organizationlst.DoesNotExist:
        resp['errmsg'] = 'Organization associated with the user does not exist.'
    except branchslist.DoesNotExist:
        resp['errmsg'] = 'Branch associated with the user does not exist.'
    except in_registrations.DoesNotExist:
        resp['errmsg'] = 'Registrations Client Not Found... Please Choose First!..'
    except IntegrityError as e:
        print(f"Integrity error occurred: {str(e)}")
        resp['errmsg'] = 'Database integrity error occurred. Please check your input.'
    except Exception as e:
        print(f"General error occurred: {str(e)}")
        resp['errmsg'] = f"Error: {str(e)}"

    return JsonResponse(resp)


@login_required()
def updateLocalPurchaseManagerAPI(request):
    resp = {'success': False, 'errmsg': 'Fails'}
    data = request.POST

    lp_id = data.get('lp_id')

    if lp_id.isnumeric() and int(lp_id) > 0:
        id_org = data.get("org")
        branch_id = data.get("branchs")
        store_id =data.get("current_store")
        reg_id = data.get("reg_id")
        if reg_id == '' or reg_id is None:
            reg_id = None  # Handle empty or missing reg_id
        is_approved_by_user = data.get('is_approved_by_user_id')
        is_credit = data.get('is_credit', False)
        is_cash = data.get('is_cash', False)

        item_ids = data.getlist('item_id[]')
        item_qtys = data.getlist('item_qty[]')
        item_prices = data.getlist('item_price[]')
        dis_percentages = data.getlist('dis_percentage[]')
        item_batchs = data.getlist('item_batchs[]')
        item_exp_dates = data.getlist('item_exp_dates[]')
        is_approved = data['is_approved']

        clients_name = data['clients_name']
        cus_mobile_number = data['cus_mobile_number']
        cus_gender = data['cus_gender']
        cus_emrg_person = data['cus_emrg_person']
        cus_emrg_mobile = data['cus_emrg_mobile']
        cus_address = data['cus_address']
        
        # Handle invoice_no and invoice_date with fallback to None
        invoice_no = data.get('invoice_no') or None
        invoice_date = data.get('invoice_date') or None
        if invoice_date == '':
            invoice_date = None  # Set empty string to None

        try:
            # Check if the user exists
            user_instance = None
            if is_approved_by_user:
                user_instance = User.objects.get(user_id=is_approved_by_user)
        except User.DoesNotExist:
            return JsonResponse({'errmsg': 'User with the provided ID does not exist.'}, status=400)

        try:
            store_instance = store.objects.get(store_id=store_id)
            org_instance = organizationlst.objects.get(org_id=id_org)
            branch_instance = branchslist.objects.get(branch_id=branch_id)
            lpreceivestock = local_purchase.objects.get(lp_id=lp_id)

            reg_instance = None
            if reg_id:
                try:
                    reg_instance = in_registrations.objects.get(reg_id=reg_id)
                except in_registrations.DoesNotExist:
                    reg_instance = None  # Set reg_instance to None if not found

            for item_id, item_batch_value in zip(item_ids, item_batchs):
                # Fetch the item associated with the item_id
                item_value = items.objects.get(item_id=item_id, org_id=id_org)

                # Check if the same combination of item_id, store_id, and item_batch exists in local_purchasedtl for another lp_id
                existing_items = local_purchasedtl.objects.filter(
                    Q(item_id=item_value) & Q(store_id=store_instance) & Q(item_batch__iexact=item_batch_value)
                ).exclude(lp_id=lpreceivestock)

                if existing_items.exists():
                    errmsg = f"This Item: '{item_value.item_name}' is already exists in this Batch No: '{item_batch_value}' and Store: '{store_instance.store_name}' Plz Change the Batch No..."
                    return JsonResponse({'success': False, 'errmsg': errmsg})

            # If it's already approved
            if lpreceivestock.is_approved:
                return JsonResponse({'success': False, 'errmsg': 'Already Approved!'})

            try:
                with transaction.atomic():
                    # Update the local_purchase instance
                    lpreceivestock.store_id = store_instance
                    lpreceivestock.id_org = org_instance
                    lpreceivestock.branch_id = branch_instance
                    lpreceivestock.reg_id = reg_instance
                    lpreceivestock.transaction_date = data.get('transaction_date')
                    lpreceivestock.invoice_no = invoice_no
                    lpreceivestock.invoice_date = invoice_date
                    lpreceivestock.is_approved = is_approved
                    lpreceivestock.is_approved_by = user_instance
                    lpreceivestock.approved_date = data.get('approved_date')
                    lpreceivestock.remarks = data.get('remarks') or ''
                    lpreceivestock.is_credit = is_credit
                    lpreceivestock.is_cash = is_cash
                    lpreceivestock.cus_clients_name = clients_name
                    lpreceivestock.cus_mobile_number = cus_mobile_number
                    lpreceivestock.cus_gender = cus_gender
                    lpreceivestock.cus_emrg_person = cus_emrg_person
                    lpreceivestock.cus_emrg_mobile = cus_emrg_mobile
                    lpreceivestock.cus_address = cus_address
                    lpreceivestock.ss_modifier = request.user
                    lpreceivestock.save()

                    # Update or create local_purchasedtl instances for each item
                    for item_id, item_price, qty, batch, exp_dates, dis_perc in zip(item_ids, item_prices, item_qtys, item_batchs, item_exp_dates, dis_percentages):
                        item_instance = items.objects.get(item_id=item_id)

                        lpreceivestockDtl, created = local_purchasedtl.objects.update_or_create(
                            lp_id=lpreceivestock,
                            item_id=item_instance,
                            defaults={
                                'lp_rec_qty': qty,
                                'item_batch': batch,
                                'item_exp_date': exp_dates or None,  # Handle empty string for item_exp_date
                                'store_id': store_instance,
                                'unit_price': item_price,
                                'dis_percentage': dis_perc,
                                'lp_rec_date': lpreceivestock.transaction_date,
                                'is_approved': lpreceivestock.is_approved,
                                'approved_date': lpreceivestock.approved_date,
                                'ss_modifier': request.user,
                            }
                        )

                        # Save the local_purchasedtl instance
                        lpreceivestockDtl.save()

                        # Update or create stock_lists
                        stock_data, created = stock_lists.objects.update_or_create(
                            lp_id=lpreceivestock,
                            lp_dtl_id=lpreceivestockDtl,
                            item_id=item_instance,
                            defaults={
                                'stock_qty': qty,
                                'item_batch': batch,
                                'item_exp_date': exp_dates or None,  # Handle empty string for item_exp_date
                                'store_id': store_instance,
                                'recon_type' : True, #recon_type=True is adding item in stock list
                                'is_approved': lpreceivestock.is_approved,
                                'approved_date': lpreceivestock.approved_date,
                                'ss_modifier': request.user
                            }
                        )

                        # Save the stock_lists instance
                        stock_data.save()

                        # Check if item and store combination exists in in_stock
                        approved_status = lpreceivestockDtl.is_approved
                        
                        # Check if item and store combination exists in in_stock
                        if approved_status == '1':
                            in_stock_obj, created = in_stock.objects.get_or_create(
                                item_id=item_instance,
                                store_id=store_instance,
                                defaults={
                                    'stock_qty': qty,
                                }
                            )
                            if not created:
                                # If the record exists, update the stock_qty
                                in_stock_obj.stock_qty += float(qty)
                                in_stock_obj.save()


                    resp['success'] = True
                    return JsonResponse({'success': True, 'msg': 'Successful'})
            except User.DoesNotExist:
                return JsonResponse({'errmsg': 'Transjection not submit.'}, status=400)
        except Exception as e:
            print("Error:", str(e))
            resp['errmsg'] = str(e)

    return HttpResponse(json.dumps(resp), content_type="application/json")



@method_decorator(csrf_exempt, name='dispatch')
@require_http_methods(["DELETE"])
def deleteLocalPurchaseDetails(request, lp_dtl_id):
    if request.method == 'DELETE':
        try:
            # Get the lP_dtl instance using lp_dtl_id
            lP_dtl = local_purchasedtl.objects.get(lp_dtl_id=lp_dtl_id)

            # Delete records related to the specified lP_dtl
            # Make sure to use the correct model relationships
            stock_data = stock_lists.objects.filter(lp_dtl_id=lp_dtl_id)
            stock_data.delete()
            lP_dtl.delete()

            return JsonResponse({'success': True, 'msg': f'Successfully deleted'})
        except local_purchasedtl.DoesNotExist:
            return JsonResponse({'success': False, 'errmsg': f'lp_dtl_id {lp_dtl_id} not found.'})
    return JsonResponse({'success': False, 'errmsg': 'Invalid request method.'})


# Report Local Purchase
@login_required()
def localPurchaseReportManagerAPI(request, lp_id=None):
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
    
    # Get all active items
    item_data = items.objects.filter(is_active=True).all()

    lp_Data = local_purchase.objects.get(pk=lp_id) if lp_id else None

    # Query without_GRNdtl records related to the withgrnData
    lpdtl_data = local_purchasedtl.objects.filter(lp_id=lp_Data).all()

    item_with_lpDtls = []

    for item in item_data:
        store_instance = lp_Data.store_id if lp_Data else None
        org_instance = lp_Data.id_org if lp_Data else None
        
        available_qty = get_available_qty(item_id=item, store_id=store_instance, org_id=org_instance)
        
        # Find the associated grn_dtls for this item
        lp_dtls = None
        for dtls in lpdtl_data:
            if dtls.item_id == item:
                lp_dtls = dtls
                break
        if lp_dtls:
            item_with_lpDtls.append({
                'grandQty': available_qty,
                'lp_dtls': lp_dtls,
            })

    context = {
        'org_list': org_list,
        'item_with_lpDtls': item_with_lpDtls,
        'lp_Data': lp_Data,
    }

    return render(request, 'local_purchase/lp_report.html', context)