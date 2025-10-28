import sys
import json
from django.db.models import Q, F, Sum, ExpressionWrapper, fields, FloatField, IntegerField, Case, When, Value, CharField
from django.db.models.functions import Coalesce
from django.db import transaction
from datetime import datetime
from collections import defaultdict
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET, require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from po_receive.models import po_receive_details
from purchase_order.models import purchase_order_list, purchase_orderdtls
from item_setup.models import items
from po_return.models import po_return_details
from po_return_receive.models import po_return_received_details
from item_pos.models import invoice_list, invoicedtl_list, payment_list, rent_others_exps
from G_R_N_with_without.models import without_GRN, without_GRNdtl
from clients_transection.models import paymentsdtls
from bank_statement.models import cash_on_hands
from . models import credit_transactions
from supplier_setup.models import suppliers
from organizations.models import branchslist, organizationlst
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def supplierOpeningBalanceAPI(request):
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

    return render(request, 'supplier_opening_balance/supplier_opening_balance.html', context)
    # return render(request, 'supplier_opening_balance/supplier_opening_balance_copy.html', context)


@login_required()
def supplierLedgerReportListsAPI(request):
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

    return render(request, 'supplier_ledger_report/supplier_ledger_report.html', context)

@login_required()
def supplierClientsDetailsReportsAPI(request, supplier_id=None):
    user = request.user
    
    if user.org_id is not None:
        # If the user has an associated organization, retrieve only that organization
        org_list = organizationlst.objects.filter(is_active=True, org_id=user.org_id).all()
    else:
        # If neither a superuser nor associated with an organization, set organizations to an empty list or handle as needed
        org_list = []

    supp_data = suppliers.objects.filter(is_active=True, supplier_id=supplier_id).first()

    context = {
        'org_data': org_list,
        'supp_data': supp_data,
    }

    return render(request, 'supplier_ledger_report/supplier_ledger_details_report.html', context)


@login_required()
def getSuppLedgerReportListsAPI(request):
    org_id = request.GET.get('filter_org', '')

    # Filtering
    filter_kwargs = Q()
    if org_id:
        filter_kwargs &= Q(org_id=org_id)

    # Query only necessary fields
    suppliers_list = suppliers.objects.filter(filter_kwargs).values(
        'supplier_id', 'supplier_no', 'supplier_name', 'phone', 'company_name', 'is_active', 'org_id__org_name'
    )

    # Rename `org_id__org_name` to `org_name`
    data = [
        {**item, 'org_name': item.pop('org_id__org_name', None)}
        for item in suppliers_list
    ]

    return JsonResponse({'data': data})


# get client list
@login_required()
def getClientsListAPI(request):
    supp_search_query = request.GET.get('supp_search_query', '')
    org_id_wise_filter = request.GET.get('org_filter', '')

    # Initialize an empty Q object for dynamic filters
    filter_kwargs = Q()

    # Add search conditions only if supp_search_query is not empty
    if supp_search_query:
        filter_kwargs |= Q(supplier_name__icontains=supp_search_query) | Q(supplier_no__icontains=supp_search_query)

    # Add org_id filter condition only if org_id_wise_filter is not empty
    if org_id_wise_filter:
        filter_kwargs &= Q(org_id=org_id_wise_filter)

    # Include the static flags in the filter
    static_filters = (Q(supplier_flag=2) | Q(b2bclient_flag=4))

    # Combine static filters with dynamic filters
    combined_filters = static_filters & filter_kwargs

    # Apply combined_filters to the query
    supp_data = suppliers.objects.filter(is_active=True).filter(combined_filters)

    data = []
    for supp_item in supp_data:
        data.append({
            'supplier_id': supp_item.supplier_id,
            'supplier_no': supp_item.supplier_no,
            'supplier_name': supp_item.supplier_name,
            'phone_no': supp_item.phone,
        })

    return JsonResponse({'data': data})


# credit transaction add view
@login_required()
def addCreditTransactionAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST
    org_id=data.get('filter_org')
    branch_id=data.get('filter_branch')
    supplier_id=data.get('supplier_id')
    is_debited=data.get('is_debited', False)
    is_credited=data.get('is_credited', False)
    credit_payment=data.get('credit_payment')
    descriptions=data.get('descriptions', '')

    try:
        org_instance = organizationlst.objects.get(org_id=org_id)
    except organizationlst.DoesNotExist:
        resp['errmsg'] = 'Organization not found'
        return JsonResponse(resp)

    try:
        branch_instance = branchslist.objects.get(branch_id=branch_id)
    except branchslist.DoesNotExist:
        resp['errmsg'] = 'Branch not found'
        return JsonResponse(resp)

    try:
        supplier_instance = suppliers.objects.get(supplier_id=supplier_id)
    except suppliers.DoesNotExist:
        resp['errmsg'] = 'Supplier not found'
        return JsonResponse(resp)

    credit_trans = credit_transactions(
        org_id=org_instance,
        branch_id=branch_instance,
        supplier_id=supplier_instance,
        credit_payment=credit_payment,
        is_debited=is_debited,
        is_credited=is_credited,
        descriptions=descriptions,
        ss_creator = request.user,
        ss_modifier = request.user,
    )
    credit_trans.save()
    resp = {'success': True, 'msg': 'Saved successfully'}

    return JsonResponse(resp)


@login_required()
def getSupplierOpBalAmtAPI(request):
    if request.method == "GET":
        # Get the organization and registration IDs from the query parameters
        org_id = request.GET.get('org_id')
        branch_id = request.GET.get('branch_id')
        supplier_id = request.GET.get('supplier_id')

        # Filter the opening balances based on org_id and reg_id
        supp_op_bal = credit_transactions.objects.all()

        if org_id:
            supp_op_bal = supp_op_bal.filter(org_id=org_id)

        if branch_id:
            supp_op_bal = supp_op_bal.filter(branch_id=branch_id)

        if supplier_id:
            supp_op_bal = supp_op_bal.filter(supplier_id=supplier_id)

        # Retrieve the values to return
        supp_op_bal = supp_op_bal.values(
            'credit_id',
            'credit_pay_date',
            'org_id',
            'branch_id',
            'supplier_id',
            'is_debited',
            'is_credited',
            'descriptions',
            'credit_payment',
        )
        
        data = list(supp_op_bal)  # Convert queryset to a list of dictionaries
        return JsonResponse(data, safe=False)

@login_required()
def deleteSupplierOpBalDtlsModalAPI(request):
    opb_data = {}
    if request.method == 'GET':
        data = request.GET
        credit_id = ''
        if 'credit_id' in data:
            credit_id = data['credit_id']
        if credit_id.isnumeric() and int(credit_id) > 0:
            opb_data = credit_transactions.objects.filter(credit_id=credit_id).first()

    context = {
        'opb_data': opb_data,
    }
    return render(request, 'supplier_opening_balance/delete_confirmation.html', context)
    

@method_decorator(csrf_exempt, name='dispatch')
@require_http_methods(["DELETE"])
def supplierOpBalDtlsDeleteAPI(request, credit_id):
    if request.method == 'DELETE':
        try:
            # Get all the matching chalan details
            opening_DtlIDs = credit_transactions.objects.filter(credit_id=credit_id)
            if opening_DtlIDs.exists():
                # Delete the current opening_DtlIDs entry
                opening_DtlIDs.delete()
                return JsonResponse({'success': True, 'msg': 'Successfully deleted'})
            else:
                return JsonResponse({'success': False, 'errmsg': f'Opening Balance details with ID {credit_id} not found.'})
        except Exception as e:
            return JsonResponse({'success': False, 'errmsg': f'Error occurred: {str(e)}'})

# ================================ report ================================

# get transaction summary report
@login_required()
def getTransactionsSummaryReportAPI(request):
    try:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            supplier_id = request.GET.get('supplier_id')
            org_id = request.GET.get('org_id')

            if not supplier_id or not supplier_id.isdigit():
                return JsonResponse({'error': 'Invalid supplier_id'}, status=400)
        
            if not org_id or not org_id.isdigit():
                return JsonResponse({'error': 'Invalid org_id'}, status=400)

            data = []
            supplier_id = int(supplier_id)
            org_id = int(org_id)

            # Fetch credited transactions
            credited_trans = credit_transactions.objects.filter(is_credited=True, org_id=org_id, supplier_id=supplier_id)
            for trans in credited_trans:
                data.append({
                    'credit_id': trans.credit_id,
                    'debit_opening': '0',
                    'credit_opening': trans.credit_payment,
                    'debit_payment': '0',
                    'credit_payment': '0',
                    'credit_pay_date': trans.credit_pay_date,
                    'type_of': 'Opening Balance (Cr.)'
                })

            # Fetch debited transactions
            debited_trans = credit_transactions.objects.filter(is_debited=True, org_id=org_id, supplier_id=supplier_id)
            for trans in debited_trans:
                data.append({
                    'credit_id': trans.credit_id,
                    'debit_opening': trans.credit_payment,
                    'credit_opening': '0',
                    'debit_payment': '0',
                    'credit_payment': '0',
                    'credit_pay_date': trans.credit_pay_date,
                    'type_of': 'Opening Balance (Dr.)'
                })

            # Fetch supplier payment details
            supp_paydtls = paymentsdtls.objects.filter(is_supplier_party=True, org_id=org_id, supplier_id=supplier_id)
            for paydtls in supp_paydtls:
                data.append({
                    'credit_id': paydtls.pay_id,
                    'debit_opening': '0',
                    'credit_opening': '0',
                    'debit_payment': paydtls.pay_amount,
                    'credit_payment': '0',
                    'credit_pay_date': paydtls.pay_date,
                    'type_of': 'Supplier Payment Details (Dr.)'
                })

            # Fetch without GRN transactions
            wo_grn_trans = without_GRNdtl.objects.filter(
                wo_grn_id__supplier_id=supplier_id,
                wo_grn_id__id_org=org_id,
                wo_grn_id__is_approved=True,
            )

            wo_grn_trans = wo_grn_trans.values('wo_grn_id').annotate(
                wo_grn_total_qty=Sum('wo_grn_qty'),
                wo_grn_total_payment=Sum(
                    ExpressionWrapper(
                        F('wo_grn_qty') * F('unit_price') * (1 - Coalesce(F('dis_percentage'), 0.0) / 100.0),
                        output_field=FloatField()
                    )
                )
            )

            for wo_grn_recd in wo_grn_trans:
                wo_grn_instance = without_GRN.objects.get(wo_grn_id=wo_grn_recd['wo_grn_id'])
                wo_grn_date = wo_grn_instance.transaction_date
                wo_grn_payment = float(wo_grn_recd['wo_grn_total_payment'] or 0)

                # Fetch item-wise details for this wo_grn_id
                item_details = list(wo_grn_trans.filter(wo_grn_id=wo_grn_instance).values(
                    'item_id__item_name', 'wo_grn_qty', 'unit_price', 'dis_percentage', 'item_id__item_uom_id__item_uom_name'
                ))

                # Rename "item_id__item_name" to "item_name"
                for item in item_details:
                    item["item_name"] = item.pop("item_id__item_name")
                    item["item_uom"] = item.pop("item_id__item_uom_id__item_uom_name")

                data.append({
                    'credit_id': wo_grn_instance.wo_grn_no,
                    'item_details': item_details,  # Include item-wise details
                    'debit_opening': '0',
                    'credit_opening': '0',
                    'debit_payment': '0' if wo_grn_instance.is_credit else wo_grn_payment,
                    'credit_payment': wo_grn_payment if wo_grn_instance.is_credit else wo_grn_payment,
                    'credit_pay_date': wo_grn_date,
                    'type_of': 'Without GRN Received (Cr.)' if wo_grn_instance.is_credit else 'Without GRN Received Debited/Credited (Cash)'
                })

            return JsonResponse(data, safe=False)
        else:
            return JsonResponse({'error': 'Invalid request'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# get transaction details report
@login_required()
def getCreditTransactionsAPI(request):
    try:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            supplier_id = request.GET.get('supplier_id')
            org_id = request.GET.get('org_id')
            from_date = request.GET.get('from_date')
            to_date = request.GET.get('to_date')

            if not supplier_id or not supplier_id.isdigit():
                return JsonResponse({'error': 'Invalid supplier_id'}, status=400)
            if not org_id or not org_id.isdigit():
                return JsonResponse({'error': 'Invalid org_id'}, status=400)

            data = []
            supplier_id = int(supplier_id)
            org_id = int(org_id)

            # Convert date strings to actual date objects
            if from_date and to_date:
                try:
                    from_date = datetime.strptime(from_date, "%Y-%m-%d")
                    to_date = datetime.strptime(to_date, "%Y-%m-%d")
                except ValueError:
                    return JsonResponse({'error': 'Invalid date format'}, status=400)

            filters = {'supplier_id': supplier_id, 'org_id': org_id}
            filterspaydtls = {'supplier_id': supplier_id, 'org_id': org_id}
            filtersgrn = {'supplier_id': supplier_id, 'org_id': org_id}
            if from_date and to_date:
                filters['credit_pay_date__range'] = (from_date, to_date)
                filterspaydtls['pay_date__range'] = (from_date, to_date)
                filtersgrn['transaction_date__range'] = (from_date, to_date)

            # Fetch credited transactions
            credited_trans = credit_transactions.objects.filter(**filters, is_credited=True)
            for trans in credited_trans:
                data.append({
                    'credit_id': trans.credit_id,
                    'invoice_no': '',
                    'store_name': '',
                    'debit_opening': '0',
                    'credit_opening': trans.credit_payment,
                    'debit_payment': '0',
                    'credit_payment': '0',
                    'credit_pay_date': trans.credit_pay_date,
                    'type_of': 'Opening Balance (Cr.)',
                    'descrip': '',
                })

            # Fetch debited transactions
            debited_trans = credit_transactions.objects.filter(**filters, is_debited=True)
            for trans in debited_trans:
                data.append({
                    'credit_id': trans.credit_id,
                    'invoice_no': '',
                    'store_name': '',
                    'debit_opening': trans.credit_payment,
                    'credit_opening': '0',
                    'debit_payment': '0',
                    'credit_payment': '0',
                    'credit_pay_date': trans.credit_pay_date,
                    'type_of': 'Opening Balance (Dr.)',
                    'descrip': '',
                })

            # Fetch supplier payment details
            supp_paydtls = paymentsdtls.objects.filter(**filterspaydtls, is_supplier_party=True)
            for paydtls in supp_paydtls:
                data.append({
                    'credit_id': paydtls.pay_id,
                    'invoice_no': '',
                    'store_name': '',
                    'debit_opening': '0',
                    'credit_opening': '0',
                    'debit_payment': paydtls.pay_amount,
                    'credit_payment': '0',
                    'credit_pay_date': paydtls.pay_date,
                    'type_of': 'Supplier Payment Details (Dr.)',
                    'descrip': paydtls.descriptions,
                })

            # Fetch without GRN transactions
            wo_grn_trans = without_GRNdtl.objects.filter(
                wo_grn_id__supplier_id=supplier_id,
                wo_grn_id__id_org=org_id,
                wo_grn_id__is_approved=True,
                wo_grn_id__transaction_date__range=filtersgrn.get('transaction_date__range', None),
            )

            wo_grn_trans = wo_grn_trans.values('wo_grn_id').annotate(
                wo_grn_total_qty=Sum('wo_grn_qty'),
                wo_grn_total_payment=Sum(
                    ExpressionWrapper(
                        F('wo_grn_qty') * F('unit_price') * (1 - Coalesce(F('dis_percentage'), 0.0) / 100.0),
                        output_field=FloatField()
                    )
                )
            )

            for wo_grn_recd in wo_grn_trans:
                wo_grn_instance = without_GRN.objects.get(wo_grn_id=wo_grn_recd['wo_grn_id'])
                wo_grn_date = wo_grn_instance.transaction_date
                store_name = wo_grn_instance.store_id.store_name if wo_grn_instance.store_id else None
                wo_grn_payment = float(wo_grn_recd['wo_grn_total_payment'] or 0)

                # Fetch item-wise details for this wo_grn_id
                item_details = list(wo_grn_trans.filter(wo_grn_id=wo_grn_instance).values(
                    'item_id__item_name', 'wo_grn_qty', 'unit_price', 'dis_percentage', 'item_id__item_uom_id__item_uom_name'
                ))

                # Rename "item_id__item_name" to "item_name"
                for item in item_details:
                    item["item_name"] = item.pop("item_id__item_name")
                    item["item_uom"] = item.pop("item_id__item_uom_id__item_uom_name")

                data.append({
                    'credit_id': wo_grn_instance.wo_grn_no,
                    'invoice_no': wo_grn_instance.invoice_no,
                    'store_name': store_name,
                    'item_details': item_details,  # Include item-wise details
                    'debit_opening': '0',
                    'credit_opening': '0',
                    'debit_payment': '0' if wo_grn_instance.is_credit else wo_grn_payment,
                    'credit_payment': wo_grn_payment if wo_grn_instance.is_credit else wo_grn_payment,
                    'credit_pay_date': wo_grn_date,
                    'type_of': 'Without GRN Received (Cr.)' if wo_grn_instance.is_credit else 'Without GRN Received Debited/Credited (Cash)',
                    'descrip': '',
                })

            data = sorted(data, key=lambda x: x['credit_pay_date'], reverse=False)    

            return JsonResponse(data, safe=False)
        else:
            return JsonResponse({'error': 'Invalid request'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# @login_required()
# def getCreditTransactionsAPI(request):
#     try:
#         if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#             supplier_id = request.GET.get('supplier_id')
#             branch_id = request.GET.get('branch_id')

#             if supplier_id and supplier_id.isdigit():
#                 data = []
                
#                 # Filter credited transactions
#                 credited_trans = credit_transactions.objects.filter(supplier_id=int(supplier_id), is_credited=True)
#                 if branch_id and branch_id.isdigit():
#                     credited_trans = credited_trans.filter(branch_id_id=int(branch_id))
#                 for Ctrans in credited_trans:
#                     data.append({
#                         'credit_id': Ctrans.credit_id,
#                         'debit_payment': '0',
#                         'credit_payment': Ctrans.credit_payment,
#                         'credit_pay_date': Ctrans.credit_pay_date,
#                         'type_of': 'Cash Credited (Asset)'
#                     })

#                 # Filter debited transactions
#                 debited_trans = credit_transactions.objects.filter(supplier_id=int(supplier_id), is_debited=True)
#                 if branch_id and branch_id.isdigit():
#                     debited_trans = debited_trans.filter(branch_id_id=int(branch_id))
#                 for trans in debited_trans:
#                     data.append({
#                         'credit_id': trans.credit_id,
#                         'debit_payment': trans.credit_payment,
#                         'credit_payment': '0',
#                         'credit_pay_date': trans.credit_pay_date,
#                         'type_of': 'Cash Debited (Asset)'
#                     })

#                 ################# invoice wise sales collection, due collection and Refund transactions
#                 # invoice_list table
#                 invice_datas = invoice_list.objects.filter(supplier_id=int(supplier_id))

#                 if branch_id and branch_id.isdigit():
#                     invice_datas = invice_datas.filter(branch_id_id=int(branch_id))
                    
#                 for invoice in invice_datas:
#                     payment_details = payment_list.objects.filter(inv_id=invoice)
#                     sales_details = invoicedtl_list.objects.filter(inv_id=invoice)
#                     # other expense or rent or fare
#                     other_expense = rent_others_exps.objects.filter(inv_id=invoice, is_buyer=True)

#                     # sales details
#                     grand_sale_amt = 0
#                     grand_total_dis = 0
#                     grand_total_gross_dis = 0
#                     grand_vat_tax = 0
#                     grand_cancel_amt = 0
#                     tot_buyer_carryin_cost = 0 

#                     # other expense or rent or fare    
#                     for other_exp in other_expense:
#                         buyer_carryin_cost = other_exp.other_exps_amt
#                         tot_buyer_carryin_cost += buyer_carryin_cost

#                         # data.append({
#                         #     'credit_id': other_exp.other_exps_id,
#                         #     'debit_payment': other_exp.other_exps_amt,
#                         #     'credit_payment': '0',
#                         #     'credit_pay_date': other_exp.other_exps_date,
#                         #     'type_of': 'Other Expense or fare'
#                         # })

#                     for sales in sales_details:
#                         # Calculate sale amount
#                         sale_amt = sales.qty * sales.sales_rate
#                         grand_sale_amt += sale_amt

#                         # Calculate item wise discount
#                         item_w_dis = sales.item_w_dis
#                         grand_total_dis += item_w_dis

#                         # Calculate total gross discount
#                         total_gross_dis = sales.gross_dis
#                         grand_total_gross_dis += total_gross_dis

#                         # Calculate total VAT tax
#                         item_wise_total_vat_tax = sales.gross_vat_tax
#                         grand_vat_tax += item_wise_total_vat_tax

#                         # Calculate total cancel amount
#                         total_item_cancel_amt = sales.sales_rate * sales.is_cancel_qty
#                         grand_cancel_amt += total_item_cancel_amt

#                         # Calculate total net bill for this invoice
#                         total_net_bill = ((grand_sale_amt + grand_vat_tax + tot_buyer_carryin_cost) - (grand_total_dis + grand_total_gross_dis))
#                         total_net_bill = round(total_net_bill, 2)

#                     data.append({
#                         'credit_id': invoice.inv_id,
#                         'debit_payment': total_net_bill,
#                         'credit_payment': '0',
#                         'credit_pay_date': invoice.invoice_date,
#                         'type_of': 'Sales (Asset)'
#                     })

#                     # if grand_cancel_amt > 0:
#                     #     data.append({
#                     #         'credit_id': invoice.inv_id,
#                     #         'debit_payment': grand_cancel_amt,
#                     #         'credit_payment': grand_cancel_amt,
#                     #         'credit_pay_date': invoice.invoice_date,
#                     #         'type_of': 'Sales (Asset) Cancel (debited/credited)'
#                     #     })

#                     for payment in payment_details:
#                         if payment.collection_mode == "1":
#                             data.append({
#                                     'credit_id': payment.inv_id.inv_id,
#                                     'debit_payment': '0',
#                                     'credit_payment': payment.pay_amt,
#                                     'credit_pay_date': payment.pay_date,
#                                     'type_of': 'Sales Collection'
#                                 })

#                         elif payment.collection_mode == "2":
#                             data.append({
#                                     'credit_id': payment.inv_id.inv_id,
#                                     'debit_payment': '0',
#                                     'credit_payment': payment.pay_amt,
#                                     'credit_pay_date': payment.pay_date,
#                                     'type_of': 'Sales Due Collection'
#                                 })
#                         elif payment.collection_mode == "3":
#                             data.append({
#                                     'credit_id': payment.inv_id.inv_id,
#                                     'debit_payment': payment.pay_amt,
#                                     'credit_payment': '0',
#                                     'credit_pay_date': payment.pay_date,
#                                     'type_of': 'Sales Collection Refunded'
#                                 })
#                         # elif payment.collection_mode == "4":
#                         #     data.append({
#                         #             'credit_id': payment.inv_id.inv_id,
#                         #             'debit_payment': '0',
#                         #             'credit_payment': payment.pay_amt,
#                         #             'credit_pay_date': payment.pay_date,
#                         #             'type_of': 'Credit Payment Adjusted'
#                         #         })
                        

#                 # Fetch without GRN transactions
#                 wo_grn_trans = without_GRNdtl.objects.filter(
#                     item_id__in=items.objects.all(),
#                     wo_grn_id__supplier_id=int(supplier_id),
#                     wo_grn_id__is_approved=True
#                 )

#                 if branch_id and branch_id.isdigit():
#                     wo_grn_trans = wo_grn_trans.filter(wo_grn_id__branch_id_id=int(branch_id))

#                 # Group by wo_grn_id, and calculate total quantity and total unit price
#                 wo_grn_trans = wo_grn_trans.values('wo_grn_id').annotate(
#                     wo_grn_total_qty=Sum('wo_grn_qty'),
#                     wo_grn_total_payment=Sum(F('wo_grn_qty') * F('unit_price'))
#                 )

#                 # Separate transactions based on is_credit and is_cash flags
#                 for wo_grn_recd in wo_grn_trans:
#                     wo_grn_instance = without_GRN.objects.get(wo_grn_id=wo_grn_recd['wo_grn_id'])
#                     wo_grn_date = wo_grn_instance.transaction_date
#                     wo_grn_credit_payment = float(wo_grn_recd['wo_grn_total_payment'])

#                     if wo_grn_instance.is_credit:
#                         data.append({
#                             'credit_id': wo_grn_instance.wo_grn_no,
#                             'debit_payment': '0',
#                             'credit_payment': wo_grn_credit_payment,
#                             'credit_pay_date': wo_grn_date,
#                             'type_of': 'Without GRN Received (Credited)'
#                         })
#                     else:
#                         data.append({
#                             'credit_id': wo_grn_instance.wo_grn_no,
#                             'debit_payment': wo_grn_credit_payment,
#                             'credit_payment': '0',
#                             'credit_pay_date': wo_grn_date,
#                             'type_of': 'Without GRN Received Debited (Cash)'
#                         })
#                         data.append({
#                             'credit_id': wo_grn_instance.wo_grn_no,
#                             'debit_payment': '0',
#                             'credit_payment': wo_grn_credit_payment,
#                             'credit_pay_date': wo_grn_date,
#                             'type_of': 'Without GRN Received Credited (Cash)'
#                         })

#                 # Fetch purchase order received transactions
#                 purchase_trans = po_receive_details.objects.filter(
#                     Q(po_id__is_credit=True) | Q(po_id__is_cash=True),  # Filter for both credit and cash transactions
#                     item_id__in=items.objects.all(),
#                     po_id__supplier_id_id=int(supplier_id)
#                 ).select_related('po_id', 'po_id__branch_id')

#                 if branch_id and branch_id.isdigit():
#                     purchase_trans = purchase_trans.filter(po_id__branch_id_id=int(branch_id))

#                 credit_payment_dict = {}
#                 credit_payment_dict_is_cash = {}

#                 for purch_recd in purchase_trans:
#                     order_detail = purchase_orderdtls.objects.filter(
#                         item_id=purch_recd.item_id,
#                         po_id=purch_recd.po_id_id
#                     ).first()

#                     if order_detail:
#                         unit_price = order_detail.unit_price
#                         credit_payment = purch_recd.receive_qty * unit_price
#                         received_date = purch_recd.received_date
#                         credit_id = purch_recd.po_id.po_no

#                         if purch_recd.po_id.is_cash:
#                             credit_payment_dict_is_cash.setdefault(credit_id, 0)
#                             credit_payment_dict_is_cash[credit_id] += credit_payment
#                         else:
#                             credit_payment_dict.setdefault(credit_id, 0)
#                             credit_payment_dict[credit_id] += credit_payment

#                 for credit_id, credit_payment in credit_payment_dict.items():
#                     data.append({
#                         'credit_id': credit_id,
#                         'debit_payment': '0',
#                         'credit_payment': credit_payment,
#                         'credit_pay_date': received_date,
#                         'type_of': 'Purchase Order Received (Credited)'
#                     })

#                 for credit_id, credit_payment_is_cash in credit_payment_dict_is_cash.items():
#                     data.append({
#                         'credit_id': credit_id,
#                         'debit_payment': credit_payment_is_cash,
#                         'credit_payment': '0',
#                         'credit_pay_date': received_date,
#                         'type_of': 'Purchase Order Received Debited (Cash)'
#                     })
#                     data.append({
#                         'credit_id': credit_id,
#                         'debit_payment': '0',
#                         'credit_payment': credit_payment_is_cash,
#                         'credit_pay_date': received_date,
#                         'type_of': 'Purchase Order Received Credited (Cash)'
#                     })

#                 # Fetch purchase order return transactions
#                 purchase_return_trans = po_return_details.objects.filter(
#                     Q(po_id__is_credit=True) | Q(po_id__is_cash=True),  # Filter for both credit and cash transactions
#                     item_id__in=items.objects.all(),
#                     po_id__supplier_id_id=int(supplier_id)
#                 ).select_related('po_id', 'po_id__branch_id')

#                 if branch_id and branch_id.isdigit():
#                     purchase_return_trans = purchase_return_trans.filter(po_id__branch_id_id=int(branch_id))

#                 return_credit_payment_dict = {}
#                 return_credit_payment_dict_is_cash = {}

#                 for purch_return in purchase_return_trans:
#                     return_detail = purchase_orderdtls.objects.filter(
#                         item_id=purch_return.item_id,
#                         po_id=purch_return.po_id_id
#                     ).first()

#                     if return_detail:
#                         return_unit_price = return_detail.unit_price
#                         return_credit_payment = purch_return.return_qty * return_unit_price
#                         returned_date = purch_return.returned_date
#                         return_credit_id = purch_return.po_id.po_no

#                         if purch_return.po_id.is_cash:
#                             return_credit_payment_dict_is_cash.setdefault(return_credit_id, 0)
#                             return_credit_payment_dict_is_cash[return_credit_id] += return_credit_payment
#                         else:
#                             return_credit_payment_dict.setdefault(return_credit_id, 0)
#                             return_credit_payment_dict[return_credit_id] += return_credit_payment
                
#                 for return_credit_id, return_credit_payment in return_credit_payment_dict.items():
#                     data.append({
#                         'credit_id': return_credit_id,
#                         'debit_payment': return_credit_payment,
#                         'credit_payment': '0',
#                         'credit_pay_date': returned_date,
#                         'type_of': 'Purchase Order Returned (Credited)'
#                     })

#                 for return_credit_id, return_credit_payment_is_cash in return_credit_payment_dict_is_cash.items():
#                     data.append({
#                         'credit_id': return_credit_id,
#                         'debit_payment': return_credit_payment_is_cash,
#                         'credit_payment': '0',
#                         'credit_pay_date': returned_date,
#                         'type_of': 'Purchase Order Returned (Cash)'
#                     })

#                 # Fetch purchase order return received transactions
#                 purchase_ret_rec_trans = po_return_received_details.objects.filter(
#                     Q(po_id__is_credit=True) | Q(po_id__is_cash=True),  # Filter for both credit and cash transactions
#                     item_id__in=items.objects.all(),
#                     po_id__supplier_id_id=int(supplier_id)
#                 ).select_related('po_id', 'po_id__branch_id')

#                 if branch_id and branch_id.isdigit():
#                     purchase_ret_rec_trans = purchase_ret_rec_trans.filter(po_id__branch_id_id=int(branch_id))

#                 ret_rec_credit_payment_dict = {}
#                 ret_rec_credit_payment_dict_is_cash = {}

#                 for purch_ret_rec in purchase_ret_rec_trans:
#                     return_rec_detail = purchase_orderdtls.objects.filter(
#                         item_id=purch_ret_rec.item_id,
#                         po_id=purch_ret_rec.po_id_id
#                     ).first()

#                     if return_rec_detail:
#                         ret_rec_unit_price = return_rec_detail.unit_price
#                         ret_rec_credit_payment = purch_ret_rec.ret_rec_qty * ret_rec_unit_price
#                         return_received_date = purch_ret_rec.return_received_date
#                         ret_rec_credit_id = purch_ret_rec.po_id.po_no

#                         if purch_ret_rec.po_id.is_cash:
#                             ret_rec_credit_payment_dict_is_cash.setdefault(ret_rec_credit_id, 0)
#                             ret_rec_credit_payment_dict_is_cash[ret_rec_credit_id] += ret_rec_credit_payment
#                         else:
#                             ret_rec_credit_payment_dict.setdefault(ret_rec_credit_id, 0)
#                             ret_rec_credit_payment_dict[ret_rec_credit_id] += ret_rec_credit_payment
                
#                 for ret_rec_credit_id, ret_rec_credit_payment in ret_rec_credit_payment_dict.items():
#                     data.append({
#                         'credit_id': ret_rec_credit_id,
#                         'debit_payment': '0',
#                         'credit_payment': ret_rec_credit_payment,
#                         'credit_pay_date': return_received_date,
#                         'type_of': 'Purchase Order Return Received (Credited)'
#                     })

#                 for ret_rec_credit_id, ret_rec_credit_payment_is_cash in ret_rec_credit_payment_dict_is_cash.items():
#                     data.append({
#                         'credit_id': ret_rec_credit_id,
#                         'debit_payment': '0',
#                         'credit_payment': ret_rec_credit_payment_is_cash,
#                         'credit_pay_date': return_received_date,
#                         'type_of': 'Purchase Order Return Received (Cash)'
#                     })

#                 return JsonResponse(data, safe=False)
#             else:
#                 return JsonResponse({'error': 'Invalid supplier_id'}, status=400)
#         else:
#             return JsonResponse({'error': 'Invalid request'}, status=400)
#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=500)

@login_required()
def reportCreditManagerAPI(request):
    # Get the supplier_id from the query parameters
    org_id = request.GET.get('org_id')
    branch_id = request.GET.get('branch_id')
    supplier_id = request.GET.get('id')

    if org_id:
        org_data = organizationlst.objects.filter(org_id=org_id).first()
    else:
        # Handle case when no supplier_id is provided
        org_data = None
    
    if branch_id:
        branch_data = branchslist.objects.filter(branch_id=branch_id).first()
    else:
        # Handle case when no supplier_id is provided
        branch_data = None

    # Retrieve the supplier object based on the supplier_id
    if supplier_id:
        supplier = suppliers.objects.filter(supplier_id=supplier_id).first()
    else:
        # Handle case when no supplier_id is provided
        supplier = None
    
    context = {
        'org_data': org_data,
        'branch_data': branch_data,
        'supplier': supplier,
    }
    
    return render(request, 'supplier_opening_balance/credit_report.html', context)



# ===================================== Supplier Client Payments =====================================
@login_required()
def supplierClientPaymentsAPI(request):
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
    
    # Ensure branch_list is always initialized
    branch_list = []

    if user.branch_id is not None:
        # If the user has an associated branch, retrieve only that branch
        branch_list = branchslist.objects.filter(is_active=True, branch_id=user.branch_id)
    
    context = {
        'org_list': org_list,
        'branch_list': branch_list,
    }

    return render(request, 'supplier_client_payment/supplier_client_payment.html', context)


# get supplier payment dtls
@login_required()
def getSupplierPaymentDtlsDataAPI(request):
    
    if request.method == "GET":
        # Get the organization and registration IDs from the query parameters
        org_id = request.GET.get('org_id')
        supplier_id = request.GET.get('supplier_id')
        start_date_filter = request.GET.get('start_date', '').strip()
        end_date_filter = request.GET.get('end_date', '').strip()

        # Filter the opening balances based on org_id and supplier_id
        paymentDtls = paymentsdtls.objects.filter(is_supplier_party=True).all()

        if org_id:
            paymentDtls = paymentDtls.filter(org_id=org_id)

        if supplier_id:
            paymentDtls = paymentDtls.filter(supplier_id=supplier_id)

        # Apply date range filter if both start and end dates are provided
        if start_date_filter and end_date_filter:
            try:
                start_date = datetime.strptime(start_date_filter, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_filter, '%Y-%m-%d').date()
                paymentDtls = paymentDtls.filter(pay_date__range=[start_date, end_date])
            except ValueError:
                return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)

        elif start_date_filter:
            try:
                start_date = datetime.strptime(start_date_filter, '%Y-%m-%d').date()
                paymentDtls = paymentDtls.filter(pay_date__gte=start_date)
            except ValueError:
                return JsonResponse({'error': 'Invalid start_date format. Use YYYY-MM-DD'}, status=400)

        elif end_date_filter:
            try:
                end_date = datetime.strptime(end_date_filter, '%Y-%m-%d').date()
                paymentDtls = paymentDtls.filter(pay_date__lte=end_date)
            except ValueError:
                return JsonResponse({'error': 'Invalid end_date format. Use YYYY-MM-DD'}, status=400)

        # Retrieve the values to return
        paymentDtls = paymentDtls.annotate(
            creator_name=F('ss_creator__username')
        ).values(
            'pay_id',
            'pay_date',
            'card_info',
            'pay_mob_number',
            'pay_reference',
            'bank_name',
            'comments',
            'descriptions',
            'creator_name',
            'pay_amount'
        )

        data = list(paymentDtls)  # Convert queryset to a list of dictionaries
        return JsonResponse(data, safe=False)
    

# save Supplier payment data
@login_required()
def saveSupplierPaymentTransactionAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST
    org_id=data.get('filter_org')
    branch_id=data.get('branch_id')
    supplier_id=data.get('supplier_id')
    pay_amount = float(data.get('pay_amount', 0.0))
    descriptions = data.get('descriptions')
    pay_mode = int(data.get('pay_mode', 0))
    pay_type = data.get('pay_type')
    comments = data.get('comments')
    card_info = data.get('card_info')
    pay_mob_number = data.get('pay_mob_number')
    pay_reference = data.get('pay_reference')
    bank_name = data.get('bank_name')

    try:
        org_instance = organizationlst.objects.get(org_id=org_id)
    except organizationlst.DoesNotExist:
        resp['errmsg'] = 'Organization not found'
        return JsonResponse(resp)
    
    try:
        branch_instance = branchslist.objects.get(branch_id=branch_id)
    except branchslist.DoesNotExist:
        resp['errmsg'] = 'Branch not found'
        return JsonResponse(resp)

    try:
        supp_instance = suppliers.objects.get(supplier_id=supplier_id)
    except suppliers.DoesNotExist:
        resp['errmsg'] = 'Registration not found'
        return JsonResponse(resp)

    pay_trans = paymentsdtls(
        org_id=org_instance,
        branch_id=branch_instance,
        supplier_id=supp_instance,
        is_reg_client=False,
        is_supplier_party=True,
        pay_amount=pay_amount,
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
    pay_trans.save()

    if pay_mode == 1 and pay_amount > 0:
        cashOnHands, created = cash_on_hands.objects.get_or_create(
            org_id=org_instance,
            branch_id=branch_instance,
            defaults={'on_hand_cash': 0}
        )
        # Update the on_hand_cash by adding the total payment value using F() expression
        cashOnHands.on_hand_cash = F('on_hand_cash') - pay_amount
        cashOnHands.save()  # This will save the update in the database

        # Refresh from the database to get the updated value
        cashOnHands.refresh_from_db()

    resp = {'success': True, 'msg': 'Saved successfully'}

    return JsonResponse(resp)