import sys
import json
import traceback
from collections import defaultdict
from num2words import num2words
from pickle import FALSE
from datetime import datetime
from django.db.models import Q, Sum, F
from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST, require_GET, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.serializers import serialize
from django.utils.dateparse import parse_date
from django.utils import timezone
from item_pos.models import invoice_list, invoicedtl_list, payment_list, rent_others_exps
from organizations.models import branchslist, organizationlst
from item_setup.models import items
from stock_list.stock_qty import get_available_qty
from store_setup.models import store
from stock_list.models import in_stock
from select_bill_receipt.models import in_bill_receipts
from drivers_setup.models import drivers_list
from registrations.models import in_registrations
from . models import delivery_Chalan_list, delivery_Chalandtl_list, manual_delivery_info
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def deliveryChalanManagerAPI(request):
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

    return render(request, 'deliver_chalan/deliver_chalan_list.html', context)


@login_required()
def fetchDeliveryChalanDataAPI(request):
    # Extract filter parameters from the request
    filter_org = request.GET.get('filter_org')
    filter_branch = request.GET.get('filter_branch')
    is_pending_list = request.GET.get('is_pending_list') == "true"
    is_delivered_list = request.GET.get('is_delivered_list') == "true"
    start_form = request.GET.get('start_form')
    end_to = request.GET.get('end_to')

    # Convert date strings to datetime objects
    start_date = parse_date(start_form)
    end_date = parse_date(end_to)

    # Filter the delivery_Chalan_list queryset based on the selected filters
    chalans = delivery_Chalan_list.objects.all()

    if filter_org:
        chalans = chalans.filter(org_id=filter_org)
    if filter_branch:
        chalans = chalans.filter(branch_id=filter_branch)
    if is_pending_list:
        chalans = chalans.filter(is_created=False)
    if is_delivered_list:
        chalans = chalans.filter(is_created=True)
    if start_date:
        chalans = chalans.filter(create_date__gte=start_date)
    if end_date:
        chalans = chalans.filter(create_date__lte=end_date)

    # Prefetch related manual_delivery_info data to minimize database queries
    chalans = chalans.prefetch_related(
        Prefetch(
            'chalan_id2mdeli_info',
            queryset=manual_delivery_info.objects.all(),
            to_attr='manual_info'
        )
    )

    # Serialize the queryset to JSON format
    data = []
    for chalan in chalans:
        chalan_dtl_list = []
        for infoDtl in getattr(chalan, 'manual_info', []):
            chalan_dtl = {
                "customer_name": infoDtl.customer_name,
                "mobile_no": infoDtl.mobile_number,
                "address": infoDtl.address,
            }
            chalan_dtl_list.append(chalan_dtl)

        # Handle cases where customer_name, mobile, or address are empty
        customer_name = chalan.inv_id.customer_name if chalan.inv_id and chalan.inv_id.customer_name else ""
        mobile = chalan.inv_id.mobile_number if chalan.inv_id and chalan.inv_id.mobile_number else ""
        address = chalan.inv_id.address if chalan.inv_id and chalan.inv_id.address else ""

        if not customer_name and chalan_dtl_list:
            customer_name = chalan_dtl_list[0].get("customer_name", "")
        if not mobile and chalan_dtl_list:
            mobile = chalan_dtl_list[0].get("mobile_no", "")
        if not address and chalan_dtl_list:
            address = chalan_dtl_list[0].get("address", "")

        chalan_data = {
            'inv_id': chalan.inv_id.inv_id if chalan.inv_id else '',
            'chalan_id': chalan.chalan_id,
            'create_date': chalan.create_date,
            'invoice_no': chalan.inv_id.inv_id if chalan.inv_id else '',
            'chalan_no': chalan.chalan_id,
            'customer_name': customer_name,
            'mobile': mobile,
            'address': address,
            'is_created': chalan.is_created,
            'is_update': chalan.is_update,
            'is_modified': chalan.is_modified_item,
            'is_manual_chalan': chalan.is_manual_chalan,
            'is_out_sourceing': chalan.is_out_sourceing,
            'is_direct_sales': chalan.is_direct_or_hold,
            'is_hold': chalan.is_direct_or_hold,
            'is_hold_approve': chalan.is_hold_approve,
            'chalans_dtl': chalan_dtl_list,
        }

        data.append(chalan_data)

    return JsonResponse({'data': data})


# edit/update opening stock
@login_required()
def updateDeliveryChalanAPI(request, inv_id=None):
    chalan_data = delivery_Chalan_list.objects.get(inv_id=inv_id)

    context = {
        'chalan_data': chalan_data,
    }
   
    return render(request, 'deliver_chalan/update_delivery_chalan.html', context)


@login_required()
def getDeliveryChalanDataAPI(request):
    inv_id = request.GET.get('inv_id')

    if not inv_id:
        return JsonResponse({'error': 'No Chalan ID provided'}, status=400)

    try:
        # Get Chalan and delivery details
        chalan_data = delivery_Chalan_list.objects.get(inv_id=inv_id)
        inv_detail_data = invoicedtl_list.objects.filter(inv_id=inv_id)
        delivery_detail_data = delivery_Chalandtl_list.objects.filter(inv_id=inv_id)

        store_instances = store.objects.filter(org_id=chalan_data.org_id, is_active=True)

        # Prepare main chalan data
        data = {
            'chalan_id': chalan_data.chalan_id,
            'inv_id': chalan_data.inv_id.inv_id,
            'org_id': chalan_data.org_id.org_id if chalan_data.org_id else '',
            'org_name': chalan_data.org_id.org_name,
            'branch_id': chalan_data.branch_id.branch_name if chalan_data.branch_id else '',
            'store_id': chalan_data.inv_id.cash_point.store_name if chalan_data.inv_id.cash_point else '',
            'customer_name': chalan_data.inv_id.customer_name,
            'road_no': chalan_data.inv_id.road_no,
            'address': chalan_data.inv_id.address,
            'gender': chalan_data.inv_id.gender,
            'mobile_number': chalan_data.inv_id.mobile_number,
            'area': chalan_data.inv_id.area,
            'emergency_person': chalan_data.inv_id.emergency_person,
            'emergency_phone': chalan_data.inv_id.emergency_phone,
            'house_no': chalan_data.inv_id.house_no,
            'sector_no': chalan_data.inv_id.sector_no,
            'driver_id': chalan_data.inv_id.driver_id.driver_id if chalan_data.inv_id.driver_id else '',
            'driver_name': chalan_data.inv_id.driver_name,
            'driver_mobile': chalan_data.inv_id.driver_mobile,
        }

        # Prepare item-wise deliver_qty sums
        item_deliver_qty_sum = {}
        for delivery in delivery_detail_data:
            item_id = delivery.item_id.item_id
            deliver_qty = delivery.deliver_qty
            # Sum the deliver_qty for each unique item_id
            if item_id in item_deliver_qty_sum:
                item_deliver_qty_sum[item_id] += deliver_qty
            else:
                item_deliver_qty_sum[item_id] = deliver_qty

        chalan_details = []

        # Loop over chalan detail data to prepare the response
        for detail in inv_detail_data:
            stores_with_qty = []
            for store_instance in store_instances:
                in_stock_entry = in_stock.objects.filter(item_id=detail.item_id, store_id=store_instance).first()
                stock_qty = in_stock_entry.stock_qty if in_stock_entry else 0
                stores_with_qty.append({
                    'store_id': store_instance.store_id,
                    'store_name': store_instance.store_name,
                    'stock_qty': stock_qty
                })

            # Get the total delivered quantity for the current item_id
            total_deliver_qty = item_deliver_qty_sum.get(detail.item_id.item_id, 0)

            item_modify = detail.inv_id.is_modified_item

            if item_modify:
                item_name = detail.item_name if detail.item_name else ''
            else:
                item_name = detail.item_id.item_name if detail.item_id and detail.item_id.item_name else ''

            # Filter delivery details for the current item
            delivery_chalan_details = [
                {
                    'inv_id': del_detail.inv_id.inv_id,
                    'invdtl_id': del_detail.invdtl_id.invdtl_id,
                    'item_id': del_detail.item_id.item_id,
                    'item_no': del_detail.item_id.item_no,
                    'item_name': del_detail.item_id.item_name,
                    'chanaldtl_id': del_detail.chanaldtl_id,
                    'chalan_id': del_detail.chalan_id.chalan_id,
                    'deliver_qty': del_detail.deliver_qty,
                    'deliver_store': del_detail.deliver_store.store_name,
                    'is_out_sourceing': del_detail.is_out_sourceing,
                    'is_direct_or_hold': del_detail.is_direct_or_hold,
                    'is_hold_approve': del_detail.is_hold_approve,
                    'is_extra_item': del_detail.is_extra_item
                }
                for del_detail in delivery_detail_data if del_detail.item_id.item_id == detail.item_id.item_id
            ]

            # Append the chalan details, including the total deliver_qty for each item
            chalan_details.append({
                'inv_id': detail.inv_id.inv_id,
                'invdtl_id': detail.invdtl_id,
                'item_id': detail.item_id.item_id,
                'item_no': detail.item_id.item_no,
                'item_name': item_name,
                'sales_qty': detail.qty,
                'stores': stores_with_qty,
                'total_deliver_qty': total_deliver_qty,  # Add total deliver qty here
                'delivery_details': delivery_chalan_details,  # Add delivery details
            })

        # Add chalan details to the response data
        data['chalan_details'] = chalan_details

        return JsonResponse(data)

    except delivery_Chalan_list.DoesNotExist:
        return JsonResponse({'error': 'Chalan not found'}, status=404)


@login_required()
def getAllStoreForManualDeliveryChalanAPI(request):
    # Extract the org_id and item_id from the request's GET parameters
    org_id = request.GET.get('org_id', None)
    item_id = request.GET.get('item_id', None)

    # Initialize the queryset for stores
    store_data = store.objects.filter(is_active=True)

    # Filter by org_id if provided
    if org_id:
        store_data = store_data.filter(org_id=org_id)

    # Prepare the store list with stock quantities
    stores_with_qty = []
    for store_instance in store_data:
        stock_qty = 0

        # If item_id is provided, check the stock quantity for the specific item in the store
        if item_id:
            in_stock_entry = in_stock.objects.filter(item_id=item_id, store_id=store_instance).first()
            stock_qty = in_stock_entry.stock_qty if in_stock_entry else 0

        stores_with_qty.append({
            'store_id': store_instance.store_id,
            'store_name': store_instance.store_name,
            'store_no': store_instance.store_no,
            'org_id': store_instance.org_id_id,  # Get the ID of the foreign key
            'branch_id': store_instance.branch_id_id,  # Get the ID of the foreign key
            'is_active': store_instance.is_active,
            'stock_qty': stock_qty
        })

    return JsonResponse({'store_data': stores_with_qty})

    
@login_required()
def saveandUpdateDeliveryChalanAPI(request):
    resp = {'status': 'failed', 'errmsg': 'Update Failed'}

    if request.method == 'POST':
        data = request.POST
        chalan_id = data.get('chalan_id')
        inv_id = data.get('inv_id')
        driver_id = data.get('driver_id')
        driver_name = data.get('driver_name')
        driver_mobile = data.get('driver_mobile')
        deliveryQty = request.POST.getlist('delivery_qty[]')
        chalan_out_sourceing = data.get('chalan_out_sourceing', False)
        chalan_direct_or_hold = data.get('chalan_direct_or_hold', False)

        try:
            with transaction.atomic():
                inv_instance = invoice_list.objects.get(inv_id=inv_id)
                
                for delQty in deliveryQty:
                    # Convert to integer for comparison
                    delQty = float(delQty)
                    if delQty < 0:
                        return JsonResponse({
                            'success': False,
                            'errmsg': 'Not Allowed! This Invoice is Modified and Delivery Qty is Greater Than Sales Qty. Please Clear delivery Items History First, Then create a new Delivery Chalan.'
                        })
                    
                delivery_chalan, created = delivery_Chalan_list.objects.update_or_create(
                    chalan_id=chalan_id,
                    defaults={
                        'inv_id': inv_instance,
                        'is_out_sourceing': chalan_out_sourceing,
                        'is_direct_or_hold': chalan_direct_or_hold,
                        'is_created': True,
                        'is_update': True,
                    }
                )

                delivery_data = list(zip(
                    request.POST.getlist('invdtl_id[]'),
                    request.POST.getlist('item_id[]'),
                    request.POST.getlist('store_name[]'),
                    request.POST.getlist('delivery_qty[]'),
                    request.POST.getlist('out_sourceing[]'),
                    request.POST.getlist('hold_sales[]'),
                ))

                for invdtl_id, item_id, store_name, delivery_qty, out_sourceing, hold_sales in delivery_data:
                    item_instance = items.objects.get(item_id=item_id)
                    store_instance = store.objects.get(store_id=store_name)
                    itemdtl_instance = invoicedtl_list.objects.get(invdtl_id=invdtl_id)

                    deli_qty = float(delivery_qty)

                    if deli_qty > 0:
                        delivery_chalanDtl = delivery_Chalandtl_list.objects.create(
                            del_chalan_date=timezone.now(),
                            chalan_id=delivery_chalan,
                            invdtl_id=itemdtl_instance,
                            inv_id=inv_instance,
                            item_id=item_instance,
                            deliver_store=store_instance,
                            deliver_qty=deli_qty,
                            is_out_sourceing=out_sourceing,
                            is_direct_or_hold=hold_sales,
                            is_extra_item=True,  # Corrected is_extra_item save
                            ss_creator=request.user,
                            ss_modifier=request.user,
                        )

                        # Try to get the existing in_stock entry
                        stock = in_stock.objects.filter(item_id=item_instance, store_id=store_instance).first()

                        if stock:
                            # If the in_stock entry already exists, update the stock quantity by subtracting the delivery_qty
                            stock.stock_qty = F('stock_qty') - deli_qty
                            stock.save()
                            stock.refresh_from_db()  # Ensure the correct value after update
                        else:
                            # If the in_stock entry does not exist, create a new one with initial stock_qty
                            in_stock.objects.create(
                                item_id=item_instance,
                                store_id=store_instance,
                                stock_qty=-deli_qty  # Subtracting since items are delivered
                            )

                # Update invoice_list model if driver information is provided
                if driver_id or driver_name or driver_mobile:
                    driver_instance = None
                    if driver_id:
                        driver_instance = get_object_or_404(drivers_list, driver_id=driver_id)

                    invoice = get_object_or_404(invoice_list, inv_id=inv_id)
                    is_modified = invoice.is_modified_item
                    invoice.driver_id = driver_instance
                    invoice.driver_name = driver_name if driver_name else invoice.driver_name
                    invoice.driver_mobile = driver_mobile if driver_mobile else invoice.driver_mobile
                    invoice.save()

            resp['status'] = 'success'
            resp['inv_id'] = inv_id
            resp['is_modified'] = is_modified
            resp['msg'] = 'Chalan updated successfully!'
            return JsonResponse(resp)

        except Exception as e:
            print(f"Error: {e}")
            resp['errmsg'] = str(e)

    return JsonResponse(resp)


# @login_required()
# def saveandUpdateDeliveryChalanAPI(request):
#     resp = {'status': 'failed', 'errmsg': 'Update Failed'}

#     if request.method == 'POST':
#         data = request.POST
#         chalan_id = data.get('chalan_id')
#         inv_id = data.get('inv_id')
#         driver_id = data.get('driver_id')
#         driver_name = data.get('driver_name')
#         driver_mobile = data.get('driver_mobile')
#         chalan_out_sourceing = data.get('chalan_out_sourceing', False)
#         chalan_direct_or_hold = data.get('chalan_direct_or_hold', False)

#         # Retrieve all fields
#         chanaldtl_ids = data.getlist('chanaldtl_id[]')
#         invdtl_ids = data.getlist('invdtl_id[]')
#         item_ids = data.getlist('item_id[]')
#         store_names = data.getlist('store_name[]')
#         delivery_qtys = data.getlist('delivery_qty[]')

#         # Checkboxes
#         out_sourceings = data.getlist('out_sourceing[]')
#         hold_sales = data.getlist('hold_sales[]')

#         try:
#             list_lengths = {
#                 "chanaldtl_ids": len(chanaldtl_ids),
#                 "invdtl_ids": len(invdtl_ids),
#                 "item_ids": len(item_ids),
#                 "store_names": len(store_names),
#                 "delivery_qtys": len(delivery_qtys),
#                 "out_sourceings": len(out_sourceings),
#                 "hold_sales": len(hold_sales),
#             }
#             print("List lengths: ", list_lengths)

#             min_length = min(len(chanaldtl_ids), len(invdtl_ids), len(item_ids), 
#                              len(store_names), len(delivery_qtys), 
#                              len(out_sourceings), len(hold_sales))

#             with transaction.atomic():
#                 delivery_chalan, created = delivery_Chalan_list.objects.update_or_create(
#                     chalan_id=chalan_id,
#                     defaults={
#                         'inv_id_id': inv_id,
#                         'is_out_sourceing': chalan_out_sourceing,
#                         'is_direct_or_hold': chalan_direct_or_hold,
#                         'is_created': True,
#                         'is_update': True,
#                     }
#                 )

#                 for i in range(min_length):
#                     chanaldtl_id = chanaldtl_ids[i]
#                     invdtl_id = invdtl_ids[i]
#                     item_id = item_ids[i]
#                     store_name = store_names[i]
                    
#                     # Convert delivery_qty to a numeric type before comparison
#                     try:
#                         delivery_qty = float(delivery_qtys[i])  # Use float or int as needed
#                     except ValueError:
#                         raise ValueError(f"Invalid delivery quantity: {delivery_qtys[i]}")

#                     out_sourceing_value = 1 if (i < len(out_sourceings) and out_sourceings[i] == '1') else 0
#                     hold_sales_value = 1 if (i < len(hold_sales) and hold_sales[i] == '1') else 0

#                     if delivery_qty > 0:
#                         delivery_chalanDtl = delivery_Chalandtl_list.objects.create(
#                             del_chalan_date=timezone.now(),
#                             chalan_id=delivery_chalan,
#                             invdtl_id_id=invdtl_id,
#                             inv_id_id=inv_id,
#                             item_id_id=item_id,
#                             deliver_store_id=store_name,
#                             deliver_qty=delivery_qty,
#                             is_out_sourceing=out_sourceing_value,
#                             is_direct_or_hold=hold_sales_value,
#                             is_extra_item=True,  # Corrected is_extra_item save
#                             ss_creator=request.user,
#                             ss_modifier=request.user,
#                         )

#                         # Update or create in_stock entry
#                         item_instance = items.objects.get(item_id=item_id)
#                         store_instance = store.objects.get(store_id=store_name)

#                         # Convert delivery_qty to a numeric type, assuming it's a string
#                         try:
#                             delivery_qty = float(delivery_qty)  # Convert to float (or int if you prefer)
#                         except ValueError:
#                             raise ValueError(f"Invalid delivery quantity: {delivery_qty}")

#                         # Try to get the existing in_stock entry
#                         stock = in_stock.objects.filter(item_id=item_instance, store_id=store_instance).first()

#                         if stock:
#                             # If the in_stock entry already exists, update the stock quantity by subtracting the delivery_qty
#                             stock.stock_qty = F('stock_qty') - delivery_qty
#                             stock.save()
#                             stock.refresh_from_db()  # Ensure the correct value after update
#                         else:
#                             # If the in_stock entry does not exist, create a new one with initial stock_qty
#                             in_stock.objects.create(
#                                 item_id=item_instance,
#                                 store_id=store_instance,
#                                 stock_qty=-delivery_qty  # Subtracting since items are delivered
#                             )

#                 # Update invoice_list model if driver information is provided
#                 if driver_id or driver_name or driver_mobile:
#                     driver_instance = None
#                     if driver_id:
#                         driver_instance = get_object_or_404(drivers_list, driver_id=driver_id)

#                     invoice = get_object_or_404(invoice_list, inv_id=inv_id)
#                     is_modified = invoice.is_modified_item
#                     invoice.driver_id = driver_instance
#                     invoice.driver_name = driver_name if driver_name else invoice.driver_name
#                     invoice.driver_mobile = driver_mobile if driver_mobile else invoice.driver_mobile
#                     invoice.save()

#             resp['status'] = 'success'
#             resp['inv_id'] = inv_id
#             resp['is_modified'] = is_modified
#             resp['msg'] = 'Chalan updated successfully!'
#             return JsonResponse(resp)

#         except Exception as e:
#             print(f"Error: {e}")
#             resp['errmsg'] = str(e)

#     return JsonResponse(resp)


@method_decorator(csrf_exempt, name='dispatch')
@require_http_methods(["DELETE"])
def deleteChalanDetailsItemsWiseAPI(request, invdtl_id):
    if request.method == 'DELETE':
        try:
            # Get all the matching chalan details
            chalan_DtlIDs = delivery_Chalandtl_list.objects.filter(invdtl_id=invdtl_id)

            tot_del_qty = 0  # Initialize total delivery quantity

            # Loop through the matching delivery_Chalandtl_list entries
            for chalan_DtlID in chalan_DtlIDs:
                del_qty = chalan_DtlID.deliver_qty
                tot_del_qty += float(del_qty)  # Accumulate the total delivery quantity

                # Get the item and store related to the current chalan detail
                item_instance = chalan_DtlID.item_id
                store_instance = chalan_DtlID.deliver_store

                # Get or create the in_stock record for this item and store
                stock, created = in_stock.objects.get_or_create(
                    item_id=item_instance,
                    store_id=store_instance,
                    defaults={'stock_qty': 0}  # Default stock_qty if the record is newly created
                )

                # Update the stock quantity (increase by the cancelled invoice quantity)
                stock.stock_qty = F('stock_qty') + del_qty
                stock.save()

                # Refresh the stock instance to ensure the correct value after updating
                stock.refresh_from_db()

                # Delete the current chalan_DtlID entry
                chalan_DtlID.delete()

            return JsonResponse({'success': True, 'msg': 'Successfully deleted'})
        except invoicedtl_list.DoesNotExist:
            return JsonResponse({'success': False, 'errmsg': f'item invoice dtl id {invdtl_id} not found.'})
        except Exception as e:
            return JsonResponse({'success': False, 'errmsg': f'Error occurred while deleting: {str(e)}'})
    return JsonResponse({'success': False, 'errmsg': 'Invalid request method.'})


# ==================================== manual delivery chalan ==========================================
@login_required()
def manualDeliveryChalanManagerAPI(request):
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

    return render(request, 'deliver_chalan/manual_delivery_chalan.html', context)


@login_required()
def editUpdateManualDeliveryChalanManagerAPI(request, chalan_id=None):
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
    chalan_data = delivery_Chalan_list.objects.get(chalan_id=chalan_id)

    context = {
        'org_list': org_list,
        'chalan_data': chalan_data,
    }

    return render(request, 'deliver_chalan/edit_manual_delivery_chalan.html', context)


@login_required()
def getManualDeliveryInfoAPI(request):
    chalan_id = request.GET.get('id_chalan_id')  # Get chalan_id from the AJAX request
    org_id = request.GET.get('org_id', None)

    if not chalan_id:
        return JsonResponse({"success": False, "error": "Chalan ID is required."})

    try:
        # Fetch the related delivery info
        delivery_info = manual_delivery_info.objects.get(chalan_id=chalan_id)
    except manual_delivery_info.DoesNotExist:
        return JsonResponse({"success": False, "error": "Delivery info not found for the provided Chalan ID."})

    # Prepare the response data
    data = {
        "is_non_register": delivery_info.is_non_register,
        "is_register": delivery_info.is_register,
        "chalan_id": delivery_info.chalan_id.chalan_id if delivery_info.chalan_id else 0,
        "org_id": delivery_info.org_id.org_id if delivery_info.org_id else 0,
        "branch_id": delivery_info.branch_id.branch_id if delivery_info.branch_id else 0,
        "cash_point": delivery_info.cash_point.store_id if delivery_info.cash_point else 0,
        "reg_id": delivery_info.reg_id.reg_id if delivery_info.reg_id else 0,
        "driver_id": delivery_info.driver_id.driver_id if delivery_info.driver_id else 0,
        "driver_name": delivery_info.driver_name or "",
        "driver_mobile": delivery_info.driver_mobile or "",
        "customer_name": delivery_info.customer_name or "General Customer",
        "gender": delivery_info.gender or "",
        "mobile_number": delivery_info.mobile_number or "",
        "house_no": delivery_info.house_no or "",
        "floor_no": delivery_info.floor_no or "",
        "road_no": delivery_info.road_no or "",
        "sector_no": delivery_info.sector_no or "",
        "area": delivery_info.area or "",
        "order_no": delivery_info.order_no or "",
        "side_office_factory": delivery_info.side_office_factory or "",
        "address": delivery_info.address or "",
        "remarks": delivery_info.remarks or "",
        "emergency_person": delivery_info.emergency_person or "",
        "emergency_phone": delivery_info.emergency_phone or "",
    }

    # Fetch all delivery item details for the given chalan_id
    delivery_itemdtl = delivery_Chalandtl_list.objects.filter(chalan_id=chalan_id)
    itemdtl_data = [
        {
            "chanaldtl_id": dtl.chanaldtl_id,
            "chalan_id": dtl.chalan_id.chalan_id if dtl.chalan_id else "",
            "item_id": dtl.item_id.item_id if dtl.item_id else "",
            "item_name": dtl.item_id.item_name if dtl.item_id else "",
            "item_no": dtl.item_id.item_no if dtl.item_id else "",
            "deliver_store_id": dtl.deliver_store.store_id if dtl.deliver_store else "",
            "deliver_store": dtl.deliver_store.store_name if dtl.deliver_store else "",
            "delivery_qty": dtl.deliver_qty,
        }
        for dtl in delivery_itemdtl
    ]
    data["itemdtl_data"] = itemdtl_data

    # Fetch store data with optional filtering by org_id
    store_data = store.objects.filter(is_active=True)
    if org_id:
        store_data = store_data.filter(org_id=org_id)

    # Compute stock_qty for each store per item_id
    stores_qty = []
    for item in itemdtl_data:
        item_id = item["item_id"]
        for store_instance in store_data:
            # Calculate stock quantity for the current item_id and store
            stock_qty = 0
            if item_id:
                in_stock_entry = in_stock.objects.filter(item_id=item_id, store_id=store_instance).first()
                stock_qty = in_stock_entry.stock_qty if in_stock_entry else 0

            # Prepare store info for the current item_id
            store_info = {
                "store_id": store_instance.store_id,
                "item_id": item_id,
                "store_name": store_instance.store_name,
                "store_no": store_instance.store_no,
                "org_id": store_instance.org_id.org_id if store_instance.org_id else "",
                "branch_id": store_instance.branch_id.branch_id if store_instance.branch_id else "",
                "is_active": store_instance.is_active,
                "stock_qty": stock_qty,  # Stock quantity for this store and item
            }
            stores_qty.append(store_info)

    data["stores_qty"] = stores_qty

    # Return the prepared response
    return JsonResponse({"success": True, "data": data})
    

# save manual delivery chalan
@login_required()
def saveManualDeliveryChalanAPI(request):
    resp = {'status': 'failed', 'msg': ''}
    data = request.POST
    cash_point = data.get('cash_point')
    org_id = data.get('org')
    branch_id = data.get('branchs')
    reg_id = data.get('reg_id')
    driver_id = data.get('driver_id')
    driver_name = data.get('driver_name')
    driver_mobile = data.get('driver_mobile')
    non_register = data.get('non_register', 'False') == 'True'  # Ensure boolean conversion
    register = data.get('register', 'False') == 'True'  # Ensure boolean conversion

    try:
        with transaction.atomic():
            organization_instance = organizationlst.objects.get(org_id=org_id)
            branch_instance = branchslist.objects.get(branch_id=branch_id)
            cash_point_instance = store.objects.get(store_id=cash_point)

            if reg_id:
                reg_instance = in_registrations.objects.get(reg_id=reg_id)
            else:
                reg_instance = None

            if driver_id:
                drivers_instance = drivers_list.objects.get(driver_id=driver_id)
            else:
                drivers_instance = None

            # Delivery chalan creator
            delivery_chalan = delivery_Chalan_list.objects.create(
                inv_id=None,
                org_id=organization_instance,
                branch_id=branch_instance,
                is_created=True,
                is_update=False,
                is_modified_item=False,
                is_out_sourceing=False,
                is_direct_or_hold=False,
                is_hold_approve=False,
                is_manual_chalan=True,
                ss_creator=request.user,
                ss_modifier=request.user,
            )

            manu_deli_info = manual_delivery_info.objects.create(
                chalan_id=delivery_chalan,
                org_id=organization_instance,
                branch_id=branch_instance,
                reg_id=reg_instance,
                driver_id=drivers_instance,
                driver_name=driver_name,
                driver_mobile=driver_mobile,
                cash_point=cash_point_instance,
                is_non_register=non_register,
                is_register=register,
                customer_name=data.get('customer_name', ''),  # Default to empty string
                gender=data.get('gender', ''),  # Default to empty string
                mobile_number=data.get('mobile_number', ''),  # Default to empty string
                house_no=data.get('house_no', ''),  # Default to empty string
                floor_no=data.get('floor_no', ''),  # Default to empty string
                road_no=data.get('road_no', ''),  # Default to empty string
                sector_no=data.get('sector_no', ''),  # Default to empty string
                area=data.get('area', ''),  # Default to empty string
                order_no=data['order_no'],
                side_office_factory=data['side_off_factory'],
                address=data.get('address', ''),  # Default to empty string
                remarks=data.get('remarks', ''),  # Default to empty string
                emergency_person=data.get('emergency_person', ''),  # Default to empty string
                emergency_phone=data.get('emergency_phone', ''),  # Default to empty string
                ss_creator=request.user,
                ss_modifier=request.user
            )

            chalan_id = delivery_chalan.chalan_id

            # Fetch all POST data at once
            delivery_data = list(zip(
                request.POST.getlist('item_id[]'),
                request.POST.getlist('store_id[]'),
                request.POST.getlist('delivery_qty[]'),
            ))

            for item_id, store_id, delivery_qty in delivery_data:
                item_instance = items.objects.get(item_id=item_id)
                store_instance = store.objects.get(store_id=store_id)

                delivery_qty = float(delivery_qty)

                if delivery_qty > 0:
                    delivery_Chalandtl_list.objects.create(
                        inv_id=None,
                        invdtl_id=None,
                        chalan_id=delivery_chalan,
                        del_chalan_date=timezone.now(),
                        item_id=item_instance,
                        deliver_store=store_instance,
                        deliver_qty=delivery_qty,
                        is_out_sourceing=False,
                        is_direct_or_hold=False,
                        is_hold_approve=False,
                        is_extra_item=False,
                        is_update=False,
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
                stock.stock_qty = F('stock_qty') - delivery_qty
                stock.save()

                # Refresh the stock instance to ensure the correct value after updating
                stock.refresh_from_db()


            resp['status'] = 'success'
            resp['chalan_id'] = chalan_id
    except Exception as e:
        resp['msg'] = str(e)

    return JsonResponse(resp)


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


# update manual delivery chalan
@login_required()
def updateManualDeliveryChalanAPI(request):
    resp = {'status': 'failed', 'msg': ''}
    data = request.POST
    id_chalan_id = data.get('id_chalan_id')  # Fetch id_chalan_id from POST data
    cash_point = data.get('cash_point')
    org_id = data.get('org')
    branch_id = data.get('branchs')
    reg_id = data.get('reg_id')
    driver_id = data.get('driver_id')
    driver_name = data.get('driver_name')
    driver_mobile = data.get('driver_mobile')
    non_register = data.get('non_register', 'False') == 'True'  # Ensure boolean conversion
    register = data.get('register', 'False') == 'True'  # Ensure boolean conversion

    try:
        with transaction.atomic():
            # Fetch related instances
            organization_instance = organizationlst.objects.get(org_id=org_id)
            branch_instance = branchslist.objects.get(branch_id=branch_id)
            cash_point_instance = store.objects.get(store_id=cash_point)

            reg_instance = in_registrations.objects.get(reg_id=reg_id) if reg_id else None
            drivers_instance = drivers_list.objects.get(driver_id=driver_id) if driver_id else None

            # Update or create delivery chalan
            if id_chalan_id:
                delivery_chalan = delivery_Chalan_list.objects.get(chalan_id=id_chalan_id)
                delivery_chalan.org_id = organization_instance
                delivery_chalan.branch_id = branch_instance
                delivery_chalan.ss_modifier = request.user
                delivery_chalan.save(update_fields=['org_id', 'branch_id', 'ss_modifier'])
            else:
                delivery_chalan = delivery_Chalan_list.objects.create(
                    inv_id=None,
                    org_id=organization_instance,
                    branch_id=branch_instance,
                    is_created=True,
                    is_update=False,
                    is_modified_item=False,
                    is_out_sourceing=False,
                    is_direct_or_hold=False,
                    is_hold_approve=False,
                    is_manual_chalan=True,
                    ss_creator=request.user,
                    ss_modifier=request.user,
                )

            # Update or create manual delivery info
            manu_deli_info, created = manual_delivery_info.objects.update_or_create(
                chalan_id=delivery_chalan,
                defaults={
                    'org_id': organization_instance,
                    'branch_id': branch_instance,
                    'reg_id': reg_instance,
                    'driver_id': drivers_instance,
                    'driver_name': driver_name,
                    'driver_mobile': driver_mobile,
                    'cash_point': cash_point_instance,
                    'is_non_register': non_register,
                    'is_register': register,
                    'customer_name': data.get('customer_name', ''),
                    'gender': data.get('gender', ''),
                    'mobile_number': data.get('mobile_number', ''),
                    'house_no': data.get('house_no', ''),
                    'floor_no': data.get('floor_no', ''),
                    'road_no': data.get('road_no', ''),
                    'sector_no': data.get('sector_no', ''),
                    'area': data.get('area', ''),
                    'side_office_factory': data.get('side_off_factory', ''),
                    'order_no': data.get('order_no', ''),
                    'address': data.get('address', ''),
                    'remarks': data.get('remarks', ''),
                    'emergency_person': data.get('emergency_person', ''),
                    'emergency_phone': data.get('emergency_phone', ''),
                    'ss_modifier': request.user,
                }
            )

            # Remove old delivery details if updating
            if id_chalan_id:
                del_chalandtl = delivery_Chalandtl_list.objects.filter(chalan_id=delivery_chalan)

                tot_del_qty = 0

                try:
                    with transaction.atomic():  # Ensure atomicity
                        for dtls in del_chalandtl:
                            # Accumulate the total delivery quantity
                            del_qty = dtls.deliver_qty
                            tot_del_qty += float(del_qty)

                            # Get the item and store related to the current chalan detail
                            item_instance = dtls.item_id
                            store_instance = dtls.deliver_store

                            # Get or create the in_stock record for this item and store
                            stock, created = in_stock.objects.get_or_create(
                                item_id=item_instance,
                                store_id=store_instance,
                                defaults={'stock_qty': 0}  # Default stock_qty if the record is newly created
                            )

                            # Update the stock quantity (increase by the delivery quantity)
                            stock.stock_qty = F('stock_qty') + del_qty
                            stock.save()

                            # Refresh the stock instance to ensure the correct value after updating
                            stock.refresh_from_db()

                            # Delete the current chalan detail entry
                            dtls.delete()

                    resp['status'] = 'success'
                    resp['msg'] = f'Total delivery quantity updated and details deleted successfully. Total: {tot_del_qty}'
                except Exception as e:
                    resp['status'] = 'failed'
                    resp['msg'] = f'Error occurred: {str(e)}'

            # Handle delivery details
            delivery_data = list(zip(
                request.POST.getlist('item_id[]'),
                request.POST.getlist('store_id[]'),
                request.POST.getlist('delivery_qty[]'),
            ))

            for item_id, store_id, delivery_qty in delivery_data:
                item_instance = items.objects.get(item_id=item_id)
                store_instance = store.objects.get(store_id=store_id)

                delivery_qty = float(delivery_qty)

                if delivery_qty > 0:
                    delivery_Chalandtl_list.objects.create(
                        inv_id=None,
                        invdtl_id=None,
                        chalan_id=delivery_chalan,
                        del_chalan_date=timezone.now(),
                        item_id=item_instance,
                        deliver_store=store_instance,
                        deliver_qty=delivery_qty,
                        is_out_sourceing=False,
                        is_direct_or_hold=False,
                        is_hold_approve=False,
                        is_extra_item=False,
                        is_update=False,
                        ss_creator=request.user,
                        ss_modifier=request.user,
                    )

                # Update the stock quantity
                stock, created = in_stock.objects.get_or_create(
                    item_id=item_instance,
                    store_id=store_instance,
                    defaults={'stock_qty': 0}
                )

                # Reduce the stock quantity
                stock.stock_qty = F('stock_qty') - delivery_qty
                stock.save()
                stock.refresh_from_db()

            resp['status'] = 'success'
            resp['chalan_id'] = delivery_chalan.chalan_id

    except Exception as e:
        resp['msg'] = str(e)

    return JsonResponse(resp)

@method_decorator(csrf_exempt, name='dispatch')
@require_http_methods(["DELETE"])
def deleteManualDeliveryChalanDtlsAPI(request, chanaldtl_id):
    if request.method == 'DELETE':
        try:
            # Get all the matching chalan details
            chalan_DtlIDs = delivery_Chalandtl_list.objects.filter(chanaldtl_id=chanaldtl_id)

            tot_del_qty = 0  # Initialize total delivery quantity

            # Loop through the matching delivery_Chalandtl_list entries
            for chalan_DtlID in chalan_DtlIDs:
                del_qty = chalan_DtlID.deliver_qty
                tot_del_qty += float(del_qty)  # Accumulate the total delivery quantity

                # Get the item and store related to the current chalan detail
                item_instance = chalan_DtlID.item_id
                store_instance = chalan_DtlID.deliver_store

                # Get or create the in_stock record for this item and store
                stock, created = in_stock.objects.get_or_create(
                    item_id=item_instance,
                    store_id=store_instance,
                    defaults={'stock_qty': 0}  # Default stock_qty if the record is newly created
                )

                # Update the stock quantity (increase by the cancelled invoice quantity)
                stock.stock_qty = F('stock_qty') + del_qty
                stock.save()

                # Refresh the stock instance to ensure the correct value after updating
                stock.refresh_from_db()

                # Delete the current chalan_DtlID entry
                chalan_DtlID.delete()

            return JsonResponse({'success': True, 'msg': 'Successfully deleted'})
        except invoicedtl_list.DoesNotExist:
            return JsonResponse({'success': False, 'errmsg': f'item invoice dtl id {chanaldtl_id} not found.'})
        except Exception as e:
            return JsonResponse({'success': False, 'errmsg': f'Error occurred while deleting: {str(e)}'})
    return JsonResponse({'success': False, 'errmsg': 'Invalid request method.'})


# ==================================== delivery chalan ==========================================

@login_required()
def deliveryChalan(request):
    id = request.GET.get('id')
    org_id = request.GET.get('org_id')

    chalantemp = in_bill_receipts.objects.filter(org_id=org_id).first()
    template_chalan = f'deliver_chalan/chalan/{chalantemp.chalan_name}.html' if chalantemp and chalantemp.chalan_name else 'deliver_chalan/chalan/delivery_chalan.html'

    sales = invoice_list.objects.filter(inv_id=id).first()
    transaction = {}
    for field in invoice_list._meta.get_fields():
        if field.related_model is None:
            transaction[field.name] = getattr(sales, field.name)

    # Retrieve all items associated with the invoice
    ItemList = delivery_Chalandtl_list.objects.filter(inv_id=sales).all()
    carrying_costs = rent_others_exps.objects.filter(inv_id=sales, is_carrying_cost=True)

    # Grouping items by store and summing their quantities
    grouped_items = defaultdict(lambda: defaultdict(lambda: {'total_deliver_qty': 0, 'item_name': ''}))
    grand_total_qty = 0
    inv_carrying_cost = sum(cost.other_exps_amt for cost in carrying_costs)

    for item in ItemList:
        item.qty_cancelQty = round(item.deliver_qty - item.invdtl_id.is_cancel_qty, 2)
        
        store_name = item.deliver_store.store_name if item.deliver_store else 'Unknown Store'
        item_name = item.item_id.item_name if item.item_id else ''
        item_uom = item.item_id.item_uom_id.item_uom_name if item.item_id and item.item_id.item_uom_id else ''
        
        grouped_items[store_name][item.item_id]['total_deliver_qty'] += item.deliver_qty
        grouped_items[store_name][item.item_id]['item_name'] = item_name  # Store the name for display
        grouped_items[store_name][item.item_id]['item_uom'] = item_uom
        grand_total_qty += item.qty_cancelQty

    # Prepare the context for rendering
    aggregated_items = {}
    for store_name, items in grouped_items.items():
        aggregated_items[store_name] = [
            {'item_id': item_id, 'item_name': details['item_name'], 'item_uom': details['item_uom'], 'total_deliver_qty': details['total_deliver_qty']}
            for item_id, details in items.items()
        ]

    context = {
        "transaction": transaction,
        "grouped_salesItems": aggregated_items,
        'grand_total_qty': grand_total_qty,
        "inv_carrying_cost": inv_carrying_cost,
        "sales": sales,
    }

    return render(request, template_chalan, context)


@login_required()
def deliveryChalanModifiedItems(request):
    id = request.GET.get('id')

    sales = invoice_list.objects.filter(inv_id=id).first()
    transaction = {}
    for field in invoice_list._meta.get_fields():
        if field.related_model is None:
            transaction[field.name] = getattr(sales, field.name)

    # Retrieve all items associated with the invoice
    ItemList = delivery_Chalandtl_list.objects.filter(inv_id=sales).all()
    carrying_costs = rent_others_exps.objects.filter(inv_id=sales, is_carrying_cost=True)

    # Grouping items by store and summing their quantities
    grouped_items = defaultdict(lambda: defaultdict(lambda: {'total_deliver_qty': 0, 'item_name': ''}))
    grand_total_qty = 0
    inv_carrying_cost = sum(cost.other_exps_amt for cost in carrying_costs)

    for item in ItemList:
        item.qty_cancelQty = round(item.deliver_qty - item.invdtl_id.is_cancel_qty, 2)

        item_modify = item.inv_id.is_modified_item

        if item_modify:
            item_name = item.invdtl_id.item_name if item.invdtl_id.item_name else ''
        else:
            item_name = item.item_id.item_name if item.item_id and item.item_id.item_name else ''
        
        store_name = item.deliver_store.store_name if item.deliver_store else 'Unknown Store'
        item_name = item_name
        item_uom = item.item_id.item_uom_id.item_uom_name if item.item_id and item.item_id.item_uom_id else ''
        
        grouped_items[store_name][item.item_id]['total_deliver_qty'] += item.deliver_qty
        grouped_items[store_name][item.item_id]['item_name'] = item_name  # Store the name for display
        grouped_items[store_name][item.item_id]['item_uom'] = item_uom
        grand_total_qty += item.qty_cancelQty

    # Prepare the context for rendering
    aggregated_items = {}
    for store_name, items in grouped_items.items():
        aggregated_items[store_name] = [
            {'item_id': item_id, 'item_name': details['item_name'], 'item_uom': details['item_uom'], 'total_deliver_qty': details['total_deliver_qty']}
            for item_id, details in items.items()
        ]

    context = {
        "transaction": transaction,
        "grouped_salesItems": aggregated_items,
        'grand_total_qty': grand_total_qty,
        "inv_carrying_cost": inv_carrying_cost,
        "sales": sales,
    }

    return render(request, 'deliver_chalan/chalan/board_chalan_modify_item.html', context)


@login_required()
def manualDeliveryChalanReceipts(request):
    id = request.GET.get('id')
    org_id = request.GET.get('org_id')

    chalantemp = in_bill_receipts.objects.filter(org_id=org_id).first()
    template_chalan = f'deliver_chalan/chalan/{chalantemp.chalan_name}.html' if chalantemp and chalantemp.chalan_name else 'deliver_chalan/chalan/delivery_chalan.html'

    chalan_instance = delivery_Chalan_list.objects.get(chalan_id=id)

    sales = manual_delivery_info.objects.filter(chalan_id=chalan_instance).first()
    transaction = {}
    for field in manual_delivery_info._meta.get_fields():
        if field.related_model is None:
            transaction[field.name] = getattr(sales, field.name)

    # Retrieve all items associated with the invoice
    ItemList = delivery_Chalandtl_list.objects.filter(chalan_id=chalan_instance).all()

    # Grouping items by store and summing their quantities
    grouped_items = defaultdict(lambda: defaultdict(lambda: {'total_deliver_qty': 0, 'item_name': ''}))
    grand_total_qty = 0

    for item in ItemList:
        item.qty_cancelQty = round(item.deliver_qty, 2)
        
        store_name = item.deliver_store.store_name if item.deliver_store else 'Unknown Store'
        item_name = item.item_id.item_name if item.item_id else ''
        item_uom = item.item_id.item_uom_id.item_uom_name if item.item_id and item.item_id.item_uom_id else ''
        
        grouped_items[store_name][item.item_id]['total_deliver_qty'] += item.deliver_qty
        grouped_items[store_name][item.item_id]['item_name'] = item_name  # Store the name for display
        grouped_items[store_name][item.item_id]['item_uom'] = item_uom
        grand_total_qty += item.qty_cancelQty

    # Prepare the context for rendering
    aggregated_items = {}
    for store_name, items in grouped_items.items():
        aggregated_items[store_name] = [
            {'item_id': item_id, 'item_name': details['item_name'], 'item_uom': details['item_uom'], 'total_deliver_qty': details['total_deliver_qty']}
            for item_id, details in items.items()
        ]

    context = {
        "transaction": transaction,
        "grouped_salesItems": aggregated_items,
        'grand_total_qty': grand_total_qty,
        "sales": sales,
    }

    return render(request, template_chalan, context)