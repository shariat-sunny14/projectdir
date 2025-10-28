import sys
import json
from django.db.models import Q, F, Sum, ExpressionWrapper, fields, FloatField, IntegerField, Case, When, Value, CharField
from django.db import transaction
from datetime import date, datetime
from collections import defaultdict
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.http import require_POST, require_GET, require_http_methods
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from clients_transection.models import paymentsdtls
from po_receive.models import po_receive_details
from purchase_order.models import purchase_order_list, purchase_orderdtls
from item_setup.models import items
from po_return.models import po_return_details
from po_return_receive.models import po_return_received_details
from item_pos.models import invoice_list, invoicedtl_list, payment_list, rent_others_exps, without_invoice_collection
from G_R_N_with_without.models import without_GRN, without_GRNdtl
from registrations.models import in_registrations
from bank_statement.models import cash_on_hands
from supplier_setup.models import suppliers
from organizations.models import branchslist, organizationlst
from django.contrib.auth import get_user_model
User = get_user_model()



@login_required()
def regClientsCollectionManagerAPI(request):
    user = request.user

    if user.org_id is not None:
        # If the user has an associated organization, retrieve only that organization
        org_list = organizationlst.objects.filter(is_active=True, org_id=user.org_id).all()
    else:
        # If neither a superuser nor associated with an organization, set organizations to an empty list or handle as needed
        org_list = []
    
    if user.branch_id is not None:
            branch_options = branchslist.objects.filter(is_active=True, branch_id=user.branch_id).values('branch_id', 'branch_name')
    
    else:
        branch_options = []

    context = {
        'org_list': org_list,
        'branch_options': branch_options,
    }

    return render(request, 'reg_client_collections/reg_client_collections.html', context)


@login_required()
def getRegClientInvoiceDueStatusAPI(request):
    if request.method == "POST":
        org_id = request.POST.get('org_id')
        branch_id = request.POST.get('branch_id')
        reg_id = request.POST.get('reg_id')  # Fetch reg_id from POST data

        try:
            invoices = invoice_list.objects.filter(org_id=org_id, branch_id=branch_id, reg_id=reg_id)
            invoice_details = invoicedtl_list.objects.all()
            payments = payment_list.objects.all()
            carrying_cost_buyer = rent_others_exps.objects.filter(is_buyer=True)

            combined_data = []

            for invoice in invoices:
                details = invoice_details.filter(inv_id=invoice)
                payment = payments.filter(inv_id=invoice)
                cost_buyer = carrying_cost_buyer.filter(inv_id=invoice)

                # Calculate totals
                grand_total = sum(detail.sales_rate * detail.qty for detail in details)
                grand_total_dis = round(sum(
                    (detail.item_w_dis / detail.qty) * (detail.qty - detail.is_cancel_qty)
                    for detail in details
                ), 2)
                grand_total_gross_dis = round(sum(
                    (detail.gross_dis / detail.qty) * (detail.qty - detail.is_cancel_qty)
                    for detail in details
                ), 2)
                total_discount_sum = round(grand_total_dis + grand_total_gross_dis, 2)

                grand_vat_tax = round(sum(
                    (detail.gross_vat_tax / detail.qty) * (detail.qty - detail.is_cancel_qty)
                    for detail in details
                ), 2)

                grand_cancel_amt = round(sum(
                    detail.sales_rate * detail.is_cancel_qty for detail in details
                ), 2)

                total_cost_amt = sum(buyer.other_exps_amt for buyer in cost_buyer)

                total_net_bill = round(
                    (grand_total + grand_vat_tax + total_cost_amt) - (total_discount_sum + grand_cancel_amt), 0
                )

                total_collection_amt = sum(float(pay.pay_amt) for pay in payment if pay.collection_mode == "1")
                total_due_collection = sum(float(pay.pay_amt) for pay in payment if pay.collection_mode == "2")
                total_refund_amt = sum(float(pay.pay_amt) for pay in payment if pay.collection_mode == "3")
                total_adjust_amt = sum(float(pay.pay_amt) for pay in payment if pay.collection_mode == "4")

                total_payment_collection = round(
                    total_collection_amt + total_due_collection + total_adjust_amt, 0
                )

                total_net_collection = total_payment_collection - total_refund_amt
                total_due_amount = round(total_net_bill - total_net_collection, 0)

                # Add invdtl_id list
                invdtl_ids = [detail.invdtl_id for detail in details]

                if total_due_amount > 0:
                    combined_data.append({
                        'invoice': {
                            'invoice_date': invoice.invoice_date,
                            'inv_id': invoice.inv_id,
                        },
                        'invdtl_ids': invdtl_ids,
                        'grand_total': grand_total,
                        'grand_total_dis': grand_total_dis,
                        'grand_vat_tax': grand_vat_tax,
                        'grand_cancel_amt': grand_cancel_amt,
                        'total_net_bill': total_net_bill,
                        'total_collection_amt': total_collection_amt,
                        'total_due_collection': total_due_collection,
                        'total_refund_amt': total_refund_amt,
                        'total_adjust_amt': total_adjust_amt,
                        'total_payment_collection': total_payment_collection,
                        'grand_total_gross_dis': grand_total_gross_dis,
                        'total_discount_sum': total_discount_sum,
                        'total_due_amount': total_due_amount,
                        'total_cost_amt': total_cost_amt,
                    })

            return JsonResponse({'invoices': combined_data}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method.'}, status=405)



@login_required()
def regClientwiseDueInvoiceDetailsAPI(request):
    id = request.GET.get('id')

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
    carrying_cost_buyer = rent_others_exps.objects.filter(inv_id=sales, is_buyer=True).all()

    # Gross Total Amt. = qty * sales_rate - item_w_dis_sum = grand total
    grand_total = 0  # Initialize the grand_total
    grand_gross_dis = 0
    grand_gross_vat_tax = 0
    total_collection_amt = 0
    

    # Initialize the variables
    refund_amt_sum = 0
    adjust_amt_sum = 0
    total_net_collection = 0
    total_cost_buyer_amt = 0

    for item in ItemList:
        # Calculate the total bill for each item
        item.total_bill = (item.qty - item.is_cancel_qty) * item.sales_rate

        # individual discount
        item.item_wise_disc = (item.item_w_dis / item.qty) * (item.qty - item.is_cancel_qty)
        # total qty = qty - cancel qty
        item.qty_cancelQty = round(item.qty - item.is_cancel_qty, 2)

        item.Item_uom = item.item_uom_id.item_uom_name if item.item_uom_id else item.item_id.item_uom_id.item_uom_name

        # cancel item_w_dis amount
        item.item_w_dis_cancel_amt = (item.item_w_dis / item.qty) * item.is_cancel_qty

        # individual item total
        item.total_amount = (item.sales_rate * (item.qty - item.is_cancel_qty)) - (item.item_w_dis - item.item_w_dis_cancel_amt)
        grand_total += item.total_amount  # Add the item's total bill to the grand_total
        # print('total_amount', item.total_amount)

        # gross discount
        item.gross_dis_inv_amt = (item.gross_dis / item.qty) * item.is_cancel_qty
        item.total_gross_dis_with_calcel = item.gross_dis - item.gross_dis_inv_amt
        grand_gross_dis += item.total_gross_dis_with_calcel
        grand_gross_dis = round(grand_gross_dis, 3)

        # gross vat tax
        item.gross_vat_tax_inv_amt = (item.gross_vat_tax / item.qty) * item.is_cancel_qty
        item.total_gross_vat_tax_with_calcel = item.gross_vat_tax - item.gross_vat_tax_inv_amt
        grand_gross_vat_tax += item.total_gross_vat_tax_with_calcel
        grand_gross_vat_tax = round(grand_gross_vat_tax, 3)
    
    # carrying cost from buyer
    for cost_buyer in carrying_cost_buyer:
        cost_buyer_amt = cost_buyer.other_exps_amt
        total_cost_buyer_amt += cost_buyer_amt


    # grand_total + grand_gross_vat_tax - grand_gross_dis
    net_total_amt = (grand_total + grand_gross_vat_tax + total_cost_buyer_amt) - grand_gross_dis
    net_total_amt = round(net_total_amt, 1)
    

    context = {
        "transaction": transaction,
        "salesItems": ItemList,
        'grand_total': grand_total,
        "grand_gross_dis": grand_gross_dis,
        'grand_gross_vat_tax': grand_gross_vat_tax,
        'net_total_amt': net_total_amt,
        "total_collection_amt": total_collection_amt,
        "adjust_amt_sum": adjust_amt_sum,
        "refund_amt_sum": refund_amt_sum,
        "total_net_collection": total_net_collection,
        "total_cost_buyer_amt": total_cost_buyer_amt,
    }
    
    return render(request, 'reg_client_collections/due_invoice_detais_views.html', context)



@login_required()
@csrf_exempt
def saveRegClientDueCollectionAmtAPI(request):
    if request.method == 'POST':
        try:
            # Parse the incoming JSON data
            data = json.loads(request.body)
            due_invoice_data = data.get('dueInvoiceData', [])
            invoice_detail_data = data.get('invoiceDetailData', [])

            organization_instance = None
            branch_instance = None

            # Save data into payment_list
            for invoice in due_invoice_data:
                inv_id = invoice.get('inv_id')
                pay_mode = int(invoice.get('pay_mode', 0))  # Ensure integer defaulting to 0
                pay_type = int(invoice.get('pay_type', 0))  # Ensure integer defaulting to 0
                pay_amt = float(invoice.get('pay_amt', 0.0))  # Ensure float defaulting to 0.0
                comments = invoice.get('id_comments', '')  # Default to empty string
                card_info = invoice.get('card_info', '')  # Default to empty string
                pay_mob_number = invoice.get('pay_mob_number', '')  # Default to empty string
                pay_reference = invoice.get('pay_reference', '')  # Default to empty string
                bank_name = invoice.get('bank_name', '')  # Default to empty string
                descriptions = invoice.get('id_descriptions', '')  # Default to empty string
                org_ids = invoice.get('org_ids', '')  # Default to empty string
                branch_ids = invoice.get('branch_ids', '')  # Default to empty string
                supplier_ids = invoice.get('supplier_ids', '')  # Default to empty string

                # Ensure valid organization and branch instances
                if org_ids and branch_ids:
                    organization_instance = organizationlst.objects.get(org_id=org_ids)
                    branch_instance = branchslist.objects.get(branch_id=branch_ids)
                    
                supp_instance = None
                if supplier_ids:
                    try:
                        supp_instance = suppliers.objects.get(supplier_id=supplier_ids)
                    except suppliers.DoesNotExist:
                        supp_instance = None

                if inv_id and pay_amt > 0:
                    payment_list.objects.create(
                        inv_id=invoice_list.objects.get(inv_id=inv_id),
                        pay_mode=pay_mode,
                        collection_mode=pay_type,
                        pay_amt=pay_amt,
                        remarks=comments,
                        card_info=card_info,
                        pay_mob_number=pay_mob_number,
                        pay_reference=pay_reference,
                        bank_name=bank_name,
                        descriptions=descriptions,
                        ss_creator=request.user,
                        ss_modifier=request.user,
                    )
                    
                    if supp_instance:
                        paymentsdtls.objects.create(
                            org_id=organization_instance,
                            branch_id=branch_instance,
                            supplier_id=supp_instance,
                            is_reg_client=False,
                            is_supplier_party=True,
                            pay_amount=pay_amt,
                            descriptions=descriptions,
                            pay_mode=pay_mode,
                            pay_type=pay_type,
                            comments=comments,
                            card_info=card_info,
                            pay_mob_number=pay_mob_number,
                            pay_reference=pay_reference,
                            bank_name=bank_name,
                            ss_creator = request.user,
                            ss_modifier = request.user,
                        )

                # Check if pay_mode is valid and pay_amt > 0 before updating cash_on_hands
                if pay_mode == 1 and pay_amt > 0:
                    cashOnHands, created = cash_on_hands.objects.get_or_create(
                        org_id=organization_instance,
                        branch_id=branch_instance,
                        defaults={'on_hand_cash': 0}  # Initialize to 0 if a new record is created
                    )
                    # Use F() expression for atomic update
                    cash_on_hands.objects.filter(
                        org_id=organization_instance,
                        branch_id=branch_instance
                    ).update(on_hand_cash=F('on_hand_cash') + pay_amt)

                    # Refresh instance to reflect DB changes
                    cashOnHands.refresh_from_db()


            # Save data into invoicedtl_list and sum gross_dis
            for detail in invoice_detail_data:
                invdtl_id = detail.get('invdtl_id')
                gross_dis = detail.get('gross_dis')

                if invdtl_id and gross_dis is not None:
                    # Use F() expressions to sum values
                    invoicedtl_list.objects.filter(invdtl_id=invdtl_id).update(
                        gross_dis=F('gross_dis') + gross_dis
                    )

            return JsonResponse({'success': True, 'msg': 'Data saved successfully!'})

        except Exception as e:
            return JsonResponse({'success': False, 'errors': str(e)})

    return JsonResponse({'success': False, 'msg': 'Invalid request method.'})


# ====================== without invoice due collection or manual collections ======================

@login_required()
def withoutInvCollectionManagerAPI(request):
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

    return render(request, 'without_inv_collection/without_inv_collection.html', context)


# Carrying Payment Bill view
@login_required()
def saveWithoutInvoiceCollectionAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST
    org_id = data.get('org')
    branch_id = data.get('branchs')
    reg_id = data.get('reg_id')
    pay_modes = int(data.get('pay_mode'))
    collection_amounts = float(data.get('collection_amount'))
    try:
        with transaction.atomic():
            organization_instance = organizationlst.objects.get(org_id=org_id)
            branch_instance = branchslist.objects.get(branch_id=branch_id)
            # Handle reg_id properly
            reg_instance = None
            if reg_id and reg_id.isdigit():  # Ensure it's a valid number
                reg_instance = in_registrations.objects.get(reg_id=int(reg_id))

            without_inv_coll = without_invoice_collection()

            # Update or set the fields based on request data
            without_inv_coll.org_id = organization_instance
            without_inv_coll.branch_id = branch_instance
            without_inv_coll.reg_id = reg_instance
            without_inv_coll.collection_mode = pay_modes
            without_inv_coll.collection_type = data.get('pay_type')
            without_inv_coll.collection_amt = collection_amounts
            without_inv_coll.customer_name = data.get('customer_name')
            without_inv_coll.gender = data.get('gender')
            without_inv_coll.customer_mobile = data.get('mobile_number')
            without_inv_coll.house_no = data.get('house_no')
            without_inv_coll.floor_no = data.get('floor_no')
            without_inv_coll.road_no = data.get('road_no')
            without_inv_coll.sector_no = data.get('sector_no')
            without_inv_coll.area = data.get('area')
            without_inv_coll.order_no = data.get('order_no')
            without_inv_coll.side_office_factory = data.get('side_off_factory')
            without_inv_coll.address = data.get('address')
            without_inv_coll.emergency_person = data.get('emergency_person')
            without_inv_coll.emergency_phone = data.get('emergency_phone')
            without_inv_coll.descriptions = data.get('descriptions')
            without_inv_coll.comments = data.get('comments')
            without_inv_coll.card_info = data.get('card_info')
            without_inv_coll.mobile_number = data.get('pay_mob_number')
            without_inv_coll.reference = data.get('pay_reference')
            without_inv_coll.bank_name = data.get('bank_name')
            without_inv_coll.ss_creator = request.user
            without_inv_coll.ss_modifier = request.user
            without_inv_coll.save()

            # 
            if pay_modes == 1:
                cashOnHands, created = cash_on_hands.objects.get_or_create(
                        org_id=organization_instance,
                        branch_id=branch_instance,
                        # Initialize to 0 if a new record is created
                        defaults={'on_hand_cash': 0}
                    )
                cashOnHands.on_hand_cash = F('on_hand_cash') + collection_amounts
                cashOnHands.save()
                cashOnHands.refresh_from_db()

            resp['success'] = True
            resp['msg'] = 'Saved successfully'
    except Exception as e:
        resp['errmsg'] = str(e)

    return JsonResponse(resp)


@login_required()
def listsOfWithoutInvoiceCollectionAPI(request):
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
    return render(request, 'without_inv_collection/without_inv_collection_lists.html', context)


@login_required()
def getWithoutInvoiceCollectionDataAPI(request):
    # Retrieve filter parameters from the frontend
    org_id_wise_filter = request.GET.get('org_id')
    branch_id_wise_filter = request.GET.get('branch_id')
    start_date_wise_filter = request.GET.get('start_date')
    end_date_wise_filter = request.GET.get('end_date')

    filter_kwargs = Q()

    if org_id_wise_filter:
        filter_kwargs &= Q(org_id=org_id_wise_filter)

    if branch_id_wise_filter:
        filter_kwargs &= Q(branch_id=branch_id_wise_filter)

    if start_date_wise_filter and end_date_wise_filter:
        try:
            start_date = datetime.strptime(start_date_wise_filter, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_wise_filter, '%Y-%m-%d')
            filter_kwargs &= Q(coll_date__range=(start_date, end_date))
        except ValueError:
            return JsonResponse({'error': 'Invalid date format'}, status=400)

    woinvcoll_data = without_invoice_collection.objects.filter(filter_kwargs)

    woinvcollData = [
        {
            'wo_coll_id': woinvcoll.wo_coll_id,
            'coll_date': woinvcoll.coll_date.strftime('%d-%m-%Y') if woinvcoll.coll_date else None,
            'org_id': woinvcoll.org_id.org_id if woinvcoll.org_id else None,
            'org_name': woinvcoll.org_id.org_name if woinvcoll.org_id else None,
            'branch_id': woinvcoll.branch_id.branch_id if woinvcoll.branch_id else None,
            'branch_name': woinvcoll.branch_id.branch_name if woinvcoll.branch_id else None,
            'reg_id': woinvcoll.reg_id.reg_id if woinvcoll.reg_id else None,
            'customer_name': woinvcoll.reg_id.full_name if woinvcoll.reg_id else woinvcoll.customer_name,
            'customer_mobile': woinvcoll.reg_id.mobile_number if woinvcoll.reg_id else woinvcoll.customer_mobile,
            'collection_amt': woinvcoll.collection_amt,
            'collection_mode': woinvcoll.collection_mode,
            'collection_type': woinvcoll.collection_type,
            'house_no': woinvcoll.house_no,
            'floor_no': woinvcoll.floor_no,
            'road_no': woinvcoll.road_no,
            'sector_no': woinvcoll.sector_no,
            'area': woinvcoll.area,
            'order_no': woinvcoll.order_no,
            'side_office_factory': woinvcoll.side_office_factory,
            'address': woinvcoll.address,
            'emergency_person': woinvcoll.emergency_person,
            'emergency_phone': woinvcoll.emergency_phone,
            'descriptions': woinvcoll.descriptions,
        }
        for woinvcoll in woinvcoll_data
    ]

    return JsonResponse({'woinvcoll_val': woinvcollData})


@login_required()
def getDeleteWithoutInvCollModelAPI(request):
    woinvcoll_data = {}
    if request.method == 'GET':
        data = request.GET
        wo_coll_id = ''
        if 'wo_coll_id' in data:
            wo_coll_id = data['wo_coll_id']
        if wo_coll_id.isnumeric() and int(wo_coll_id) > 0:
            woinvcoll_data = without_invoice_collection.objects.filter(wo_coll_id=wo_coll_id).first()

    context = {
        'woinvcoll_data': woinvcoll_data,
    }
    return render(request, 'without_inv_collection/without_inv_coll_delete_confirm.html', context)


@method_decorator(csrf_exempt, name='dispatch')
@require_http_methods(["DELETE"])
def withoutInvCollectionDtlDeleteAPI(request, wo_coll_id):
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
        woinvcoll_DtlIDs = without_invoice_collection.objects.filter(wo_coll_id=wo_coll_id).first()

        if not woinvcoll_DtlIDs:
            return JsonResponse({'success': False, 'errmsg': f'Payments details with ID {wo_coll_id} not found.'}, status=404)

        # Retrieve values before deletion
        collection_mode = woinvcoll_DtlIDs.collection_mode
        collection_amt = woinvcoll_DtlIDs.collection_amt
        coll_date = woinvcoll_DtlIDs.coll_date
        present_date = date.today()
        
        if present_date == coll_date:
            # Handle cash payment case
            if collection_mode == "1" and collection_amt:  # Assuming "1" represents cash payments
                cashOnHands, created = cash_on_hands.objects.get_or_create(
                    org_id=org_id,
                    branch_id=branch_id,
                    defaults={'on_hand_cash': 0}
                )

                # Update the on_hand_cash value
                cashOnHands.on_hand_cash = F('on_hand_cash') - collection_amt
                cashOnHands.save(update_fields=['on_hand_cash'])

            # Delete the payment record
            woinvcoll_DtlIDs.delete()

            return JsonResponse({'success': True, 'msg': 'Successfully deleted'})
        else:
            return JsonResponse({'success': False, 'errmsg': 'Only Present Date Collection Transaction Can Be Deleted...'}, status=400)

    except Exception as e:
        return JsonResponse({'success': False, 'errmsg': f'Error occurred: {str(e)}'}, status=500)