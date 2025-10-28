import sys
import json
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from datetime import datetime
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.db.models import Q, F, Sum, ExpressionWrapper, fields, FloatField
from django.db import transaction
from django.contrib import messages
from item_setup.models import items
from store_setup.models import store
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from organizations.models import branchslist, organizationlst
from stock_list.stock_qty import get_available_qty
from user_auth.utils.notification_data_context import save_notification_data_json
from user_setup.models import access_list
from supplier_setup.models import suppliers
from . models import without_GRN, without_GRNdtl
from stock_list.models import in_stock, stock_lists
from item_pos.models import invoicedtl_list
from opening_stock.models import opening_stockdtl
from others_setup.models import item_type
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def without_GRN_listAPI(request):
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
        'billingBtn_access': billingBtn_access
    }
    return render(request, 'G_R_N_with_without/without_grn_list.html', context)

@login_required()
def getWGRNListDetailsAPI(request):
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
    wo_grn_data = without_GRN.objects.filter(filter_kwargs)

    # Prepare response data
    data = []
    for wo_grn_list in wo_grn_data:
        org_name = wo_grn_list.id_org.org_name if wo_grn_list.id_org else None
        branch_name = wo_grn_list.branch_id.branch_name if wo_grn_list.branch_id else None
        store_name = wo_grn_list.store_id.store_name if wo_grn_list.store_id else None
        is_approved_by_first = wo_grn_list.is_approved_by.first_name if wo_grn_list.is_approved_by else ""
        is_approved_by_last = wo_grn_list.is_approved_by.last_name if wo_grn_list.is_approved_by else ""
        data.append({
            'wo_grn_id': wo_grn_list.wo_grn_id,
            'wo_grn_no': wo_grn_list.wo_grn_no,
            'transaction_date': wo_grn_list.transaction_date,
            'approved_date': wo_grn_list.approved_date,
            'org_name': org_name,
            'branch_name': branch_name,
            'store_name': store_name,
            'invoice_no': wo_grn_list.invoice_no,
            'invoice_date': wo_grn_list.invoice_date,
            'is_approved': wo_grn_list.is_approved,
            'is_approved_by_first': is_approved_by_first,
            'is_approved_by_last': is_approved_by_last,
        })

    return JsonResponse({'data': data})


# add receive stock without grn
@login_required()
def recStockwithout_GRNAPI(request, id=0):
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

    has_access = access_list.objects.filter(
        user_id=user,
        feature_id__feature_page_link='GRNAPPROVEBTN',
        is_active=True
    ).exists()
    
    billingBtn_access = access_list.objects.filter(
        user_id=user,
        feature_id__feature_page_link='BILLINGFORMACCESSBTN',
        is_active=True
    ).exists()

    context = {
        'org_list': org_list,
        'has_access': has_access,
        'billingBtn_access': billingBtn_access,
    }

    return render(request, 'G_R_N_with_without/add_rec_stock_withoutgrn.html', context)

# get receive stock without grn list
@login_required()
def get_recStckwithout_GRNAPI(request):
    selected_type_id = request.GET.get('selectedTypeId')
    selected_id_org = request.GET.get('id_org')
    selected_supplier_id = request.GET.get('filter_suppliers')
    query = request.GET.get('query', '')  # Fetch the query term

    # Base query with filters applied more efficiently
    filters = {'is_active': True}

    if selected_type_id and selected_type_id != '1':
        filters['type_id'] = selected_type_id

    if selected_id_org:
        filters['org_id'] = selected_id_org

    # Fetch the data using select_related and prefetch_related for optimization
    item_data = items.objects.filter(**filters).select_related(
        'org_id', 'type_id'
    ).prefetch_related('item_supplierdtl__supplier_id')

    if selected_supplier_id and selected_supplier_id != '1':
        item_data = item_data.filter(item_supplierdtl__supplier_id=selected_supplier_id)

    # Filter items based on the query (item_name contains query term)
    if query:
        item_data = item_data.filter(Q(item_name__icontains=query) | Q(item_no__icontains=query))

    # Using values to avoid object instantiation
    item_data = item_data.values('item_id', 'item_no', 'item_name')

    # Paginate the results
    paginator = Paginator(item_data, 200)  # 200 items per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Prepare response
    item_with_grandQty = list(page_obj)  # Convert page_obj to list

    return JsonResponse({'data': item_with_grandQty})


# get receive stock without grn list details
@login_required()
def get_recStockwithout_grn_details(request):
    if request.method == 'GET' and 'selectedItem' in request.GET:
        selected_item_id = request.GET.get('selectedItem')
        store_id = request.GET.get('store_id')
        org_id = request.GET.get('selected_id_org')
        
        try:
            selected_item = items.objects.get(item_id=selected_item_id, org_id=org_id)

            item_details = []
            
            available_qty = get_available_qty(item_id=selected_item, store_id=store_id, org_id=org_id)

            item_details.append({
                'item_id': selected_item.item_id,
                'item_no': selected_item.item_no,
                'type_name': selected_item.type_id.type_name if selected_item.type_id else '',
                'uom_name': selected_item.item_uom_id.item_uom_name if selected_item.item_uom_id else '',
                'grandQty': available_qty,
                'purchase_price': selected_item.purchase_price,
                'sales_price': selected_item.sales_price,
                'item_name': selected_item.item_name,
            })

            return JsonResponse({'data': item_details})
        except items.DoesNotExist:
            return JsonResponse({'error': 'Item not found'}, status=404)
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)


# edit/update receive stock without grn
@login_required()
def edit_recStockwithout_GRNAPI(request, wo_grn_id=None):
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

    wogrn_Data = without_GRN.objects.get(pk=wo_grn_id) if wo_grn_id else None

    # Query without_GRNdtl records related to the withgrnData
    wogrndtl_data = without_GRNdtl.objects.filter(wo_grn_id=wogrn_Data).all()

    item_with_wogrnDtls = []

    for item in item_data:
        store_instance = wogrn_Data.store_id if wogrn_Data else None
        org_instance = wogrn_Data.id_org if wogrn_Data else None
        
        available_qty = get_available_qty(item_id=item, store_id=store_instance, org_id=org_instance)
        
        # Find the associated grn_dtls for this item
        wogrn_dtls = None
        for dtls in wogrndtl_data:
            if dtls.item_id == item:
                wogrn_dtls = dtls
                break
        if wogrn_dtls:
            item_with_wogrnDtls.append({
                'grandQty': available_qty,
                'wogrn_dtls': wogrn_dtls,
            })

    has_access = access_list.objects.filter(
        user_id=user,
        feature_id__feature_page_link='GRNAPPROVEBTN',
        is_active=True
    ).exists()
    
    billingBtn_access = access_list.objects.filter(
        user_id=user,
        feature_id__feature_page_link='BILLINGFORMACCESSBTN',
        is_active=True
    ).exists()

    context = {
        'org_list': org_list,
        'item_with_wogrnDtls': item_with_wogrnDtls,
        'wogrn_Data': wogrn_Data,
        'has_access': has_access,
        'billingBtn_access': billingBtn_access,
    }

    return render(request, 'G_R_N_with_without/edit_rec_stock_withoutgrn.html', context)


@login_required()
def exsit_receiveStockWogrnAPI(request):
    resp = {'status': 'failed', 'msg': ''}
    data = request.POST

    store_id = data.get("store_id")
    item_ids = data.getlist('item_ids[]')
    item_batch_name = data.getlist('item_batch')

    store_instance = store.objects.get(store_id=store_id)

    # Create a list to store error messages for existing items
    existing_items_err_msgs = []

    for item_id, item_batch in zip(item_ids, item_batch_name):
        # Fetch the item associated with the item_id
        item_instance = items.objects.get(item_id=item_id)

        # Check if an item with the same item_id exists in without_GRNdtl
        if without_GRNdtl.objects.filter(Q(item_id=item_instance) & Q(store_id=store_instance) & Q(item_batch__iexact=item_batch)).exists():
            errmsg = f"This Item: '{item_instance.item_name}' is already exists in Batch: '{item_batch}' and Store: '{store_instance.store_name}' Please.. Change the 'Batch' Name ..."
            existing_items_err_msgs.append(errmsg)

    # Check if there are any existing items
    if existing_items_err_msgs:
        # If there are existing items, return an error response
        resp['msg'] = ', '.join(existing_items_err_msgs)
    else:
        resp['status'] = 'success'

    return JsonResponse(resp)


@login_required()
def receiveStockWogrnAPI(request):
    resp = {'status': 'failed', 'errmsg': 'Failed ...'}
    data = request.POST

    id_org = data.get("org")
    branch_id = data.get("branchs")
    store_id =data.get("current_store")
    supplier_id = data.get("supplier")
    is_approved_by_user = data.get('is_approved_by_user_id')
    is_credit = data.get('is_credit', False)
    is_cash = data.get('is_cash', False)
    carrying_lifting_cost = data.get("carrying_lifting_cost")

    item_ids = data.getlist('item_id[]')
    item_qtys = data.getlist('item_qty[]')
    bonus_qtys = data.getlist('bonus_qty[]')
    item_prices = data.getlist('item_price[]')
    dis_percentages = data.getlist('dis_percentage[]')
    item_batchs = data.getlist('item_batchs[]')
    item_exp_dates = data.getlist('item_exp_dates[]')
    is_approved = data['is_approved']
    
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
        if without_GRNdtl.objects.filter(Q(item_id=item_instance) & Q(store_id=store_instance) & Q(item_batch__iexact=item_batch_value)).exists():
            errmsg = f"This Item: '{item_instance.item_name}' is already exists in this Batch No: '{item_batch_value}' and Store: '{store_instance.store_name}' Please.. Change the 'Batch No' ..."
            existing_items_err_msgs.append(errmsg)

    # Check if there are any existing items
    if existing_items_err_msgs:
        # If there are existing items, return an error response
        return JsonResponse({'success': False, 'errmsg': ', '.join(existing_items_err_msgs)})

    try:
        with transaction.atomic():
            try:
                # Check if the user exists
                user_instance = None
                if is_approved_by_user:
                    user_instance = User.objects.get(user_id=is_approved_by_user)
            except User.DoesNotExist:
                return JsonResponse({'errmsg': 'User with the provided ID does not exist.'}, status=400)
            
            if id_org and branch_id:
                try:
                    org_instance = organizationlst.objects.get(org_id=id_org)
                    branch_instance = branchslist.objects.get(branch_id=branch_id)
                    supplier_instance = suppliers.objects.get(supplier_id=supplier_id)
                    
                    if not carrying_lifting_cost:  # catches None, '', or '0'
                        carrying_lifting_cost = 0
                    else:
                        try:
                            carrying_lifting_cost = float(carrying_lifting_cost)
                        except ValueError:
                            carrying_lifting_cost = 0
                            
                    # receive an without_GRN instance
                    receiveGRNstock = without_GRN(
                        id_org=org_instance,
                        branch_id=branch_instance,
                        supplier_id=supplier_instance,
                        is_cash=is_cash,
                        is_credit=is_credit,
                        store_id=store_instance,
                        transaction_date=data['transaction_date'],
                        carrying_lifting_cost=carrying_lifting_cost,
                        invoice_no=invoice_no,
                        invoice_date=invoice_date,
                        is_approved=is_approved,
                        is_approved_by=user_instance,
                        approved_date=data['approved_date'],
                        remarks=data['remarks'],
                        ss_creator=request.user
                    )
                    receiveGRNstock.save()

                    # receive without_GRNdtl instances for each item
                    for item_id, item_price, dis_percentage, qty, bonus_qty, batch, exp_dates in zip(item_ids, item_prices, dis_percentages, item_qtys, bonus_qtys, item_batchs, item_exp_dates):
                        item_instance = items.objects.get(item_id=item_id)

                        # Handle null or empty expiration dates
                        if exp_dates in [None, '']:
                            exp_dates = None  # Set to None for empty values

                        rec_qty = float(qty)
                        rec_dis_perc = float(dis_percentage)
                        
                        if not bonus_qty:  # catches None, '', or '0'
                            rec_bonus_qty = 0
                        else:
                            try:
                                rec_bonus_qty = float(bonus_qty)
                            except ValueError:
                                rec_bonus_qty = 0
                                
                        total_qty = rec_qty + rec_bonus_qty

                        receiveGRNstockDtl = without_GRNdtl(
                            unit_price=item_price,
                            dis_percentage=rec_dis_perc,
                            wo_grn_qty=rec_qty,
                            bonus_qty=rec_bonus_qty,
                            item_batch=batch,
                            item_exp_date=exp_dates,
                            item_id=item_instance,
                            wo_grn_id=receiveGRNstock,
                            store_id=store_instance,
                            supplier_id=supplier_instance,
                            wo_grn_date=receiveGRNstock.transaction_date,
                            is_approved=receiveGRNstock.is_approved,
                            approved_date=receiveGRNstock.approved_date,
                            ss_creator=request.user
                        )
                        receiveGRNstockDtl.save()

                        stock_data = stock_lists(
                            wo_grn_id=receiveGRNstock,
                            wo_grndtl_id=receiveGRNstockDtl,
                            stock_qty=total_qty,
                            item_batch=batch,
                            item_exp_date=exp_dates,
                            item_id=item_instance,
                            store_id=store_instance,
                            recon_type=True, #recon_type=True is adding item in stock list
                            is_approved=receiveGRNstock.is_approved,
                            approved_date=receiveGRNstock.approved_date,
                            ss_creator=request.user
                        )
                        stock_data.save()

                        # Check if item and store combination exists in in_stock
                        approved_status = receiveGRNstock.is_approved
                        
                        if approved_status == '1':
                            in_stock_obj, created = in_stock.objects.get_or_create(
                                item_id=item_instance,
                                store_id=store_instance,
                                defaults={
                                    'stock_qty': total_qty,
                                }
                            )
                            if not created:
                                # If the record exists, update the stock_qty
                                in_stock_obj.stock_qty += float(total_qty)
                                in_stock_obj.save()
                        
                    # Update notification JSON after invoice save
                    save_notification_data_json()


                    resp['status'] = 'success'
                    return JsonResponse({'success': True, 'msg': 'Successful'})

                except organizationlst.DoesNotExist:
                    resp['errmsg'] = 'Organization associated with the user does not exist.'
                except branchslist.DoesNotExist:
                    resp['errmsg'] = 'Branch associated with the user does not exist.'
                except suppliers.DoesNotExist:
                    resp['errmsg'] = 'Suppliers Not Selected... Please Select First!..'
            else:
                resp['errmsg'] = 'User is not associated with an organization or branch.'
    except Exception as e:
        print("Error:", str(e))
        resp['status'] = 'failed'

    return HttpResponse(json.dumps(resp), content_type="application/json")


@login_required()
def edit_receiveStockWogrnAPI(request):
    resp = {'success': False, 'errmsg': 'Fails'}
    data = request.POST

    wo_grn_id = data.get('wo_grn_id')

    if wo_grn_id.isnumeric() and int(wo_grn_id) > 0:
        id_org = data.get("org")
        branch_id = data.get("branchs")
        store_id = data.get("current_store")
        supplier_id = data.get("supplier")
        is_approved_by_user = data.get('is_approved_by_user_id')
        is_credit = data.get('is_credit', False)
        is_cash = data.get('is_cash', False)
        carrying_lifting_cost = data.get("carrying_lifting_cost")
        item_prices = data.getlist('item_price[]')
        dis_percentages = data.getlist('dis_percentage[]')
        item_ids = data.getlist('item_id[]')
        item_qtys = data.getlist('item_qty[]')
        bonus_qtys = data.getlist('bonus_qty[]')
        item_batchs = data.getlist('item_batchs[]')
        item_exp_dates = data.getlist('item_exp_dates[]')
        is_approved = data.get('is_approved', False)
        
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
            supplier_instance = suppliers.objects.get(supplier_id=supplier_id)
            receiveGRNstock = without_GRN.objects.get(wo_grn_id=wo_grn_id)

            for item_id, item_batch_value in zip(item_ids, item_batchs):
                # Fetch the item associated with the item_id
                item_value = items.objects.get(item_id=item_id, org_id=id_org)

                # Check if the same combination of item_id, store_id, and item_batch exists in without_GRNdtl for another wo_grn_id
                existing_items = without_GRNdtl.objects.filter(
                    Q(item_id=item_value) & Q(store_id=store_instance) & Q(item_batch__iexact=item_batch_value)
                ).exclude(wo_grn_id=receiveGRNstock)

                if existing_items.exists():
                    errmsg = f"This Item: '{item_value.item_name}' is already exists in this Batch No: '{item_batch_value}' and Store: '{store_instance.store_name}' Plz Change the Batch No..."
                    return JsonResponse({'success': False, 'errmsg': errmsg})

            # If it's already approved
            if receiveGRNstock.is_approved:
                return JsonResponse({'success': False, 'errmsg': 'Already Approved!'})
            
            if not carrying_lifting_cost:  # catches None, '', or '0'
                carrying_lifting_cost = 0
            else:
                try:
                    carrying_lifting_cost = float(carrying_lifting_cost)
                except ValueError:
                    carrying_lifting_cost = 0

            try:
                with transaction.atomic():
                    # Update the without_GRN instance
                    receiveGRNstock.store_id = store_instance
                    receiveGRNstock.id_org = org_instance
                    receiveGRNstock.branch_id = branch_instance
                    receiveGRNstock.supplier_id = supplier_instance
                    receiveGRNstock.transaction_date = data.get('transaction_date')
                    receiveGRNstock.carrying_lifting_cost=carrying_lifting_cost
                    receiveGRNstock.invoice_no = invoice_no
                    receiveGRNstock.invoice_date = invoice_date
                    receiveGRNstock.is_approved = is_approved
                    receiveGRNstock.is_approved_by = user_instance
                    receiveGRNstock.approved_date = data.get('approved_date')
                    receiveGRNstock.remarks = data.get('remarks') or ''
                    receiveGRNstock.is_credit = is_credit
                    receiveGRNstock.is_cash = is_cash
                    receiveGRNstock.ss_modifier = request.user
                    receiveGRNstock.save()

                    # Update or create without_GRNdtl instances for each item
                    for item_id, item_price, dis_percentage, qty, bonus_qty, batch, exp_dates in zip(item_ids, item_prices, dis_percentages, item_qtys, bonus_qtys, item_batchs, item_exp_dates):
                        item_instance = items.objects.get(item_id=item_id)

                        rec_qty = float(qty)
                        rec_dis_perc = float(dis_percentage)
                        
                        if not bonus_qty:  # catches None, '', or '0'
                            rec_bonus_qty = 0
                        else:
                            try:
                                rec_bonus_qty = float(bonus_qty)
                            except ValueError:
                                rec_bonus_qty = 0
                                
                        total_qty = rec_qty + rec_bonus_qty

                        receiveGRNstockDtl, created = without_GRNdtl.objects.update_or_create(
                            wo_grn_id=receiveGRNstock,
                            item_id=item_instance,
                            defaults={
                                'wo_grn_qty': rec_qty,
                                'bonus_qty': rec_bonus_qty,
                                'item_batch': batch,
                                'item_exp_date': exp_dates or None,  # Handle empty string for item_exp_date
                                'store_id': store_instance,
                                'unit_price': item_price,
                                'dis_percentage': rec_dis_perc,
                                'wo_grn_date': receiveGRNstock.transaction_date,
                                'is_approved': receiveGRNstock.is_approved,
                                'approved_date': receiveGRNstock.approved_date,
                                'ss_modifier': request.user,
                            }
                        )

                        # Save the without_GRNdtl instance
                        receiveGRNstockDtl.save()

                        # Update or create stock_lists
                        stock_data, created = stock_lists.objects.update_or_create(
                            wo_grn_id=receiveGRNstock,
                            wo_grndtl_id=receiveGRNstockDtl,
                            item_id=item_instance,
                            defaults={
                                'stock_qty': total_qty,
                                'item_batch': batch,
                                'item_exp_date': exp_dates or None,  # Handle empty string for item_exp_date
                                'store_id': store_instance,
                                'recon_type' : True, #recon_type=True is adding item in stock list
                                'is_approved': receiveGRNstock.is_approved,
                                'approved_date': receiveGRNstock.approved_date,
                                'ss_modifier': request.user
                            }
                        )

                        # Save the stock_lists instance
                        stock_data.save()

                        # Check if item and store combination exists in in_stock
                        approved_status = receiveGRNstock.is_approved
                        
                        # Check if item and store combination exists in in_stock
                        if approved_status == '1':
                            in_stock_obj, created = in_stock.objects.get_or_create(
                                item_id=item_instance,
                                store_id=store_instance,
                                defaults={
                                    'stock_qty': total_qty,
                                }
                            )
                            if not created:
                                # If the record exists, update the stock_qty
                                in_stock_obj.stock_qty += float(total_qty)
                                in_stock_obj.save()
                    # Update notification JSON after invoice save
                    save_notification_data_json()


                    resp['success'] = True
                    return JsonResponse({'success': True, 'msg': 'Successful'})
            except User.DoesNotExist:
                return JsonResponse({'errmsg': 'Transjection not submit.'}, status=400)
        except Exception as e:
            print("Error:", str(e))
            resp['errmsg'] = str(e)

    return HttpResponse(json.dumps(resp), content_type="application/json")


# Report without grn
@login_required()
def reportWithoutGRNAPI(request, wo_grn_id=None):
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

    wogrn_Data = without_GRN.objects.get(pk=wo_grn_id) if wo_grn_id else None

    # Query without_GRNdtl records related to the withgrnData
    wogrndtl_data = without_GRNdtl.objects.filter(wo_grn_id=wogrn_Data).all()

    item_with_wogrnDtls = []

    for item in item_data:
        store_instance = wogrn_Data.store_id if wogrn_Data else None
        org_instance = wogrn_Data.id_org if wogrn_Data else None
        
        available_qty = get_available_qty(item_id=item, store_id=store_instance, org_id=org_instance)
        
        # Find the associated grn_dtls for this item
        wogrn_dtls = None
        for dtls in wogrndtl_data:
            if dtls.item_id == item:
                wogrn_dtls = dtls
                break
        if wogrn_dtls:
            item_with_wogrnDtls.append({
                'grandQty': available_qty,
                'wogrn_dtls': wogrn_dtls,
            })

    context = {
        'org_list': org_list,
        'item_with_wogrnDtls': item_with_wogrnDtls,
        'wogrn_Data': wogrn_Data,
    }

    return render(request, 'G_R_N_with_without/report_without_grn.html', context)


@method_decorator(csrf_exempt, name='dispatch')
@require_http_methods(["DELETE"])
def delete_wo_grn(request, wo_grndtl_id):
    if request.method == 'DELETE':
        try:
            # Get the wo_grndtl instance using wo_grndtl_id
            wo_grndtl = without_GRNdtl.objects.get(wo_grndtl_id=wo_grndtl_id)

            # Delete records related to the specified wo_grndtl
            # Make sure to use the correct model relationships
            stock_data = stock_lists.objects.filter(wo_grndtl_id=wo_grndtl)
            stock_data.delete()
            wo_grndtl.delete()

            return JsonResponse({'success': True, 'msg': f'Successfully deleted'})
        except without_GRNdtl.DoesNotExist:
            return JsonResponse({'success': False, 'errmsg': f'wo_grndtl_id {wo_grndtl_id} not found.'})
    return JsonResponse({'success': False, 'errmsg': 'Invalid request method.'})


# ==================================================================
@login_required()
def grnAppDetailsReportsAPI(request):
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
    return render(request, 'G_R_N_with_without/grn_details_approve_report/grn_app_details_report.html', context)


@login_required()
def grnAppSummaryReportsAPI(request):
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
    return render(request, 'G_R_N_with_without/grn_details_approve_report/grn_app_summary_report.html', context)


# get GRN Details transaction Details
@login_required()
def getGRNAppDetailsReportsDataAPI(request):
    try:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            org_id = request.GET.get('org_id')
            op_starts = request.GET.get('op_start')
            op_ends = request.GET.get('op_end')

            start_date, end_date = None, None

            # Parse and validate date inputs
            if op_starts and op_ends:
                try:
                    start_date = datetime.strptime(op_starts, '%Y-%m-%d').date()
                    end_date = datetime.strptime(op_ends, '%Y-%m-%d').date()
                except ValueError:
                    return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)
                
            if not org_id:
                return JsonResponse({'error': 'Missing org_id'}, status=400)

            grn_purchases = without_GRN.objects.filter(id_org=org_id, is_approved=True, transaction_date__range=(start_date, end_date))
            if not grn_purchases.exists():
                return JsonResponse({'message': 'No Without GRN found for this organization.'}, status=200)

            data = []
            for grn_data in grn_purchases:
                pur_details = []
                grand_grn_total = 0
                branch_name = grn_data.branch_id.branch_name

                grn_details = without_GRNdtl.objects.filter(wo_grn_id=grn_data)

                for grndetail in grn_details:
                    total_amount = grndetail.unit_price * grndetail.wo_grn_qty
                    # dis_percent = grndetail.dis_percentage or 0
                    # total_dis_amt = total_amount * (dis_percent / 100)
                    # row_total_amount = total_amount - total_dis_amt
                    # grand_grn_total += row_total_amount
                    grand_grn_total += total_amount

                    pur_details.append({
                        'item_id': grndetail.item_id.item_id,
                        'item_name': grndetail.item_id.item_name,
                        'uom': grndetail.item_id.item_uom_id.item_uom_name,
                        'sales_rate': grndetail.unit_price,
                        'qty': grndetail.wo_grn_qty,
                        # 'dis_perc': dis_percent,
                    })

                # if grn_data.is_credit and grand_grn_total > 0:
                data.append({
                    'trans_id': grn_data.wo_grn_id,
                    'trans_no': grn_data.wo_grn_no,
                    'clients_name': grn_data.supplier_id.supplier_name if grn_data.supplier_id else '',
                    'invoice_date': grn_data.invoice_date if grn_data.invoice_date else '',
                    'trans_date': grn_data.transaction_date,
                    'branch': branch_name,
                    'trns_amt': grand_grn_total,
                    'details_data': pur_details,
                })

            data = sorted(data, key=lambda x: x['trans_date'], reverse=True)
            return JsonResponse(data, safe=False)

        return JsonResponse({'error': 'Invalid request'}, status=400)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    

# get GRN Summary transaction Details
@login_required()
def getGRNAppSummaryReportsDataAPI(request):
    try:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            org_id = request.GET.get('org_id')
            op_starts = request.GET.get('op_start')
            op_ends = request.GET.get('op_end')

            if not org_id:
                return JsonResponse({'error': 'Missing org_id'}, status=400)

            start_date, end_date = None, None
            if op_starts and op_ends:
                try:
                    start_date = datetime.strptime(op_starts, '%Y-%m-%d').date()
                    end_date = datetime.strptime(op_ends, '%Y-%m-%d').date()
                except ValueError:
                    return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

            grn_purchases = without_GRN.objects.filter(
                id_org=org_id, is_approved=True, transaction_date__range=(start_date, end_date)
            )

            if not grn_purchases.exists():
                return JsonResponse({'message': 'No Without GRN found for this organization.'}, status=200)

            data = {}
            
            for grn_data in grn_purchases:
                transaction_date = grn_data.transaction_date.strftime('%Y-%m-%d')  # Convert date to string for JSON

                grn_details = without_GRNdtl.objects.filter(wo_grn_id=grn_data)
                item_summary = grn_details.values('item_id').annotate(total_qty=Sum('wo_grn_qty'))

                if transaction_date not in data:
                    data[transaction_date] = {}

                for item in item_summary:
                    item_id = item['item_id']
                    if item_id not in data[transaction_date]:
                        item_obj = items.objects.get(pk=item_id)
                        data[transaction_date][item_id] = {
                            'item_id': item_id,
                            'item_name': item_obj.item_name,
                            'uom': item_obj.item_uom_id.item_uom_name if item_obj.item_uom_id else '',
                            'total_qty': 0  # Initialize total_qty
                        }
                    
                    data[transaction_date][item_id]['total_qty'] += item['total_qty']

            # Convert data to required JSON format
            response_data = []
            for trans_date, items_dict in sorted(data.items(), reverse=True):
                response_data.append({
                    'trans_date': trans_date,
                    'details_data': list(items_dict.values())
                })

            return JsonResponse(response_data, safe=False)

        return JsonResponse({'error': 'Invalid request'}, status=400)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
