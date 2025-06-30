import sys
import json
from num2words import num2words
from datetime import date, datetime
from django.db.models import Q, F, Sum, Prefetch, ExpressionWrapper, fields, FloatField
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from stock_list.models import in_stock, stock_lists
from item_setup.models import item_supplierdtl, items
from store_setup.models import store
from organizations.models import branchslist, organizationlst
from b2b_clients_management.models import b2b_client_item_rates
from stock_list.stock_qty import get_available_qty, get_totalSum_available_qty
from drivers_setup.models import drivers_list
from bank_statement.models import cash_on_hands
from registrations.models import in_registrations
from select_bill_receipt.models import in_bill_receipts
from bill_templates.models import in_apps_templates
from others_setup.models import item_type, item_uom
from deliver_chalan.models import delivery_Chalan_list, delivery_Chalandtl_list
from user_setup.models import access_list, lookup_values
from supplier_setup.models import suppliers
from . models import carrying_cost_payments, invoice_list, invoicedtl_list, item_fav_list, payment_list, rent_others_exps, reward_points, reward_pointsdtls
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def item_posAPI(request):
    user = request.user

    # Fetch the corresponding template based on org_id
    apps_temps = in_apps_templates.objects.filter(org_id=user.org_id).first()

    # Determine the template to use
    if apps_temps and apps_temps.billing_temp:
        billing_templates = f'item_pos/pos_billing/{apps_temps.billing_temp}.html'
    else:
        billing_templates = 'item_pos/pos_billing/defaults_pos.html'

    if user.is_superuser:
        # If the user is a superuser, retrieve all organizations
        org_list = organizationlst.objects.filter(is_active=True).all()
    elif user.org_id is not None:
        # If the user has an associated organization, retrieve only that organization
        org_list = organizationlst.objects.filter(is_active=True, org_id=user.org_id).all()
    else:
        # If neither a superuser nor associated with an organization, set organizations to an empty list or handle as needed
        org_list = []

    # **************last invoice print*****************
    # last id query
    # Filter sales by today’s date and authenticated user
    today = date.today()
    sales = invoice_list.objects.filter(
        is_cancel=False, ss_creator=user, invoice_date=today).order_by('-inv_id')[:1][::-1]
    sale_data = []
    for sale in sales:
        data = {}
        for field in sale._meta.get_fields(include_parents=False):
            if field.related_model is None:
                data[field.name] = getattr(sale, field.name)

        sale_data.append(data)

    # ************** Access Buttons Query ***************
    # Query access_list using the __in lookup
    del_chal_access = access_list.objects.filter(
        user_id=user,
        feature_id__feature_page_link='DELCHALANBTNACCSS',
        is_active=True
    ).exists()

    cus_reg_access = access_list.objects.filter(
        user_id=user,
        feature_id__feature_page_link='CUSREGBTNACCSS',
        is_active=True
    ).exists()

    manu_ret_rec_access = access_list.objects.filter(
        user_id=user,
        feature_id__feature_page_link='MANUITMRRBTNACCSS',
        is_active=True
    ).exists()

    lp_rec_access = access_list.objects.filter(
        user_id=user,
        feature_id__feature_page_link='LPRECBTNACCSS',
        is_active=True
    ).exists()

    lp_ret_access = access_list.objects.filter(
        user_id=user,
        feature_id__feature_page_link='LPRETBTNACCSS',
        is_active=True
    ).exists()

    grn_access = access_list.objects.filter(
        user_id=user,
        feature_id__feature_page_link='GRNRBTNACCSS',
        is_active=True
    ).exists()

    pou_access = access_list.objects.filter(
        user_id=user,
        feature_id__feature_page_link='INVUPBTNACCSS',
        is_active=True
    ).exists()

    can_due_access = access_list.objects.filter(
        user_id=user,
        feature_id__feature_page_link='CANDUECOLLREFBTNACCSS',
        is_active=True
    ).exists()

    sales_rep_access = access_list.objects.filter(
        user_id=user,
        feature_id__feature_page_link='SALESRBTNACCSS',
        is_active=True
    ).exists()

    coll_rep_access = access_list.objects.filter(
        user_id=user,
        feature_id__feature_page_link='COLLREPORTBTNACCSS',
        is_active=True
    ).exists()

    due_rep_access = access_list.objects.filter(
        user_id=user,
        feature_id__feature_page_link='DUEREPORTBTNACCSS',
        is_active=True
    ).exists()

    inv_list_access = access_list.objects.filter(
        user_id=user,
        feature_id__feature_page_link='INVLBTNACCSS',
        is_active=True
    ).exists()

    context_pos = {
        'org_list': org_list,
        'sale_data': sale_data,
        'del_chal_access': del_chal_access,
        'cus_reg_access': cus_reg_access,
        'manu_ret_rec_access': manu_ret_rec_access,
        'lp_rec_access': lp_rec_access,
        'lp_ret_access': lp_ret_access,
        'grn_access': grn_access,
        'pou_access': pou_access,
        'can_due_access': can_due_access,
        'sales_rep_access': sales_rep_access,
        'coll_rep_access': coll_rep_access,
        'due_rep_access': due_rep_access,
        'inv_list_access': inv_list_access,
    }
    return render(request, billing_templates, context_pos)

# =======================================================================================
@login_required()
def getItemListWithSumTotalStockAPI(request):
    selected_store_id = request.GET.get('store_id')
    selected_supplier_id = request.GET.get('filter_suppliers')
    filter_org = request.GET.get('org_id')
    b2b_client_supp = request.GET.get('b2b_client_supp_id')
    search_query = request.GET.get('query', '')  # Get the search query
    page_number = int(request.GET.get('page', 1))
    # Default page size is 100
    page_size = int(request.GET.get('page_size', 100))

    try:
        # Base query for filtering items based on active status and organization
        filters = {'is_active': True, 'org_id': filter_org}

        # Add supplier filter
        if selected_supplier_id and selected_supplier_id != '1':
            filters['item_supplierdtl__supplier_id'] = selected_supplier_id

        # Apply search filters (similar to get_Opening_Stock_listAPI)
        search_filters = Q(item_id__icontains=search_query) | Q(
            item_name__icontains=search_query) | Q(item_no__icontains=search_query)

        # Fetch data with necessary relations and filtering
        item_data_query = items.objects.filter(
            search_filters,
            **filters
        ).select_related('type_id', 'item_uom_id').only(
            'item_id', 'item_no', 'item_name', 'sales_price', 'type_id__type_name', 'item_uom_id__item_uom_name'
        ).prefetch_related(
            Prefetch('item_supplierdtl_set', queryset=item_supplierdtl.objects.select_related(
                'supplier_id').only('supplier_id', 'supplier_id__supplier_name'), to_attr='prefetched_supplierdtl'),
            Prefetch('item_id2in_stock', queryset=in_stock.objects.filter(store_id=selected_store_id).select_related(
                'store_id').only('store_id', 'store_id__store_name', 'stock_qty'), to_attr='prefetched_stock')
        )

        # Pagination similar to get_Opening_Stock_listAPI
        paginator = Paginator(item_data_query, page_size)
        page_obj = paginator.get_page(page_number)
        item_data = list(page_obj)

        # Fetch b2b_client_item_rates if required
        b2b_client_rates = {}
        if b2b_client_supp:
            b2b_client_rates = {
                rate.item_id_id: rate.b2b_client_rate
                for rate in b2b_client_item_rates.objects.filter(
                    org_id=filter_org,
                    supplier_id=b2b_client_supp,
                    item_id__in=[item.item_id for item in item_data]
                ).only('item_id', 'b2b_client_rate')
            }

        # Serialize item data
        serialized_data = []
        for item in item_data:
            supplier_data = item.prefetched_supplierdtl[0] if item.prefetched_supplierdtl else None
            b2b_client_item_rate = b2b_client_rates.get(item.item_id, None)
            available_qty = get_totalSum_available_qty(item.item_id)
            stock_details = item.prefetched_stock[0] if item.prefetched_stock else None

            sales_price = b2b_client_item_rate if b2b_client_item_rate else item.sales_price

            serialized_item = {
                'item_id': item.item_id,
                'item_no': item.item_no,
                'item_name': item.item_name,
                'item_type_name': item.type_id.type_name if hasattr(item, 'type_id') and item.type_id else "Unknown",
                'item_uom': item.item_uom_id.item_uom_name if hasattr(item, 'item_uom_id') and item.item_uom_id else "Unknown",
                'item_Supplier': supplier_data.supplier_id.supplier_name if supplier_data else "Unknown",
                'store_id': stock_details.store_id.store_id if stock_details else "Unknown",
                'store_name': stock_details.store_id.store_name if stock_details else "Unknown",
                'item_price': sales_price,
                'stock_qty': available_qty,
            }

            serialized_data.append(serialized_item)

        # Sort data by stock quantity, similar to previous behavior
        sorted_serialized_data = sorted(
            serialized_data, key=lambda x: x['stock_qty'], reverse=True)

        response_data = {'data': sorted_serialized_data}

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required()
def selectItemListWithSumTotalStockAPI(request):
    if request.method == 'GET' and 'selectedItem' in request.GET:
        store_id = request.GET.get('store_id')
        selected_stock_id = request.GET.get('selectedItem')
        filter_org = request.GET.get('org_id')
        b2b_client_supp = request.GET.get('b2b_client_supp_id')

        try:
            # Get the item object
            item = items.objects.get(
                item_id=selected_stock_id, org_id=filter_org)

            # Get available stock quantity
            available_qty = get_totalSum_available_qty(item.item_id)

            # Get item type name
            item_type_name = item.type_id.type_name if item.type_id else None

            # Fetch the first supplier detail for the item
            supplier_data = item_supplierdtl.objects.filter(
                item_id=item.item_id).first()

            # Fetch b2b client item rate if provided
            b2b_client_item_rate = None
            if b2b_client_supp:
                b2b_client_item_rate = b2b_client_item_rates.objects.filter(
                    org_id=filter_org, supplier_id=b2b_client_supp, item_id=item.item_id
                ).first()

            # Fetch stock details
            stock_details = in_stock.objects.filter(
                item_id=item.item_id, store_id=store_id).first()

            # Build item info dictionary
            item_Supplier = supplier_data.supplier_id.supplier_name if supplier_data else None
            sales_price = b2b_client_item_rate.b2b_client_rate if b2b_client_item_rate else item.sales_price

            if stock_details:
                store_info = {
                    'store_id': stock_details.store_id.store_id,
                    'store_name': stock_details.store_id.store_name
                }
            else:
                # If no stock details, return a default store info (can also be empty if needed)
                store_info = {
                    'store_id': store_id,  # Use the provided store_id
                    'store_name': 'Not Found'  # You can leave this as default or provide a message
                }

            item_info = {
                'store_id': store_info['store_id'],
                'store_name': store_info['store_name'],
                'item_id': item.item_id,
                'org_id': item.org_id.org_id,
                'item_name': item.item_name,
                'item_no': item.item_no,
                'item_type_name': item_type_name,
                'extended_stock': item.extended_stock,
                're_order_qty': item.re_order_qty,
                # Default to 0 if no stock details
                'stock_qty': available_qty if available_qty is not None else 0,
                'item_price': sales_price,
                'item_uom': item.item_uom_id.item_uom_name if item.item_uom_id else None,
                'item_Supplier': item_Supplier,
            }

            # Return the item info whether stock is found or not
            return JsonResponse({'data': [item_info]})

        except items.DoesNotExist:
            return JsonResponse({'error': 'Item does not exist'}, status=404)

    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)
# =======================================================================================


@login_required()
def get_item_listAPI(request):
    selected_store_id = request.GET.get('store_id')
    selected_supplier_id = request.GET.get('filter_suppliers')
    filter_org = request.GET.get('org_id')
    b2b_client_supp = request.GET.get('b2b_client_supp_id')
    search_query = request.GET.get('query', '')  # Get the search query
    page_number = int(request.GET.get('page', 1))
    # Default page size is 100
    page_size = int(request.GET.get('page_size', 100))

    try:
        # Base query for filtering items based on active status and organization
        filters = {'is_active': True, 'org_id': filter_org}

        # Add supplier filter
        if selected_supplier_id and selected_supplier_id != '1':
            filters['item_supplierdtl__supplier_id'] = selected_supplier_id

        # Apply search filters (similar to get_Opening_Stock_listAPI)
        search_filters = Q(item_id__icontains=search_query) | Q(
            item_name__icontains=search_query) | Q(item_no__icontains=search_query)

        # Fetch data with necessary relations and filtering
        item_data_query = items.objects.filter(
            search_filters,
            **filters
        ).select_related('type_id', 'item_uom_id').only(
            'item_id', 'item_no', 'item_name', 'sales_price', 'type_id__type_name', 'item_uom_id__item_uom_name'
        ).prefetch_related(
            Prefetch('item_supplierdtl_set', queryset=item_supplierdtl.objects.select_related(
                'supplier_id').only('supplier_id', 'supplier_id__supplier_name'), to_attr='prefetched_supplierdtl'),
            Prefetch('item_id2in_stock', queryset=in_stock.objects.filter(store_id=selected_store_id).select_related(
                'store_id').only('store_id', 'store_id__store_name', 'stock_qty'), to_attr='prefetched_stock')
        )

        # Pagination similar to get_Opening_Stock_listAPI
        paginator = Paginator(item_data_query, page_size)
        page_obj = paginator.get_page(page_number)
        item_data = list(page_obj)

        # Fetch b2b_client_item_rates if required
        b2b_client_rates = {}
        if b2b_client_supp:
            b2b_client_rates = {
                rate.item_id_id: rate.b2b_client_rate
                for rate in b2b_client_item_rates.objects.filter(
                    org_id=filter_org,
                    supplier_id=b2b_client_supp,
                    item_id__in=[item.item_id for item in item_data]
                ).only('item_id', 'b2b_client_rate')
            }

        # Serialize item data
        serialized_data = []
        for item in item_data:
            supplier_data = item.prefetched_supplierdtl[0] if item.prefetched_supplierdtl else None
            b2b_client_item_rate = b2b_client_rates.get(item.item_id, None)
            available_qty = get_available_qty(
                item.item_id, selected_store_id, filter_org)
            stock_details = item.prefetched_stock[0] if item.prefetched_stock else None

            sales_price = b2b_client_item_rate if b2b_client_item_rate else item.sales_price

            serialized_item = {
                'item_id': item.item_id,
                'item_no': item.item_no,
                'item_name': item.item_name,
                'item_type_name': item.type_id.type_name if hasattr(item, 'type_id') and item.type_id else "Unknown",
                'item_uom': item.item_uom_id.item_uom_name if hasattr(item, 'item_uom_id') and item.item_uom_id else "Unknown",
                'item_Supplier': supplier_data.supplier_id.supplier_name if supplier_data else "Unknown",
                'store_id': stock_details.store_id.store_id if stock_details else "Unknown",
                'store_name': stock_details.store_id.store_name if stock_details else "Unknown",
                'item_price': sales_price,
                'stock_qty': available_qty,
            }

            serialized_data.append(serialized_item)

        # Sort data by stock quantity, similar to previous behavior
        sorted_serialized_data = sorted(
            serialized_data, key=lambda x: x['stock_qty'], reverse=True)

        response_data = {'data': sorted_serialized_data}

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required()
def getItemListWithItemNameAPI(request):
    selected_store_id = request.GET.get('store_id')
    selected_supplier_id = request.GET.get('filter_suppliers')
    filter_org = request.GET.get('org_id')
    b2b_client_supp = request.GET.get('b2b_client_supp_id')
    search_query = request.GET.get('query', '')  # Get the search query
    page_number = int(request.GET.get('page', 1))
    # Default page size is 100
    page_size = int(request.GET.get('page_size', 100))

    try:
        # Base query for filtering items based on active status and organization
        filters = {'is_active': True, 'org_id': filter_org}

        # Add supplier filter
        if selected_supplier_id and selected_supplier_id != '1':
            filters['item_supplierdtl__supplier_id'] = selected_supplier_id

        # Apply search filters (similar to get_Opening_Stock_listAPI)
        search_filters = Q(item_name__icontains=search_query)

        # Fetch data with necessary relations and filtering
        item_data_query = items.objects.filter(
            search_filters,
            **filters
        ).select_related('type_id', 'item_uom_id').only(
            'item_id', 'item_no', 'item_name', 'sales_price', 'type_id__type_name', 'item_uom_id__item_uom_name'
        ).prefetch_related(
            Prefetch('item_supplierdtl_set', queryset=item_supplierdtl.objects.select_related(
                'supplier_id').only('supplier_id', 'supplier_id__supplier_name'), to_attr='prefetched_supplierdtl'),
            Prefetch('item_id2in_stock', queryset=in_stock.objects.filter(store_id=selected_store_id).select_related(
                'store_id').only('store_id', 'store_id__store_name', 'stock_qty'), to_attr='prefetched_stock')
        )

        # Pagination similar to get_Opening_Stock_listAPI
        paginator = Paginator(item_data_query, page_size)
        page_obj = paginator.get_page(page_number)
        item_data = list(page_obj)

        # Fetch b2b_client_item_rates if required
        b2b_client_rates = {}
        if b2b_client_supp:
            b2b_client_rates = {
                rate.item_id_id: rate.b2b_client_rate
                for rate in b2b_client_item_rates.objects.filter(
                    org_id=filter_org,
                    supplier_id=b2b_client_supp,
                    item_id__in=[item.item_id for item in item_data]
                ).only('item_id', 'b2b_client_rate')
            }

        # Serialize item data
        serialized_data = []
        for item in item_data:
            supplier_data = item.prefetched_supplierdtl[0] if item.prefetched_supplierdtl else None
            b2b_client_item_rate = b2b_client_rates.get(item.item_id, None)
            available_qty = get_available_qty(
                item.item_id, selected_store_id, filter_org)
            stock_details = item.prefetched_stock[0] if item.prefetched_stock else None

            sales_price = b2b_client_item_rate if b2b_client_item_rate else item.sales_price

            serialized_item = {
                'item_id': item.item_id,
                'item_no': item.item_no,
                'item_name': item.item_name,
                'item_type_name': item.type_id.type_name if hasattr(item, 'type_id') and item.type_id else "Unknown",
                'item_uom': item.item_uom_id.item_uom_name if hasattr(item, 'item_uom_id') and item.item_uom_id else "Unknown",
                'item_Supplier': supplier_data.supplier_id.supplier_name if supplier_data else "Unknown",
                'store_id': stock_details.store_id.store_id if stock_details else "Unknown",
                'store_name': stock_details.store_id.store_name if stock_details else "Unknown",
                'item_price': sales_price,
                'stock_qty': available_qty,
            }

            serialized_data.append(serialized_item)

        # Sort data by stock quantity, similar to previous behavior
        sorted_serialized_data = sorted(
            serialized_data, key=lambda x: x['stock_qty'], reverse=True)

        response_data = {'data': sorted_serialized_data}

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required()
def select_item_listAPI(request):
    if request.method == 'GET' and 'selectedItem' in request.GET:
        store_id = request.GET.get('store_id')
        selected_stock_id = request.GET.get('selectedItem')
        filter_org = request.GET.get('org_id')
        b2b_client_supp = request.GET.get('b2b_client_supp_id')

        try:
            get_itemID = items.objects.get(
                item_id=selected_stock_id, org_id=filter_org)
            stock_data = in_stock.objects.filter(
                item_id=get_itemID, store_id=store_id).values('item_id', 'stock_qty')

            for item in stock_data:
                item_id = item['item_id']

                available_qty = get_available_qty(
                    item_id, store_id, filter_org)

                item_id = get_itemID.item_id
                item_type_name = get_itemID.type_id.type_name

                supplier_data = item_supplierdtl.objects.filter(
                    item_id=item_id).first()

                b2b_client_item_rate = None

                if b2b_client_supp:
                    b2b_client_item_rate = b2b_client_item_rates.objects.filter(
                        org_id=filter_org, supplier_id=b2b_client_supp, item_id=item_id).first()

                stock_details = in_stock.objects.filter(
                    item_id=item_id, store_id=store_id).first()
                store = stock_details.store_id
                item_Supplier = supplier_data.supplier_id.supplier_name if supplier_data else None
                store_info = {
                    'store_id': store.store_id,
                    'store_name': store.store_name
                }

                if b2b_client_item_rate:
                    sales_price = b2b_client_item_rate.b2b_client_rate
                else:
                    sales_price = get_itemID.sales_price

                item_info = {
                    'store_id': store_info['store_id'],
                    'store_name': store_info['store_name'],
                    'item_id': item_id,
                    'item_name': get_itemID.item_name,
                    'item_no': get_itemID.item_no,
                    'item_type_name': item_type_name,
                    'extended_stock': get_itemID.extended_stock,
                    're_order_qty': get_itemID.re_order_qty,
                    'stock_qty': available_qty,
                    'item_price': sales_price,
                    'item_uom': get_itemID.item_uom_id.item_uom_name,
                    'item_Supplier': item_Supplier,
                }

                return JsonResponse({'data': [item_info]})
            else:
                return JsonResponse({'data': []})
        except stock_lists.DoesNotExist:
            return JsonResponse({'error': 'Stock ID does not exist'}, status=404)
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required()
def selectItemWithoutStocklistAPI(request):
    if request.method == 'GET' and 'selectedItem' in request.GET:
        store_id = request.GET.get('store_id')
        selected_stock_id = request.GET.get('selectedItem')
        filter_org = request.GET.get('org_id')
        b2b_client_supp = request.GET.get('b2b_client_supp_id')

        try:
            # Get the item object
            item = items.objects.get(
                item_id=selected_stock_id, org_id=filter_org)

            # Get available stock quantity
            available_qty = get_available_qty(
                item.item_id, store_id, filter_org)

            # Get item type name
            item_type_name = item.type_id.type_name if item.type_id else None

            # Fetch the first supplier detail for the item
            supplier_data = item_supplierdtl.objects.filter(
                item_id=item.item_id).first()

            # Fetch b2b client item rate if provided
            b2b_client_item_rate = None
            if b2b_client_supp:
                b2b_client_item_rate = b2b_client_item_rates.objects.filter(
                    org_id=filter_org, supplier_id=b2b_client_supp, item_id=item.item_id
                ).first()

            # Fetch stock details
            stock_details = in_stock.objects.filter(
                item_id=item.item_id, store_id=store_id).first()

            # Build item info dictionary
            item_Supplier = supplier_data.supplier_id.supplier_name if supplier_data else None
            sales_price = b2b_client_item_rate.b2b_client_rate if b2b_client_item_rate else item.sales_price

            if stock_details:
                store_info = {
                    'store_id': stock_details.store_id.store_id,
                    'store_name': stock_details.store_id.store_name
                }
            else:
                # If no stock details, return a default store info (can also be empty if needed)
                store_info = {
                    'store_id': store_id,  # Use the provided store_id
                    'store_name': 'Not Found'  # You can leave this as default or provide a message
                }

            item_info = {
                'store_id': store_info['store_id'],
                'store_name': store_info['store_name'],
                'item_id': item.item_id,
                'org_id': item.org_id.org_id,
                'item_name': item.item_name,
                'item_no': item.item_no,
                'item_type_name': item_type_name,
                'extended_stock': item.extended_stock,
                're_order_qty': item.re_order_qty,
                # Default to 0 if no stock details
                'stock_qty': available_qty if stock_details else 0,
                'item_price': sales_price,
                'item_uom': item.item_uom_id.item_uom_name if item.item_uom_id else None,
                'item_Supplier': item_Supplier,
            }

            # Return the item info whether stock is found or not
            return JsonResponse({'data': [item_info]})

        except items.DoesNotExist:
            return JsonResponse({'error': 'Item does not exist'}, status=404)

    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required()
def selectAutomaticItemWithBarcodeAPI(request):
    barcode = request.GET.get('barcode')
    org_id = request.GET.get('org_id')

    try:
        # Use Q objects for a combined query
        item = items.objects.get(
            Q(item_id__icontains=barcode) | Q(item_no__icontains=barcode),
            org_id=org_id
        )
        return JsonResponse({'success': True, 'item_id': item.item_id})
    except items.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'No matching item found.'})
    except items.MultipleObjectsReturned:
        return JsonResponse({'success': False, 'message': 'Multiple items found. Please refine your search.'})


# board store billing save invoice
@login_required()
def saveBoardStoreInvoiceAPI(request):
    resp = {'status': 'failed', 'msg': ''}
    data = request.POST
    cash_point = data.get('cash_point')
    org_id = data.get('org')
    branch_id = data.get('branchs')
    supplier_id = data.get('supplier_id')
    reg_id = data.get('reg_id')
    driver_id = data.get('driver_id')
    driver_name = data.get('driver_name')
    driver_mobile = data.get('driver_mobile')
    general_bill = data.get('general_bill', False)
    b2b_clients = data.get('b2b_clients', False)
    non_register = data.get('non_register', False)
    register = data.get('register', False)
    seller = data.get('seller', False)
    buyer = data.get('buyer', False)
    notapp_carr_cost = data.get('notapp_carr_cost', False)
    is_modified_items = data.get('is_modified_items', False)
    other_exps_amt = data.get('rent_other_expense', '').strip()
    hand_on_cash_amts = data.get('hand_on_cash_amt')
    

    try:
        with transaction.atomic():
            organization_instance = organizationlst.objects.get(org_id=org_id)
            branch_instance = branchslist.objects.get(branch_id=branch_id)
            cash_point_instance = store.objects.get(store_id=cash_point)

            if supplier_id:
                suppliers_instance = suppliers.objects.get(
                    supplier_id=supplier_id)
            else:
                suppliers_instance = None

            if reg_id:
                reg_instance = in_registrations.objects.get(reg_id=reg_id)
            else:
                reg_instance = None

            if driver_id:
                drivers_instance = drivers_list.objects.get(
                    driver_id=driver_id)
            else:
                drivers_instance = None

            invoice = invoice_list.objects.create(
                org_id=organization_instance,
                branch_id=branch_instance,
                supplier_id=suppliers_instance,
                reg_id=reg_instance,
                driver_id=drivers_instance,
                driver_name=driver_name,
                driver_mobile=driver_mobile,
                cash_point=cash_point_instance,
                is_general_bill=general_bill,
                is_b2b_clients=b2b_clients,
                is_non_register=non_register,
                is_register=register,
                is_carrcost_notapp=notapp_carr_cost,
                is_modified_item=is_modified_items,
                customer_name=data['customer_name'],
                gender=data.get('gender', ''),
                mobile_number=data['mobile_number'],
                house_no=data['house_no'],
                floor_no=data['floor_no'],
                road_no=data['road_no'],
                sector_no=data['sector_no'],
                area=data['area'],
                order_no=data['order_no'],
                side_office_factory=data['side_off_factory'],
                address=data['address'],
                remarks=data['remarks'],
                emergency_person=data['emergency_person'],
                emergency_phone=data['emergency_phone'],
                ss_creator=request.user,
                ss_modifier=request.user
            )

            invoice_id = invoice.inv_id
            is_carrcost_notapp = invoice.is_carrcost_notapp
            is_modified = invoice.is_modified_item

            # Fetch all POST data at once
            item_data = list(zip(
                request.POST.getlist('item_id[]'),
                request.POST.getlist('store_id[]'),
                request.POST.getlist('sales_qty[]'),
                request.POST.getlist('item_uoms[]'),
                request.POST.getlist('item_price[]'),
                request.POST.getlist('item_w_dis[]'),
                request.POST.getlist('gross_dis[]'),
                request.POST.getlist('gross_vat_tax[]'),
                request.POST.getlist('item_names[]'),
            ))

            for item_id, store_id, qty, uom_id, price, w_dis, dis, vat_tax, item_name in item_data:
                item_instance = items.objects.get(item_id=item_id)
                store_instance = store.objects.get(store_id=store_id)
                uom_instance = item_uom.objects.get(item_uom_id=uom_id)

                # Check if 'is_modified_items' is set and if the item_name is not empty or None
                if is_modified_items == "1":
                    itemName = item_name  # Use the provided item name if it's valid
                else:
                    itemName = None  # Save as NULL if the item name is not provided or empty

                invoice_detail = invoicedtl_list.objects.create(
                    inv_id=invoice,
                    item_id=item_instance,
                    store_id=store_instance,
                    item_name=itemName,
                    qty=qty,
                    item_uom_id=uom_instance,
                    sales_rate=price,
                    item_w_dis=w_dis,
                    gross_dis=dis,
                    gross_vat_tax=vat_tax,
                    ss_creator=request.user,
                    ss_modifier=request.user,
                )

                # # Update the stock quantity
                # stock, created = in_stock.objects.get_or_create(
                #     item_id=item_instance,
                #     store_id=store_instance,
                #     defaults={
                #         'stock_qty': 0  # Default stock_qty if it doesn't exist
                #     }
                # )

                # # Reduce the stock quantity
                # stock.stock_qty = F('stock_qty') - qty
                # stock.save()

                # # Refresh the stock instance to ensure the correct value after updating
                # stock.refresh_from_db()

            # Ensure 'hand_on_cash_amts' and 'other_exps_amt' are properly converted to float
            other_exps_amt = float(other_exps_amt) if other_exps_amt else 0
            hand_on_cash_amts = float(hand_on_cash_amts) if hand_on_cash_amts else 0
            
            pay_data = list(zip(
                request.POST.getlist('multi_pay_mode[]'),
                request.POST.getlist('multi_collection_mode[]'),
                request.POST.getlist('multi_payment_amt[]'),
                request.POST.getlist('multi_given_amt[]'),
                request.POST.getlist('multi_change_amt[]'),
                request.POST.getlist('multi_card_info[]'),
                request.POST.getlist('multi_pay_mob_number[]'),
                request.POST.getlist('multi_pay_reference[]'),
                request.POST.getlist('multi_bank_name[]'),
            ))

            for pay_mode, collection_mode, payment_amt, given_amt, change_amt, card_info, pay_mob_number, pay_reference, bank_name in pay_data:
                
                # Ensure values are converted properly
                try:
                    payment_amt = float(payment_amt) if payment_amt else 0.0
                    given_amt = float(given_amt) if given_amt else 0.0
                    change_amt = float(change_amt) if change_amt else 0.0
                except ValueError:
                    continue  # Skip this entry if conversion fails

                if float(payment_amt) > 0:
                    payment = payment_list.objects.create(
                        inv_id=invoice,
                        pay_mode=pay_mode,
                        collection_mode=collection_mode,
                        pay_amt=payment_amt,
                        given_amt=given_amt,
                        change_amt=change_amt,
                        card_info=card_info,
                        pay_mob_number=pay_mob_number,
                        pay_reference=pay_reference,
                        bank_name=bank_name,
                        ss_creator=request.user,
                        ss_modifier=request.user,
                    )
                
            if hand_on_cash_amts > 0:
                cashOnHands, created = cash_on_hands.objects.get_or_create(
                    org_id=organization_instance,
                    branch_id=branch_instance,
                    defaults={'on_hand_cash': 0}
                )
                # Update the on_hand_cash by adding the total payment value using F() expression
                cashOnHands.on_hand_cash = F('on_hand_cash') + hand_on_cash_amts
                cashOnHands.save()  # This will save the update in the database

                # Refresh from the database to get the updated value
                cashOnHands.refresh_from_db()

            # Handling cash on hand
            try:
                other_exps_amt = float(other_exps_amt) if other_exps_amt else 0
            except ValueError:
                other_exps_amt = 0

            if  other_exps_amt > 0:
                other_exps_pay = rent_others_exps.objects.create(
                    inv_id=invoice,
                    org_id=organization_instance,
                    branch_id=branch_instance,
                    is_seller=seller,
                    is_buyer=buyer,
                    is_carrying_cost=True,
                    other_exps_reason='Carrying + Lifting Cost',
                    other_exps_amt=other_exps_amt,
                    ss_creator=request.user,
                    ss_modifier=request.user,
                )

            resp['status'] = 'success'
            resp['invoice_id'] = invoice_id
            resp['is_carrcost_notapp'] = is_carrcost_notapp
            resp['is_modified_item'] = is_modified
    except Exception as e:
        resp['msg'] = str(e)

    return JsonResponse(resp)


# Grocery store billing save invoice
@login_required()
def saveGroceryStoreInvoiceAPI(request):
    resp = {'status': 'failed', 'msg': ''}
    data = request.POST
    cash_point = data.get('cash_point')
    org_id = data.get('org')
    branch_id = data.get('branchs')
    reg_id = data.get('reg_id')
    general_bill = data.get('general_bill', False)
    b2b_clients = data.get('b2b_clients', False)
    non_register = data.get('non_register', False)
    register = data.get('register', False)
    pay_amt = data['receivable_amt']
    given_amt = data['given_amt'] if data['given_amt'].strip() else 0
    change_amt = data['change_amt'] if data['change_amt'].strip() else 0
    collection_mode = data['Collection_mode']
    pay_mode = data['pay_mode']
    rewardpoints = data['reward_point']

    try:
        with transaction.atomic():
            organization_instance = organizationlst.objects.get(org_id=org_id)
            branch_instance = branchslist.objects.get(branch_id=branch_id)
            cash_point_instance = store.objects.get(store_id=cash_point)

            # every transection save in cash_on_hands model
            # Convert 'other_exps_amt' to an integer, ensuring it defaults to 0 if empty
            pay_amt = float(pay_amt) if pay_amt else 0
            collection_mode = int(collection_mode) if collection_mode else 0
            pay_mode = int(pay_mode) if pay_mode else 0

            if reg_id:
                reg_instance = in_registrations.objects.get(reg_id=reg_id)
            else:
                reg_instance = None

            invoice = invoice_list.objects.create(
                org_id=organization_instance,
                branch_id=branch_instance,
                reg_id=reg_instance,
                cash_point=cash_point_instance,
                is_general_bill=general_bill,
                is_b2b_clients=b2b_clients,
                is_non_register=non_register,
                is_register=register,
                customer_name=data['customer_name'],
                gender=data.get('gender', ''),
                mobile_number=data['mobile_number'],
                house_no=data['house_no'],
                floor_no=data['floor_no'],
                road_no=data['road_no'],
                sector_no=data['sector_no'],
                area=data['area'],
                address=data['address'],
                remarks=data['remarks'],
                emergency_person=data['emergency_person'],
                emergency_phone=data['emergency_phone'],
                ss_creator=request.user,
                ss_modifier=request.user
            )

            invoice_id = invoice.inv_id

            # Fetch all POST data at once
            item_data = list(zip(
                request.POST.getlist('item_id[]'),
                request.POST.getlist('store_id[]'),
                request.POST.getlist('sales_qty[]'),
                request.POST.getlist('item_uoms[]'),
                request.POST.getlist('item_price[]'),
                request.POST.getlist('item_w_dis[]'),
                request.POST.getlist('gross_dis[]'),
                request.POST.getlist('gross_vat_tax[]'),
                request.POST.getlist('item_names[]'),
            ))

            for item_id, store_id, qty, uom_id, price, w_dis, dis, vat_tax, item_name in item_data:
                item_instance = items.objects.get(item_id=item_id)
                store_instance = store.objects.get(store_id=store_id)
                uom_instance = item_uom.objects.get(item_uom_id=uom_id)

                invoice_detail = invoicedtl_list.objects.create(
                    inv_id=invoice,
                    item_id=item_instance,
                    store_id=store_instance,
                    item_name=item_name,
                    qty=qty,
                    item_uom_id=uom_instance,
                    sales_rate=price,
                    item_w_dis=w_dis,
                    gross_dis=dis,
                    gross_vat_tax=vat_tax,
                    ss_creator=request.user,
                    ss_modifier=request.user,
                )

                # Update the stock quantity
                stock, created = in_stock.objects.get_or_create(
                    item_id=item_instance,
                    store_id=store_instance,
                    defaults={
                        'stock_qty': 0  # Default stock_qty if it doesn't exist
                    }
                )

                # Reduce the stock quantity
                stock.stock_qty = F('stock_qty') - qty
                stock.save()

                # Refresh the stock instance to ensure the correct value after updating
                stock.refresh_from_db()

            # reward point data && Reward point logic
            if reg_id and int(collection_mode) == 1:
                # Get or create the reward point balance record
                rewardPoint, created = reward_points.objects.get_or_create(
                    org_id=organization_instance,
                    branch_id=branch_instance,
                    reg_id=reg_instance,
                    defaults={
                        'reward_balance': 0,
                        'ss_creator': request.user,
                        'ss_modifier': request.user,
                    }
                )

                # Update the reward balance
                rewardpoints = float(rewardpoints)
                rewardPoint.reward_balance = F('reward_balance') + rewardpoints
                rewardPoint.ss_modifier = request.user
                rewardPoint.save()

                # Create reward point details record
                reward_pointsdtls.objects.create(
                    inv_id=invoice,
                    org_id=organization_instance,
                    branch_id=branch_instance,
                    reg_id=reg_instance,
                    reward_dtls_balance=rewardpoints,
                    ss_creator=request.user,
                    ss_modifier=request.user,
                )

            if float(pay_amt) > 0:
                payment = payment_list.objects.create(
                    inv_id=invoice,
                    pay_mode=pay_mode,
                    collection_mode=collection_mode,
                    pay_amt=pay_amt,
                    given_amt=given_amt,
                    change_amt=change_amt,
                    card_info=data['card_info'],
                    pay_mob_number=data['pay_mob_number'],
                    pay_reference=data['pay_reference'],
                    bank_name=data['bank_name'],
                    ss_creator=request.user,
                    ss_modifier=request.user,
                )

                if reg_id and int(collection_mode) == 4:
                    adj_rewardPoint, created = reward_points.objects.get_or_create(
                        org_id=organization_instance,
                        branch_id=branch_instance,
                        reg_id=reg_instance,
                        ss_creator=request.user,
                        ss_modifier=request.user,
                        defaults={
                            'reward_balance': 0
                        }
                    )

                    adj_rewardPoint.reward_balance = F(
                        'reward_balance') - (pay_amt / 2)
                    adj_rewardPoint.save()

            # Proceed only if the conditions for collection are met
            if pay_amt > 0 and collection_mode == 1:
                # Get or create the cash_on_hands record
                cashOnHands, created = cash_on_hands.objects.get_or_create(
                    org_id=organization_instance,
                    branch_id=branch_instance,
                    # Initialize to 0 if a new record is created
                    defaults={'on_hand_cash': 0}
                )

                # Determine the totalPayment based on the pay_mode
                if pay_mode in [1, 5, 6, 7, 8]:
                    totalPayment = pay_amt
                    # Add totalPayment to on_hand_cash
                    cashOnHands.on_hand_cash = F('on_hand_cash') + totalPayment

                # Save the updated cashOnHands and refresh from the database
                cashOnHands.save()
                cashOnHands.refresh_from_db()

            resp['status'] = 'success'
            resp['invoice_id'] = invoice_id
    except Exception as e:
        resp['msg'] = str(e)

    return JsonResponse(resp)


# pharmacy pos billing save invoice
@login_required()
def savePharmacyPOSManagerAPI(request):
    resp = {'status': 'failed', 'msg': ''}
    data = request.POST
    cash_point = data.get('cash_point')
    org_id = data.get('org')
    branch_id = data.get('branchs')
    reg_id = data.get('reg_id')
    general_bill = data.get('general_bill', False)
    b2b_clients = data.get('b2b_clients', False)
    non_register = data.get('non_register', False)
    register = data.get('register', False)
    pay_amt = data['receivable_amt']
    given_amt = data['given_amt'] if data['given_amt'].strip() else 0
    change_amt = data['change_amt'] if data['change_amt'].strip() else 0
    collection_mode = data['Collection_mode']
    pay_mode = data['pay_mode']

    try:
        with transaction.atomic():
            organization_instance = organizationlst.objects.get(org_id=org_id)
            branch_instance = branchslist.objects.get(branch_id=branch_id)
            cash_point_instance = store.objects.get(store_id=cash_point)

            # every transection save in cash_on_hands model
            # Convert 'other_exps_amt' to an integer, ensuring it defaults to 0 if empty
            pay_amt = float(pay_amt) if pay_amt else 0
            collection_mode = int(collection_mode) if collection_mode else 0
            pay_mode = int(pay_mode) if pay_mode else 0

            if reg_id:
                reg_instance = in_registrations.objects.get(reg_id=reg_id)
            else:
                reg_instance = None

            invoice = invoice_list.objects.create(
                org_id=organization_instance,
                branch_id=branch_instance,
                reg_id=reg_instance,
                cash_point=cash_point_instance,
                is_general_bill=general_bill,
                is_b2b_clients=b2b_clients,
                is_non_register=non_register,
                is_register=register,
                customer_name=data['customer_name'],
                gender=data.get('gender', ''),
                mobile_number=data['mobile_number'],
                house_no=data['house_no'],
                floor_no=data['floor_no'],
                road_no=data['road_no'],
                sector_no=data['sector_no'],
                area=data['area'],
                address=data['address'],
                remarks=data['remarks'],
                emergency_person=data['emergency_person'],
                emergency_phone=data['emergency_phone'],
                ss_creator=request.user,
                ss_modifier=request.user
            )

            invoice_id = invoice.inv_id

            # Fetch all POST data at once
            item_data = list(zip(
                request.POST.getlist('item_id[]'),
                request.POST.getlist('store_id[]'),
                request.POST.getlist('sales_qty[]'),
                request.POST.getlist('item_uoms[]'),
                request.POST.getlist('item_price[]'),
                request.POST.getlist('item_w_dis[]'),
                request.POST.getlist('gross_dis[]'),
                request.POST.getlist('gross_vat_tax[]'),
                request.POST.getlist('item_names[]'),
            ))

            for item_id, store_id, qty, uom_id, price, w_dis, dis, vat_tax, item_name in item_data:
                item_instance = items.objects.get(item_id=item_id)
                store_instance = store.objects.get(store_id=store_id)
                uom_instance = item_uom.objects.get(item_uom_id=uom_id)

                invoice_detail = invoicedtl_list.objects.create(
                    inv_id=invoice,
                    item_id=item_instance,
                    store_id=store_instance,
                    item_name=item_name,
                    qty=qty,
                    item_uom_id=uom_instance,
                    sales_rate=price,
                    item_w_dis=w_dis,
                    gross_dis=dis,
                    gross_vat_tax=vat_tax,
                    ss_creator=request.user,
                    ss_modifier=request.user,
                )

                # Update the stock quantity
                stock, created = in_stock.objects.get_or_create(
                    item_id=item_instance,
                    store_id=store_instance,
                    defaults={
                        'stock_qty': 0  # Default stock_qty if it doesn't exist
                    }
                )

                # Reduce the stock quantity
                stock.stock_qty = F('stock_qty') - qty
                stock.save()

                # Refresh the stock instance to ensure the correct value after updating
                stock.refresh_from_db()

            if float(pay_amt) > 0:
                payment = payment_list.objects.create(
                    inv_id=invoice,
                    pay_mode=pay_mode,
                    collection_mode=collection_mode,
                    pay_amt=pay_amt,
                    given_amt=given_amt,
                    change_amt=change_amt,
                    card_info=data['card_info'],
                    pay_mob_number=data['pay_mob_number'],
                    pay_reference=data['pay_reference'],
                    bank_name=data['bank_name'],
                    ss_creator=request.user,
                    ss_modifier=request.user,
                )


            # Proceed only if the conditions for collection are met
            if pay_amt > 0 and collection_mode == 1:
                # Get or create the cash_on_hands record
                cashOnHands, created = cash_on_hands.objects.get_or_create(
                    org_id=organization_instance,
                    branch_id=branch_instance,
                    # Initialize to 0 if a new record is created
                    defaults={'on_hand_cash': 0}
                )

                # Determine the totalPayment based on the pay_mode
                if pay_mode in [1, 5, 6, 7, 8]:
                    totalPayment = pay_amt
                    # Add totalPayment to on_hand_cash
                    cashOnHands.on_hand_cash = F('on_hand_cash') + totalPayment

                # Save the updated cashOnHands and refresh from the database
                cashOnHands.save()
                cashOnHands.refresh_from_db()

            resp['status'] = 'success'
            resp['invoice_id'] = invoice_id
    except Exception as e:
        resp['msg'] = str(e)

    return JsonResponse(resp)


@login_required()
def searchb2bClientsInBillingAPI(request):
    data = []

    org_id_wise_filter = request.GET.get('org_filter', '')

    # Initialize an empty Q object for dynamic filters
    filter_kwargs = Q()

    # Add org_id filter condition only if org_id_wise_filter is not empty
    if org_id_wise_filter:
        filter_kwargs &= Q(org_id=org_id_wise_filter)

    # Include the static flags in the filter
    static_filters = Q(b2bclient_flag=4)

    # Combine static filters with dynamic filters
    combined_filters = static_filters & filter_kwargs

    # Apply combined_filters to the query
    supp_data = suppliers.objects.filter(
        is_active=True).filter(combined_filters)

    for supp_item in supp_data:
        data.append({
            'supplier_id': supp_item.supplier_id,
            'supplier_name': supp_item.supplier_name,
        })

    return JsonResponse({'data': data})


@login_required()
def selectB2bClientsDetailsAPI(request):
    if request.method == 'GET' and 'selectedb2bClient' in request.GET:
        selected_b2b_client = request.GET.get('selectedb2bClient')

        try:
            selected_b2bClient = suppliers.objects.get(
                supplier_id=selected_b2b_client)

            b2bClient_details = []

            b2bClient_details.append({
                'supplier_id': selected_b2bClient.supplier_id,
                'supplier_no': selected_b2bClient.supplier_no,
                'supplier_name': selected_b2bClient.supplier_name,
                'phone': selected_b2bClient.phone if selected_b2bClient.phone else '',
                'address': selected_b2bClient.address if selected_b2bClient.address else '',
            })

            return JsonResponse({'data': b2bClient_details})
        except suppliers.DoesNotExist:
            return JsonResponse({'error': 'suppliers not found'}, status=404)
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)


# =================================== Add Registration in pos =========================================
@login_required()
def addNewRegistrationManagerAPI(request):
    user = request.user

    division_name = 'division'
    district_name = 'district'
    upazila_name = 'upazila'

    if user.is_superuser:
        # If the user is a superuser, retrieve all organizations
        org_list = organizationlst.objects.filter(is_active=True).all()
    elif user.org_id is not None:
        # If the user has an associated organization, retrieve only that organization
        org_list = organizationlst.objects.filter(
            is_active=True, org_id=user.org_id).all()
    else:
        # If neither a superuser nor associated with an organization, set organizations to an empty list or handle as needed
        org_list = []

    divisions = lookup_values.objects.filter(identify_code=division_name).all()
    districts = lookup_values.objects.filter(identify_code=district_name).all()
    upazilas = lookup_values.objects.filter(identify_code=upazila_name).all()

    context = {
        'divisions': divisions,
        'districts': districts,
        'upazilas': upazilas,
        'org_list': org_list,
    }

    return render(request, 'item_pos/pos_reg_setup/add_new_registration.html', context)


# =================================== Item setup in pos =========================================
@login_required()
def itemAddInPosBillingUpdateManagerAPI(request):
    user = request.user

    if user.is_superuser:
        # If the user is a superuser, retrieve all organizations
        org_list = organizationlst.objects.filter(is_active=True).all()
    elif user.org_id is not None:
        # If the user has an associated organization, retrieve only that organization
        org_list = organizationlst.objects.filter(
            is_active=True, org_id=user.org_id).all()
    else:
        # If neither a superuser nor associated with an organization, set organizations to an empty list or handle as needed
        org_list = []

    context = {
        'org_list': org_list,
    }

    return render(request, 'item_pos/pos_item_setup/add_item_pos.html', context)


@login_required()
def addItemPosUpdateInvManagerAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST

    try:
        with transaction.atomic():
            type_id = data.get('item_type_name')
            item_uom_id = data.get('uom_name')
            supplier_id = data.get('manufacturer_name')
            org_id = data.get('org')

            # Fetch instances of related models
            item_type_instance = item_type.objects.get(type_id=type_id)
            uom_id_instance = item_uom.objects.get(item_uom_id=item_uom_id)
            manufac_instance = suppliers.objects.get(supplier_id=supplier_id)
            org_instance = organizationlst.objects.get(org_id=org_id)

            checkitem_name = items.objects.filter(
                Q(item_name=data.get('item_name')) & Q(org_id=org_instance)).exists()
            if checkitem_name:
                return JsonResponse({'success': False, 'errmsg': 'Item Name Already Exists'})

            ############################ item no Auto add ############################
            # Check if any item_no like 'ITM000001' exists for the organization
            latest_item = items.objects.filter(
                org_id=org_instance, item_no__startswith='ITM').order_by('-item_no').first()

            if latest_item:
                # If an item with 'ITM000001' exists, increment its number
                latest_item_no = latest_item.item_no
                prefix = latest_item_no[:3]  # Extract the 'ITM' part
                number_part = latest_item_no[3:]  # Extract the numeric part
                # Increment the number and zero-pad
                itemNoSer = f"{prefix}{str(int(number_part) + 1).zfill(6)}"
            else:
                # If no item exists, set the first item number to 'ITM000001'
                itemNoSer = 'ITM000001'
            ############################ item no Auto add ############################

            # Create a new item
            item_data = items()

            # Set the fields based on request data
            item_data.item_no = itemNoSer
            item_data.item_name = data.get('item_name')
            item_data.sales_price = data.get('item_price')
            item_data.purchase_price = data.get('item_price')
            item_data.org_id = org_instance
            item_data.type_id = item_type_instance
            item_data.item_uom_id = uom_id_instance
            item_data.supplier_id = manufac_instance
            item_data.box_qty = 0
            item_data.re_order_qty = 0
            item_data.is_active = True
            item_data.is_foreign_flag = False
            item_data.is_discount_able = False
            item_data.is_expireable = False
            item_data.extended_stock = 0
            item_data.ss_creator = request.user
            item_data.ss_modifier = request.user
            item_data.save()

            # Create item-supplier relationship
            item_supplierdata = item_supplierdtl(
                item_id=item_data,
                supplier_id=manufac_instance,
                supplier_is_active=True,
                ss_creator=request.user,
                ss_modifier=request.user
            )
            item_supplierdata.save()

            resp['success'] = True
            resp['msg'] = 'Item saved successfully'
    except Exception as e:
        resp['errmsg'] = str(e)

    return JsonResponse(resp)
# =================================== Item setup in pos =========================================

# ========================================== Rent/Others Expense ==========================================
@login_required()
def rentOthersExpsManagerAPI(request):
    user = request.user

    if user.is_superuser:
        # If the user is a superuser, retrieve all organizations
        org_list = organizationlst.objects.filter(is_active=True).all()
    elif user.org_id is not None:
        # If the user has an associated organization, retrieve only that organization
        org_list = organizationlst.objects.filter(
            is_active=True, org_id=user.org_id).all()
    else:
        # If neither a superuser nor associated with an organization, set organizations to an empty list or handle as needed
        org_list = []

    context = {
        'org_list': org_list,
    }
    return render(request, 'rent_others_exps/rent_others_exps.html', context)


@login_required()
def getRentOthersExpsListsAPI(request):
    # Retrieve filter parameters from the frontend
    is_seller_wise_filter = request.GET.get('is_seller')
    is_buyer_wise_filter = request.GET.get('is_buyer')
    is_expense_list = request.GET.get('is_expense_list')
    is_carrying_cost = request.GET.get('is_carrying_cost')
    org_id_wise_filter = request.GET.get('org_id')
    branch_id_wise_filter = request.GET.get('branch_id')
    start_date_wise_filter = request.GET.get('start_date')
    end_date_wise_filter = request.GET.get('end_date')

    filter_kwargs = Q()

    if org_id_wise_filter:
        filter_kwargs &= Q(org_id=org_id_wise_filter)

    if branch_id_wise_filter:  # Exclude branch_id if it's not provided
        filter_kwargs &= Q(branch_id=branch_id_wise_filter)

    # Add date range filter conditions if start_date and end_date are provided
    if start_date_wise_filter and end_date_wise_filter:
        start_date = datetime.strptime(start_date_wise_filter, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_wise_filter, '%Y-%m-%d')
        filter_kwargs &= Q(other_exps_date__range=(start_date, end_date))

    if is_seller_wise_filter == 'true':
        filter_kwargs &= Q(is_seller=True)
    elif is_buyer_wise_filter == 'true':
        filter_kwargs &= Q(is_buyer=True)

    if is_expense_list == 'true':
        filter_kwargs &= Q(is_carrying_cost=False)
    elif is_carrying_cost == 'true':
        filter_kwargs &= Q(is_carrying_cost=True)

    # Apply dynamic filters to rent_others_exps queryset
    expense_data = rent_others_exps.objects.filter(filter_kwargs)

    # Convert expense data to a list of dictionaries
    expenData = []
    for expense in expense_data:
        expenData.append({
            'other_exps_id': expense.other_exps_id,
            'inv_id': expense.inv_id.inv_id if expense.inv_id else None,
            'exps_reason': expense.other_exps_reason,
            'exps_date': expense.other_exps_date,
            'is_seller': expense.is_seller,
            'is_buyer': expense.is_buyer,
            'exps_amt': expense.other_exps_amt,
        })

    # Return the filtered data as JSON
    return JsonResponse({'expen_val': expenData})

# add Expenses modal
@login_required()
def addExpensesModelManageAPI(request):
    user = request.user

    if user.is_superuser:
        # If the user is a superuser, retrieve all organizations
        org_list = organizationlst.objects.filter(is_active=True).all()
    elif user.org_id is not None:
        # If the user has an associated organization, retrieve only that organization
        org_list = organizationlst.objects.filter(
            is_active=True, org_id=user.org_id).all()
    else:
        # If neither a superuser nor associated with an organization, set organizations to an empty list or handle as needed
        org_list = []

    context = {
        'org_list': org_list,
    }
    return render(request, 'rent_others_exps/add_others_exps.html', context)


# Expense add/update view
@login_required()
def addExpenseAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST
    org_id = data.get('org_id')
    branch_id = data.get('branch_id')

    try:
        with transaction.atomic():
            organization_instance = organizationlst.objects.get(org_id=org_id)
            branch_instance = branchslist.objects.get(branch_id=branch_id)

            other_exps_data = rent_others_exps()

            # Update or set the fields based on request data
            other_exps_data.other_exps_amt = data.get('expense_amt')
            other_exps_data.other_exps_reason = data.get('expense_reason')
            other_exps_data.org_id = organization_instance
            other_exps_data.branch_id = branch_instance
            other_exps_data.ss_creator = request.user
            other_exps_data.ss_modifier = request.user
            other_exps_data.save()

            # 
            cashOnHands, created = cash_on_hands.objects.get_or_create(
                    org_id=organization_instance,
                    branch_id=branch_instance,
                    # Initialize to 0 if a new record is created
                    defaults={'on_hand_cash': 0}
                )
            cashOnHands.on_hand_cash = F('on_hand_cash') - data.get('expense_amt')
            cashOnHands.save()
            cashOnHands.refresh_from_db()

            resp['success'] = True
            resp['msg'] = 'Saved successfully'
    except Exception as e:
        resp['errmsg'] = str(e)

    return JsonResponse(resp)
# ========================================== Rent/Others Expense end =====================================

# ========================================== Carrying Cost Payment =======================================
@login_required()
def carryingCostPaymentManagerAPI(request):
    user = request.user

    if user.is_superuser:
        # If the user is a superuser, retrieve all organizations
        org_list = organizationlst.objects.filter(is_active=True).all()
    elif user.org_id is not None:
        # If the user has an associated organization, retrieve only that organization
        org_list = organizationlst.objects.filter(
            is_active=True, org_id=user.org_id).all()
    else:
        # If neither a superuser nor associated with an organization, set organizations to an empty list or handle as needed
        org_list = []

    context = {
        'org_list': org_list,
    }
    return render(request, 'carrying_cost_payment/carrying_cost_payment.html', context)

# Carrying Payment Bill view
@login_required()
def saveCarryingPaymentBillAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST
    org_id = data.get('org_id')
    branch_id = data.get('branch_id')
    driver_id = data.get('driver_id')

    try:
        with transaction.atomic():
            organization_instance = organizationlst.objects.get(org_id=org_id)
            branch_instance = branchslist.objects.get(branch_id=branch_id)
            driver_instance = drivers_list.objects.get(driver_id=driver_id)

            carrying_payment = carrying_cost_payments()

            # Update or set the fields based on request data
            carrying_payment.pay_inv_date = data.get('bill_date')
            carrying_payment.c_cost_amt = data.get('carrying_pay_amt')
            carrying_payment.descriptions = data.get('descriptions')
            carrying_payment.org_id = organization_instance
            carrying_payment.branch_id = branch_instance
            carrying_payment.driver_id = driver_instance
            carrying_payment.ss_creator = request.user
            carrying_payment.ss_modifier = request.user
            carrying_payment.save()

            # 
            cashOnHands, created = cash_on_hands.objects.get_or_create(
                    org_id=organization_instance,
                    branch_id=branch_instance,
                    # Initialize to 0 if a new record is created
                    defaults={'on_hand_cash': 0}
                )
            cashOnHands.on_hand_cash = F('on_hand_cash') - data.get('carrying_pay_amt')
            cashOnHands.save()
            cashOnHands.refresh_from_db()

            resp['success'] = True
            resp['msg'] = 'Saved successfully'
    except Exception as e:
        resp['errmsg'] = str(e)

    return JsonResponse(resp)

@login_required()
def getCarrierPaymentListsAPI(request):
    # Retrieve filter parameters from the frontend
    org_id_wise_filter = request.GET.get('org_id', '').strip()
    branch_id_wise_filter = request.GET.get('branch_id', '').strip()
    start_date_wise_filter = request.GET.get('start_date', '').strip()
    end_date_wise_filter = request.GET.get('end_date', '').strip()

    filter_kwargs = {}

    if org_id_wise_filter:
        filter_kwargs['org_id'] = org_id_wise_filter

    if branch_id_wise_filter:
        filter_kwargs['branch_id'] = branch_id_wise_filter

    if start_date_wise_filter and end_date_wise_filter:
        try:
            start_date = datetime.strptime(start_date_wise_filter, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_wise_filter, '%Y-%m-%d')
            filter_kwargs['c_cost_date__range'] = (start_date, end_date)
        except ValueError:
            return JsonResponse({'error': 'Invalid date format'}, status=400)

    carrying_data = carrying_cost_payments.objects.filter(**filter_kwargs).order_by('-c_cost_date')

    carryingData = [
        {
            'c_cost_id': carrying.c_cost_id,
            'c_cost_date': carrying.c_cost_date.strftime('%d-%m-%Y') if carrying.c_cost_date else None,
            'pay_inv_date': carrying.pay_inv_date.strftime('%d-%m-%Y') if carrying.pay_inv_date else None,
            'org_id': carrying.org_id.org_id if carrying.org_id else None,
            'org_name': carrying.org_id.org_name if carrying.org_id else None,
            'branch_id': carrying.branch_id.branch_id if carrying.branch_id else None,
            'branch_name': carrying.branch_id.branch_name if carrying.branch_id else None,
            'driver_id': carrying.driver_id.driver_id if carrying.driver_id else None,
            'driver_name': carrying.driver_id.driver_name if carrying.driver_id else None,
            'driver_phone': carrying.driver_id.phone if carrying.driver_id else None,
            'c_cost_amt': carrying.c_cost_amt,
            'descriptions': carrying.descriptions,
        }
        for carrying in carrying_data
    ]

    return JsonResponse({'carrying_val': carryingData})


@login_required()
def getDeleteCarryingCostPayModelAPI(request):
    cc_pay_data = {}
    if request.method == 'GET':
        data = request.GET
        c_cost_id = ''
        if 'c_cost_id' in data:
            c_cost_id = data['c_cost_id']
        if c_cost_id.isnumeric() and int(c_cost_id) > 0:
            cc_pay_data = carrying_cost_payments.objects.filter(c_cost_id=c_cost_id).first()

    context = {
        'cc_pay_data': cc_pay_data,
    }
    return render(request, 'carrying_cost_payment/carrying_delete_confirmation.html', context)


@method_decorator(csrf_exempt, name='dispatch')
@require_http_methods(["DELETE"])
def carryingCostPaymentsDtlDeleteAPI(request, c_cost_id):
    try:
        # Try to get data from JSON body first
        try:
            data = json.loads(request.body)
            org_id = data.get('org_id')
            branch_id = data.get('branch_id')
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'errmsg': 'Invalid JSON body.'}, status=400)

        if not org_id or not branch_id:
            return JsonResponse({'success': False, 'errmsg': 'Missing org_id or branch_id.'}, status=400)

        # Fetch the payment details entry
        carrcostpay_DtlIDs = carrying_cost_payments.objects.filter(c_cost_id=c_cost_id).first()

        if not carrcostpay_DtlIDs:
            return JsonResponse({'success': False, 'errmsg': f'Payments details with ID {c_cost_id} not found.'}, status=404)

        # Retrieve values before deletion
        c_cost_amt = carrcostpay_DtlIDs.c_cost_amt
        c_cost_date = carrcostpay_DtlIDs.c_cost_date
        present_date = date.today()
        
        if present_date == c_cost_date:
            # Handle cash payment case
            if c_cost_amt > 0:  # Assuming "1" represents cash payments
                cashOnHands, created = cash_on_hands.objects.get_or_create(
                    org_id=org_id,
                    branch_id=branch_id,
                    defaults={'on_hand_cash': 0}
                )

                # Update the on_hand_cash value
                cashOnHands.on_hand_cash = F('on_hand_cash') + c_cost_amt
                cashOnHands.save(update_fields=['on_hand_cash'])

            # Delete the payment record
            carrcostpay_DtlIDs.delete()

            return JsonResponse({'success': True, 'msg': 'Successfully deleted'})
        else:
            return JsonResponse({'success': False, 'errmsg': 'Only Present Date Carrying Cost Can Be Deleted...'}, status=400)

    except Exception as e:
        return JsonResponse({'success': False, 'errmsg': f'Error occurred: {str(e)}'}, status=500)
    
    # if request.method == 'DELETE':
    #     try:
    #         # Get all the matching chalan details
    #         carrcostpay_DtlIDs = carrying_cost_payments.objects.filter(c_cost_id=c_cost_id)
    #         if carrcostpay_DtlIDs.exists():
    #             # Delete the current carrcostpay_DtlIDs entry
    #             carrcostpay_DtlIDs.delete()
    #             return JsonResponse({'success': True, 'msg': 'Successfully deleted'})
    #         else:
    #             return JsonResponse({'success': False, 'errmsg': f'Carrying Cost Payments details with ID {c_cost_id} not found.'})
    #     except Exception as e:
    #         return JsonResponse({'success': False, 'errmsg': f'Error occurred: {str(e)}'})
        
# ========================================== Carrying Cost Payment end ====================================

# ========================================== favorite list views ==========================================

@login_required
def saveFavoriteItemManagerAPI(request):
    if request.method == "POST":
        item_id = request.POST.get('item_id')
        user = request.user

        try:
            # Check if the item is already in the favorite list
            if not item_fav_list.objects.filter(item_id_id=item_id, user_id=user).exists():
                # Save to favorite list
                item_fav = item_fav_list(item_id_id=item_id, user_id=user)
                item_fav.save()

                return JsonResponse({'status': 'success', 'message': 'Item added to favorites!'})
            else:
                return JsonResponse({'status': 'exists', 'message': 'Item already in favorites!'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


@login_required
def getFavItemListManagerAPI(request):
    # Get the logged-in user
    user = request.user

    # Get the search query from the request
    search_query = request.GET.get('search', '').lower()

    # Filter the favorite items by the authenticated user and the search query
    fav_items = item_fav_list.objects.filter(
        user_id=user).select_related('item_id')

    if search_query:
        fav_items = fav_items.filter(
            item_id__item_name__icontains=search_query)

    # Prepare the data to be returned as JSON
    data = []
    for fav_item in fav_items:
        data.append({
            'fav_id': fav_item.fav_id,
            'item_id': fav_item.item_id.item_id,
            'item_name': fav_item.item_id.item_name,
        })

    return JsonResponse({'fav_items': data})


@login_required
@require_http_methods(["DELETE"])
def delete_fav_item(request, fav_id):
    # Get the logged-in user
    user = request.user

    # Try to find the favorite item and delete it
    fav_item = get_object_or_404(item_fav_list, fav_id=fav_id, user_id=user)
    fav_item.delete()

    return JsonResponse({'status': 'success'})

# ============================================== Reward Point ==============================


@login_required
def getRewardPointBalanceAPI(request):
    data = []

    if request.method == "GET":
        try:
            reg_id = int(request.GET.get('reg_id', 0))
        except (TypeError, ValueError):
            return JsonResponse({'error': 'Invalid or missing reg_id'}, status=400)

        try:
            org_id = int(request.GET.get('org_id', 0)
                         ) if request.GET.get('org_id') else None
        except ValueError:
            return JsonResponse({'error': 'Invalid org_id'}, status=400)

        # Filter transactions
        reward_points_qs = reward_points.objects.filter(reg_id=reg_id)
        if org_id:
            reward_points_qs = reward_points_qs.filter(org_id=org_id)

        data = [{'reward_balance': point.reward_balance}
                for point in reward_points_qs]

        return JsonResponse(data, safe=False)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
def openRewardPointModalAPI(request):
    org_id = request.GET.get('id_org')
    branch_id = request.GET.get('id_branch')
    reg_id = request.GET.get('reg_id')

    org_ids = organizationlst.objects.filter(org_id=org_id).first()
    branch_ids = branchslist.objects.filter(branch_id=branch_id).first()
    reg_ids = in_registrations.objects.filter(reg_id=reg_id).first()

    context = {
        'org_ids': org_ids,
        'branch_ids': branch_ids,
        'reg_ids': reg_ids,
    }

    return render(request, 'item_pos/add_reward_point/add_reward_point.html', context)


@login_required()
def addRewardPointManagerAPI(request):
    # Initialize the response
    resp = {'success': False, 'errmsg': 'Failed'}

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Extract POST data
                org_id = request.POST.get('id_org')
                branch_id = request.POST.get('id_branch')
                reg_id = request.POST.get('reg_id')
                reward_type = request.POST.get('reward_type')
                reward_balance = float(request.POST.get('reward_balance', 0))

                # Validate required fields
                if not all([org_id, branch_id, reg_id, reward_type]):
                    return JsonResponse({'errmsg': 'Missing required fields.'}, status=400)

                if reward_type not in ['1', '2']:
                    return JsonResponse({'errmsg': 'Invalid reward type.'}, status=400)

                # Fetch related instances
                org_instance = organizationlst.objects.filter(org_id=org_id).first()
                branch_instance = branchslist.objects.filter(branch_id=branch_id).first()
                reg_instance = in_registrations.objects.filter(reg_id=reg_id).first()

                if not reg_instance:
                    return JsonResponse({'errmsg': 'Invalid registration ID.'}, status=400)

                # Get or create reward points record
                reward_point, created = reward_points.objects.get_or_create(
                    reg_id_id=reg_instance.pk,  # Pass the primary key
                    defaults={
                        'org_id': org_instance,
                        'branch_id': branch_instance,
                        'reward_balance': reward_balance if reward_type == '1' else 0,
                    }
                )

                # Update reward balance based on reward_type
                if not created:
                    if reward_type == '1':  # Add reward points
                        reward_point.reward_balance = F('reward_balance') + reward_balance
                    elif reward_type == '2':  # Subtract reward points
                        reward_point.reward_balance = F('reward_balance') - reward_balance

                    reward_point.save()
                    reward_point.refresh_from_db()  # Refresh to get the updated value

                resp['success'] = True
                resp['msg'] = 'Reward points updated successfully!'
                return JsonResponse(resp, status=200)

        except Exception as e:
            resp['errmsg'] = str(e)
            return JsonResponse(resp, status=400)

    resp['errmsg'] = 'Invalid request method.'
    return JsonResponse(resp, status=405)
# ============================================== Reward Point ==============================

# ============================================== receipt ==============================
@login_required()
def receipt(request):
    id = request.GET.get('id')
    org_id = request.GET.get('org_id')

    # Fetch the corresponding template based on org_id
    receipttemp = in_bill_receipts.objects.filter(org_id=org_id).first()

    # Determine the template to use
    if receipttemp and receipttemp.receipt_name:
        template_receipt = f'item_pos/receipt/{receipttemp.receipt_name}.html'
    # else:
    #     template_receipt = 'item_pos/receipt/receipt.html'

    sales = invoice_list.objects.filter(inv_id=id).first()
    transaction = {}
    for field in invoice_list._meta.get_fields():
        if field.related_model is None:
            transaction[field.name] = getattr(sales, field.name)
        if 'customer_name' in transaction:
            transaction['customer_name'] = transaction['customer_name']

        # Include related fields for `reg_id` and `org_id`
        transaction['reg_id'] = sales.reg_id.reg_id if sales.reg_id else 0
        transaction['org_id'] = sales.org_id.org_id if sales.org_id else 0
        transaction['first_name'] = sales.ss_creator.first_name if sales.ss_creator else 'Unknown'
        transaction['last_name'] = sales.ss_creator.last_name if sales.ss_creator else 'Unknown'

    ItemList = invoicedtl_list.objects.filter(inv_id=sales).all()
    PayList = payment_list.objects.filter(inv_id=sales).all()
    carrying_cost_buyer = rent_others_exps.objects.filter(
        inv_id=sales, is_buyer=True).all()
    carrying_cost_seller = rent_others_exps.objects.filter(
        inv_id=sales, is_seller=True).all()

    # Gross Total Amt. = qty * sales_rate - item_w_dis_sum = grand total
    grand_total = 0  # Initialize the grand_total
    grand_gross_dis = 0
    grand_gross_vat_tax = 0
    total_collection_amt = 0

    # Initialize the variables
    collection_amt_sum = 0
    due_collection_amt_sum = 0
    refund_amt_sum = 0
    adjust_amt_sum = 0
    total_net_collection = 0
    total_cost_buyer_amt = 0
    total_cost_seller_amt = 0
    tot_given_amt = 0
    tot_change_amt = 0

    for item in ItemList:
        # Calculate the total bill for each item
        item.total_bill = (item.qty - item.is_cancel_qty) * item.sales_rate

        # individual discount
        item.item_wise_disc = (item.item_w_dis / item.qty) * \
            (item.qty - item.is_cancel_qty)
        # total qty = qty - cancel qty
        item.qty_cancelQty = round(item.qty - item.is_cancel_qty, 2)

        item.Item_uom = item.item_uom_id.item_uom_name if item.item_uom_id else item.item_id.item_uom_id.item_uom_name

        # cancel item_w_dis amount
        item.item_w_dis_cancel_amt = (
            item.item_w_dis / item.qty) * item.is_cancel_qty

        # individual item total
        item.total_amount = (item.sales_rate * (item.qty - item.is_cancel_qty)
                             ) - (item.item_w_dis - item.item_w_dis_cancel_amt)
        grand_total += item.total_amount  # Add the item's total bill to the grand_total
        # print('total_amount', item.total_amount)

        # gross discount
        item.gross_dis_inv_amt = (
            item.gross_dis / item.qty) * item.is_cancel_qty
        item.total_gross_dis_with_calcel = item.gross_dis - item.gross_dis_inv_amt
        grand_gross_dis += item.total_gross_dis_with_calcel
        grand_gross_dis = round(grand_gross_dis, 3)

        # gross vat tax
        item.gross_vat_tax_inv_amt = (
            item.gross_vat_tax / item.qty) * item.is_cancel_qty
        item.total_gross_vat_tax_with_calcel = item.gross_vat_tax - item.gross_vat_tax_inv_amt
        grand_gross_vat_tax += item.total_gross_vat_tax_with_calcel
        grand_gross_vat_tax = round(grand_gross_vat_tax, 3)

    # carrying cost from buyer
    for cost_buyer in carrying_cost_buyer:
        cost_buyer_amt = cost_buyer.other_exps_amt
        total_cost_buyer_amt += cost_buyer_amt

    # carrying cost from seller
    for cost_seller in carrying_cost_seller:
        cost_seller_amt = cost_seller.other_exps_amt
        total_cost_seller_amt += cost_seller_amt

    # grand_total + grand_gross_vat_tax - grand_gross_dis
    net_total_amt = (grand_total + grand_gross_vat_tax +
                     total_cost_buyer_amt) - grand_gross_dis
    net_total_amt = round(net_total_amt, 1)

    # pay amount value and find out due value
    # Filter PayList for collection_mode="1" and sum the payments
    collection_amt = PayList.filter(collection_mode="1")
    collection_amt_result = collection_amt.aggregate(
        pay_amt_sum=Sum('pay_amt'))
    if collection_amt_result['pay_amt_sum'] is not None:
        collection_amt_sum = collection_amt_result['pay_amt_sum']

    # Filter PayList for collection_mode="2" and sum the payments
    due_collection_amt = PayList.filter(collection_mode="2")
    due_collection_amt_result = due_collection_amt.aggregate(
        pay_amt_sum=Sum('pay_amt'))
    if due_collection_amt_result['pay_amt_sum'] is not None:
        due_collection_amt_sum = due_collection_amt_result['pay_amt_sum']

    # Filter PayList for collection_mode="3" and sum the payments
    refund_amt = PayList.filter(collection_mode="3")
    refund_amt_result = refund_amt.aggregate(pay_amt_sum=Sum('pay_amt'))
    if refund_amt_result['pay_amt_sum'] is not None:
        refund_amt_sum = refund_amt_result['pay_amt_sum']

    # Filter PayList for collection_mode="4" and sum the payments
    adjust_amt = PayList.filter(collection_mode="4")
    adjust_amt_result = adjust_amt.aggregate(pay_amt_sum=Sum('pay_amt'))
    if adjust_amt_result['pay_amt_sum'] is not None:
        adjust_amt_sum = adjust_amt_result['pay_amt_sum']

    # total payment = collection + due collection - refund
    total_collection_amt = collection_amt_sum + due_collection_amt_sum
    # total net collection
    total_net_collection = (total_collection_amt +
                            adjust_amt_sum) - refund_amt_sum

    # net_due_amt = net_total_amt - pay_amt_sum
    net_due_amt = ((net_total_amt - adjust_amt_sum) -
                   (total_collection_amt - refund_amt_sum))
    # Calculate the net_due_amt and round it to 2 decimal places
    net_due_amt = round(net_due_amt, 0)

    # given amount calculations
    tot_given_amt = PayList.aggregate(total_given=Sum('given_amt'))[
        'total_given'] or 0

    # change amount calculations
    if tot_given_amt == 0:
        tot_change_amt = 0
    else:
        tot_change_amt = tot_given_amt - total_collection_amt

    # inword query
    # Convert total_collection_amt to words
    words = ''
    if total_collection_amt > 0:
        words = f"{num2words(total_collection_amt, lang='en')} Tk. only"

    if adjust_amt_sum > 0:
        words = f"{num2words(adjust_amt_sum, lang='en')} Tk. only"

    if total_collection_amt == 0 and adjust_amt_sum == 0:
        words = f"{num2words(net_due_amt, lang='en')} Tk. only"

    remarks_value = ''
    for remark in PayList:
        remarks_value = remark.remarks if remark.remarks else ''

    context = {
        "transaction": transaction,
        "salesItems": ItemList,
        "PayList": PayList,
        'remarks_value': remarks_value,
        'grand_total': grand_total,
        "grand_gross_dis": grand_gross_dis,
        'grand_gross_vat_tax': grand_gross_vat_tax,
        'net_total_amt': net_total_amt,
        'net_due_amt': net_due_amt,
        "numbers_as_words": words,
        "total_collection_amt": total_collection_amt,
        "adjust_amt_sum": adjust_amt_sum,
        "refund_amt_sum": refund_amt_sum,
        "total_net_collection": total_net_collection,
        "total_cost_buyer_amt": total_cost_buyer_amt,
        "total_cost_seller_amt": total_cost_seller_amt,
        'tot_given_amt': tot_given_amt,
        'tot_change_amt': tot_change_amt,
    }

    return render(request, template_receipt, context)

# ============================================== receipt ==============================
