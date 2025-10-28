import sys
import json
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from datetime import datetime
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.db.models import Q, F, Sum, ExpressionWrapper, fields, FloatField, Prefetch
from django.db import transaction
from django.contrib import messages
from item_setup.models import items
from store_setup.models import store
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from organizations.models import branchslist, organizationlst
from stock_list.stock_qty import get_available_qty
from store_transfers.models import stock_transfer_list, stock_transfer_listdtl
from user_auth.utils.notification_data_context import save_notification_data_json
from user_setup.models import access_list
from supplier_setup.models import suppliers
from stock_list.models import in_stock, stock_lists
from item_pos.models import invoicedtl_list
from opening_stock.models import opening_stockdtl
from others_setup.models import item_type
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def storeTransferListManagerAPI(request):
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
    return render(request, 'store_transfers/store_transfer_list.html', context)


@login_required()
def addNewStoreTransferManagerAPI(request):
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
        feature_id__feature_page_link='STORETRANSAPPBTN',
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

    return render(request, 'store_transfers/add_store_transfer.html', context)


@login_required()
def editStoreTransferFormManagerAPI(request):
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
        feature_id__feature_page_link='STORETRANSAPPBTN',
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

    return render(request, 'store_transfers/edit_store_transfer.html', context)


@login_required()
def getStockTransferItemListAPI(request):
    selected_store_id = request.GET.get('store_id')
    selected_type_id = request.GET.get('selectedTypeId')
    selected_supplier_id = request.GET.get('filter_suppliers')
    filter_org = request.GET.get('id_org')
    search_query = request.GET.get('query', '')  # Get the search query
    page_number = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 100))  # Default page size is 100

    try:

        filters = {'is_active': True, 'org_id': filter_org}
        
        
        # Filter by item type
        if selected_type_id and selected_type_id != '1':
            filters['type_id'] = selected_type_id
            
            
        # Add supplier filter
        if selected_supplier_id and selected_supplier_id != '1':
            filters['item_supplierdtl__supplier_id'] = selected_supplier_id
            
        if selected_store_id == '':
            return JsonResponse({'error': 'From Store Selected First !...'}, status=404)


        # Fetch stock information related to the selected store
        stock_qs = in_stock.objects.filter(store_id=selected_store_id).select_related('store_id').only(
            'store_id', 'store_id__store_name', 'stock_qty'
        )

        # Build the base query for filtering items
        search_filters = Q(item_name__icontains=search_query) | Q(item_no__icontains=search_query)

        item_data_query = items.objects.filter(
            search_filters,
            **filters
        ).select_related('type_id', 'item_uom_id').only(
            'item_id', 'item_no', 'item_name', 'sales_price', 'type_id__type_name', 'item_uom_id__item_uom_name'
        ).prefetch_related(
            Prefetch('item_id2in_stock', queryset=stock_qs, to_attr='prefetched_stock')
        )

        # Paginate the query
        paginator = Paginator(item_data_query, page_size)
        page_obj = paginator.get_page(page_number)

        # Build the serialized response
        serialized_data = []
        for item in page_obj:
            available_qty = get_available_qty(item.item_id, selected_store_id, filter_org)
            stock_details = item.prefetched_stock[0] if item.prefetched_stock else None

            serialized_item = {
                'item_id': item.item_id,
                'item_no': item.item_no,
                'item_name': item.item_name,
                'item_type_name': item.type_id.type_name if item.type_id else "Unknown",
                'item_uom': item.item_uom_id.item_uom_name if item.item_uom_id else "Unknown",
                'item_Supplier': item.supplier_id.supplier_name if item.supplier_id else "Unknown",
                'store_name': stock_details.store_id.store_name if stock_details else "Unknown",
                'item_price': item.sales_price,
                'stock_qty': available_qty,
            }

            serialized_data.append(serialized_item)

        # Sort by stock quantity in descending order
        sorted_serialized_data = sorted(serialized_data, key=lambda x: x['stock_qty'], reverse=True)

        response_data = {
            'data': sorted_serialized_data,
            'total_pages': paginator.num_pages,
            'current_page': page_obj.number,
            'total_items': paginator.count,
        }

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
    
@login_required()
def saveStoreTransferManagerAPI(request):
    resp = {'status': 'failed', 'errmsg': 'Failed ...'}
    data = request.POST

    id_org = data.get("org")
    branch_id = data.get("branchs")
    from_store =data.get("from_store")
    to_store = data.get("to_store")

    item_ids = data.getlist('item_id[]')
    item_qtys = data.getlist('transfer_qty[]')
    item_batchs = data.getlist('item_batchs[]')
    item_exp_dates = data.getlist('item_exp_dates[]')
    is_approved = data['is_approved']
    is_approved_by_user = data.get('is_approved_by_user_id')

    from_store_instance = store.objects.get(store_id=from_store)
    to_store_instance = store.objects.get(store_id=to_store)
    
    # Create a list to store error messages for existing items
    existing_items_err_msgs = []

    for item_id, item_batch_value in zip(item_ids, item_batchs):
        # Fetch the item associated with the item_id
        item_instance = items.objects.get(item_id=item_id, org_id=id_org)

        # Check if an item with the same item_id exists in opening_stockdtl
        if stock_transfer_listdtl.objects.filter(Q(item_id=item_instance) & Q(to_store=to_store_instance) & Q(item_batch__iexact=item_batch_value)).exists():
            errmsg = f"This Item: '{item_instance.item_name}' is already exists in this Batch No: '{item_batch_value}' and Store: '{to_store_instance.store_name}' Please.. Change the 'Batch No' ..."
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
                    # receive an stock_transfer_list instance
                    stockTrnsList = stock_transfer_list(
                        id_org=org_instance,
                        branch_id=branch_instance,
                        from_store=from_store_instance,
                        to_store=to_store_instance,
                        transaction_date=data['transaction_date'],
                        is_approved=is_approved,
                        is_approved_by=user_instance,
                        approved_date=data['approved_date'],
                        remarks=data['remarks'],
                        ss_creator=request.user
                    )
                    stockTrnsList.save()

                    # receive stock_transfer_listdtl instances for each item
                    for item_id, qty, batch, exp_dates in zip(item_ids, item_qtys, item_batchs, item_exp_dates):
                        item_instance = items.objects.get(item_id=item_id)

                        # Handle null or empty expiration dates
                        if exp_dates in [None, '']:
                            exp_dates = None  # Set to None for empty values

                        rec_qty = float(qty)

                        stockTrnsListDtl = stock_transfer_listdtl(
                            transfer_qty=rec_qty,
                            item_batch=batch,
                            item_exp_date=exp_dates,
                            item_id=item_instance,
                            stock_trans_id=stockTrnsList,
                            from_store=from_store_instance,
                            to_store=to_store_instance,
                            transaction_date=stockTrnsList.transaction_date,
                            is_approved=stockTrnsList.is_approved,
                            approved_date=stockTrnsList.approved_date,
                            ss_creator=request.user
                        )
                        stockTrnsListDtl.save()

                        to_stock_data = stock_lists(
                            stock_trans_id=stockTrnsList,
                            stock_transdtl_id=stockTrnsListDtl,
                            stock_qty=qty,
                            item_batch=batch,
                            item_exp_date=exp_dates,
                            item_id=item_instance,
                            store_id=to_store_instance,
                            recon_type=True, #recon_type=True is adding item in stock list
                            is_approved=stockTrnsList.is_approved,
                            approved_date=stockTrnsList.approved_date,
                            ss_creator=request.user
                        )
                        to_stock_data.save()
                        
                        from_stock_data = stock_lists(
                            stock_trans_id=stockTrnsList,
                            stock_transdtl_id=stockTrnsListDtl,
                            stock_qty=qty,
                            item_batch=batch,
                            item_exp_date=exp_dates,
                            item_id=item_instance,
                            store_id=to_store_instance,
                            recon_type=False, #recon_type=False is substrac item in stock list
                            is_approved=stockTrnsList.is_approved,
                            approved_date=stockTrnsList.approved_date,
                            ss_creator=request.user
                        )
                        from_stock_data.save()
                        
                        # Check if item and store combination exists in in_stock
                        approved_status = stockTrnsList.is_approved
                        
                        # Check if item and store combination exists in in_stock
                        if approved_status == '1':
                            to_stock, _ = in_stock.objects.get_or_create(
                                item_id=item_instance, 
                                store_id=to_store_instance,
                                defaults={'stock_qty': 0}
                            )
                            from_stock, _ = in_stock.objects.get_or_create(
                                item_id=item_instance, 
                                store_id=from_store_instance,
                                defaults={'stock_qty': 0}
                            )
                            to_stock.stock_qty += rec_qty
                            from_stock.stock_qty -= rec_qty
                            to_stock.save()
                            from_stock.save()
                        
                    # Update notification JSON after invoice save
                    save_notification_data_json()


                    resp['status'] = 'success'
                    return JsonResponse({'success': True, 'msg': 'Successful'})

                except organizationlst.DoesNotExist:
                    resp['errmsg'] = 'Organization associated with the user does not exist.'
                except branchslist.DoesNotExist:
                    resp['errmsg'] = 'Branch associated with the user does not exist.'
            else:
                resp['errmsg'] = 'User is not associated with an organization or branch.'
    except Exception as e:
        error_msg = str(e)
        print("Error:", error_msg)  # Still prints on console
        resp['status'] = 'failed'
        resp['errmsg'] = error_msg  # Include actual error message in the response
        return JsonResponse(resp)



@login_required()
def getStoreTransferListManagerAPI(request):
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
    trans_data = stock_transfer_list.objects.filter(filter_kwargs)

    # Prepare response data
    data = []
    for trns_list in trans_data:
        org_name = trns_list.id_org.org_name if trns_list.id_org else None
        branch_name = trns_list.branch_id.branch_name if trns_list.branch_id else None
        from_store = trns_list.from_store.store_name if trns_list.from_store else None
        to_store = trns_list.to_store.store_name if trns_list.to_store else None
        is_approved_by_first = trns_list.is_approved_by.first_name if trns_list.is_approved_by else ""
        is_approved_by_last = trns_list.is_approved_by.last_name if trns_list.is_approved_by else ""
        data.append({
            'stock_trans_id': trns_list.stock_trans_id,
            'stock_trans_no': trns_list.stock_trans_no,
            'transaction_date': trns_list.transaction_date,
            'approved_date': trns_list.approved_date,
            'org_name': org_name,
            'branch_name': branch_name,
            'from_store': from_store,
            'to_store': to_store,
            'is_approved': trns_list.is_approved,
            'is_approved_by_first': is_approved_by_first,
            'is_approved_by_last': is_approved_by_last,
        })

    return JsonResponse({'data': data})


@login_required()
def getStockTransferDataEditFromManagerAPI(request):
    stock_trans_id = request.GET.get('stock_trans_id')

    try:
        # Fetch master record
        master = stock_transfer_list.objects.select_related(
            'id_org', 'branch_id', 'from_store', 'to_store', 'is_approved_by'
        ).get(pk=stock_trans_id)

        master_data = {
            "stock_trans_id": master.stock_trans_id,
            "stock_trans_no": master.stock_trans_no,
            "transaction_date": master.transaction_date.strftime("%Y-%m-%d") if master.transaction_date else "",
            "org_id": master.id_org.org_id if master.id_org else None,
            "org_name": master.id_org.org_name if master.id_org else None,
            "branch_id": master.branch_id.branch_id if master.branch_id else None,
            "branch_name": master.branch_id.branch_name if master.branch_id else None,
            # branch details
            "branch_email": master.branch_id.email if master.branch_id else '',
            "branch_fax": master.branch_id.fax if master.branch_id else '',
            "branch_website": master.branch_id.website if master.branch_id else '',
            "branch_hotline": master.branch_id.hotline if master.branch_id else '',
            "branch_phone": master.branch_id.phone if master.branch_id else '',
            "branch_address": master.branch_id.address if master.branch_id else '',
            # 
            "from_store_id": master.from_store.store_id if master.from_store else None,
            "from_store_name": master.from_store.store_name if master.from_store else None,
            "to_store_id": master.to_store.store_id if master.to_store else None,
            "to_store_name": master.to_store.store_name if master.to_store else None,
            "is_approved": master.is_approved,
            "approved_date": master.approved_date,
            "remarks": master.remarks,
            # organization logo
            "org_logo": master.id_org.org_logo.url if (master.id_org and master.id_org.org_logo) else None,
        }

        # Fetch detail records
        details = stock_transfer_listdtl.objects.filter(stock_trans_id=master).select_related('item_id')

        detail_data = []
        for d in details:
            available_qty = get_available_qty(d.item_id, master.from_store.store_id, master.id_org.org_id)
            detail_data.append({
                "stock_transdtl_id": d.stock_transdtl_id,
                "item_id": d.item_id.item_id if d.item_id else None,
                "item_no": d.item_id.item_no if d.item_id else None,
                "item_name": d.item_id.item_name if d.item_id else "",
                "type_name": d.item_id.type_id.type_name if d.item_id.type_id else "",
                "uom_name": d.item_id.item_uom_id.item_uom_name if d.item_id.item_uom_id else "",
                "stock_qty": available_qty,
                "transfer_qty": d.transfer_qty,
                "item_batch": d.item_batch,
                "item_exp_date": d.item_exp_date.strftime("%Y-%m-%d") if d.item_exp_date else "",
                "from_store_id": d.from_store.store_id if d.from_store else None,
                "to_store_id": d.to_store.store_id if d.to_store else None
            })

        return JsonResponse({
            "success": True,
            "master": master_data,
            "details": detail_data
        })

    except stock_transfer_list.DoesNotExist:
        return JsonResponse({"success": False, "error": "Stock transfer not found."}, status=404)
    

@csrf_exempt
@require_http_methods(["DELETE"])
def deletetransfer_listdtlManagerAPI(request, stock_transdtl_id):
    try:
        transfer_listdtl = stock_transfer_listdtl.objects.get(stock_transdtl_id=stock_transdtl_id)

        # Delete related stock_list entries
        stock_lists.objects.filter(stock_transdtl_id=transfer_listdtl).delete()

        # Delete the transfer detail
        transfer_listdtl.delete()

        return JsonResponse({'success': True, 'msg': 'Successfully deleted'})
    except stock_transfer_listdtl.DoesNotExist:
        return JsonResponse({'success': False, 'errmsg': f'stock_transdtl_id {stock_transdtl_id} not found.'})
    except Exception as e:
        return JsonResponse({'success': False, 'errmsg': str(e)})
    
    
    
@login_required()
def editUpdateStockTransferDataManagerAPI(request):
    resp = {'success': False, 'errmsg': 'Fails'}
    data = request.POST

    stock_trans_id = data.get('stock_trans_id')

    if stock_trans_id.isnumeric() and int(stock_trans_id) > 0:
        id_org = data.get("org")
        branch_id = data.get("branchs")
        from_store =data.get("from_store")
        to_store = data.get("to_store")
        item_ids = data.getlist('item_id[]')
        item_qtys = data.getlist('transfer_qty[]')
        item_batchs = data.getlist('item_batchs[]')
        item_exp_dates = data.getlist('item_exp_dates[]')
        is_approved = data['is_approved']
        is_approved_by_user = data.get('is_approved_by_user_id')
        
        try:
            # Check if the user exists
            user_instance = None
            if is_approved_by_user:
                user_instance = User.objects.get(user_id=is_approved_by_user)
        except User.DoesNotExist:
            return JsonResponse({'errmsg': 'User with the provided ID does not exist.'}, status=400)

        try:
            from_store_instance = store.objects.get(store_id=from_store)
            to_store_instance = store.objects.get(store_id=to_store)
            branch_instance = branchslist.objects.get(branch_id=branch_id)
            Trans_Instance = stock_transfer_list.objects.get(stock_trans_id=stock_trans_id)

            for item_id, item_batch_value in zip(item_ids, item_batchs):
                # Fetch the item associated with the item_id
                item_value = items.objects.get(item_id=item_id, org_id=id_org)

                # Check if the same combination of item_id, to_store, and item_batch exists in stock_transfer_listdtl for another stock_trans_id
                existing_items = stock_transfer_listdtl.objects.filter(
                    Q(item_id=item_value) & Q(to_store=to_store_instance) & Q(item_batch__iexact=item_batch_value)
                ).exclude(stock_trans_id=Trans_Instance)

                if existing_items.exists():
                    errmsg = f"This Item: '{item_value.item_name}' is already exists in this Batch No: '{item_batch_value}' and Store: '{to_store_instance.store_name}' Plz Change the Batch No..."
                    return JsonResponse({'success': False, 'errmsg': errmsg})

            # If it's already approved
            if Trans_Instance.is_approved:
                return JsonResponse({'success': False, 'errmsg': 'Already Approved!'})

            try:
                with transaction.atomic():
                    # Update the without_GRN instance
                    Trans_Instance.from_store = from_store_instance
                    Trans_Instance.to_store = to_store_instance
                    Trans_Instance.branch_id = branch_instance
                    Trans_Instance.is_approved = is_approved
                    Trans_Instance.is_approved_by = user_instance
                    Trans_Instance.approved_date = data.get('approved_date')
                    Trans_Instance.remarks = data.get('remarks') or ''
                    Trans_Instance.ss_modifier = request.user
                    Trans_Instance.save()
                    
                    # Step 1: Delete old stock_lists entries for this transaction
                    stock_lists.objects.filter(stock_trans_id=Trans_Instance).delete()

                    # Update or create stock_transfer_listdtl instances for each item
                    for item_id, qty, batch, exp_dates in zip(item_ids, item_qtys, item_batchs, item_exp_dates):
                        item_instance = items.objects.get(item_id=item_id)
                        
                        def parse_date_safe(date_str):
                            try:
                                return datetime.strptime(date_str, '%Y-%m-%d').date()
                            except (ValueError, TypeError):
                                return None
                            
                        rec_qty = float(qty)

                        Trans_InstanceDtl, created = stock_transfer_listdtl.objects.update_or_create(
                            stock_trans_id=Trans_Instance,
                            item_id=item_instance,
                            defaults={
                                'transfer_qty': rec_qty,
                                'item_batch': batch,
                                'item_exp_date': parse_date_safe(exp_dates),
                                'from_store': from_store_instance,
                                'to_store': to_store_instance,
                                'is_approved': Trans_Instance.is_approved,
                                'approved_date': Trans_Instance.approved_date,
                                'ss_modifier': request.user,
                            }
                        )
                        # Save the stock_transfer_listdtl instance
                        Trans_InstanceDtl.save()

                        to_stock_data = stock_lists(
                            stock_trans_id=Trans_Instance,
                            stock_transdtl_id=Trans_InstanceDtl,
                            stock_qty=qty,
                            item_batch=batch,
                            item_exp_date=parse_date_safe(exp_dates),
                            item_id=item_instance,
                            store_id=to_store_instance,
                            recon_type=True, #recon_type=True is adding item in stock list
                            is_approved=Trans_Instance.is_approved,
                            approved_date=Trans_Instance.approved_date,
                            ss_creator=request.user,
                            ss_modifier=request.user
                        )
                
                        from_stock_data = stock_lists(
                            stock_trans_id=Trans_Instance,
                            stock_transdtl_id=Trans_InstanceDtl,
                            stock_qty=qty,
                            item_batch=batch,
                            item_exp_date=parse_date_safe(exp_dates),
                            item_id=item_instance,
                            store_id=to_store_instance,
                            recon_type=False, #recon_type=False is substrac item in stock list
                            is_approved=Trans_Instance.is_approved,
                            approved_date=Trans_Instance.approved_date,
                            ss_creator=request.user,
                            ss_modifier=request.user
                        )
                        
                        to_stock_data.save()
                        from_stock_data.save()
                        
                        # Check if item and store combination exists in in_stock
                        approved_status = Trans_Instance.is_approved
                        
                        # Check if item and store combination exists in in_stock
                        if approved_status == '1':
                            to_stock, _ = in_stock.objects.get_or_create(
                                item_id=item_instance, 
                                store_id=to_store_instance,
                                defaults={'stock_qty': 0}
                            )
                            from_stock, _ = in_stock.objects.get_or_create(
                                item_id=item_instance, 
                                store_id=from_store_instance,
                                defaults={'stock_qty': 0}
                            )
                            to_stock.stock_qty += rec_qty
                            from_stock.stock_qty -= rec_qty
                            to_stock.save()
                            from_stock.save()
                            
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


@login_required()
def storeTransferReportsManagerAPI(request):
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

    return render(request, 'store_transfers/report_store_transfer.html', context)