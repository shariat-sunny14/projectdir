import sys
import json
from django.db.models import Q, F, Sum, ExpressionWrapper, fields, FloatField, IntegerField, Case, When, Value, CharField
from django.db import transaction
from datetime import datetime
from collections import defaultdict
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from po_receive.models import po_receive_details
from purchase_order.models import purchase_order_list, purchase_orderdtls
from item_setup.models import items
from po_return.models import po_return_details
from po_return_receive.models import po_return_received_details
from item_pos.models import invoice_list, invoicedtl_list, payment_list, rent_others_exps
from G_R_N_with_without.models import without_GRN, without_GRNdtl
from registrations.models import in_registrations
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

            # Save data into payment_list
            for invoice in due_invoice_data:
                inv_id = invoice.get('inv_id')
                pay_mode = invoice.get('pay_mode')
                pay_type = invoice.get('pay_type')
                pay_amt = invoice.get('pay_amt')
                comments = invoice.get('id_comments')
                card_info = invoice.get('card_info')
                pay_mob_number = invoice.get('pay_mob_number')
                pay_reference = invoice.get('pay_reference')
                bank_name = invoice.get('bank_name')
                descriptions = invoice.get('id_descriptions')

                if inv_id and pay_amt is not None:
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

            # Save data into invoicedtl_list and sum gross_dis
            for detail in invoice_detail_data:
                invdtl_id = detail.get('invdtl_id')
                gross_dis = detail.get('gross_dis')

                if invdtl_id and gross_dis is not None:
                    # Use F() expressions to sum values
                    invoicedtl_list.objects.filter(invdtl_id=invdtl_id).update(
                        gross_dis=F('gross_dis') + gross_dis
                    )

            return JsonResponse({'success': True, 'message': 'Data saved successfully!'})

        except Exception as e:
            return JsonResponse({'success': False, 'errors': str(e)})

    return JsonResponse({'success': False, 'message': 'Invalid request method.'})
