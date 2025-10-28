from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.db.models import Q, F, Sum
from collections import defaultdict
from django.db.models import FloatField
from decimal import Decimal
from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from item_pos.models import carrying_cost_payments, invoice_list, invoicedtl_list, payment_list, rent_others_exps, without_invoice_collection
from organizations.models import branchslist, organizationlst
from bank_statement.models import cash_on_hands, daily_bank_statement
from local_purchase.models import local_purchase, local_purchasedtl
from local_purchase_return.models import lp_return_details
from manual_return_receive.models import manual_return_receive, manual_return_receivedtl
from clients_transection.models import paymentsdtls
from user_setup.models import access_list
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def collectionsReportManagerAPI(request):
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

    billingBtn_access = access_list.objects.filter(
        user_id=user,
        feature_id__feature_page_link='BILLINGFORMACCESSBTN',
        is_active=True
    ).exists()
    
    context = {
        'org_list': org_list,
        'billingBtn_access': billingBtn_access
    }

    return render(request, 'sales_coll_report/collection_report.html', context)

@login_required()
def collectionsDetailsReportManagerAPI(request):
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

    return render(request, 'sales_coll_report/coll_dtls_report.html', context)


@login_required()
def collectionsReportAPI(request):
    
    start_from = None
    end_from = None

    # Define context here
    combined_data = []

    grand_total_net_collection = 0
    total_collection = 0
    total_due_collection = 0
    total_grand_collection = 0
    total_refund_collection = 0
    total_adjust_collection = 0
    grandtotal_sales = 0
    grand_total_discount = 0
    grand_total_vat_tax = 0
    grand_total_cancel_amt = 0
    grand_total_net_bill = 0
    total_other_exp_amt = 0
    grand_total_collection = 0
    grandtotal_cost = 0
    total_daily_deposit = 0
    deposit_main_branch = 0
    dep_rec_sub_branch = 0
    total_cash_on_hand = 0
    grand_mobile_bank_coll = 0
    grand_total_bank_coll = 0
    grand_total_amt = 0
    grand_ret_total_amt = 0
    grand_mrr_total_amt = 0
    grand_carrying_pay_amt = 0
    grand_bkash_coll_amt = 0
    grand_nagad_coll_amt = 0
    grand_upay_coll_amt = 0
    grand_ucash_coll_amt = 0
    mobile_bank_coll = 0
    net_mobile_bank_coll = 0
    grand_bkash_ref_amt = 0
    grand_nagad_ref_amt = 0
    grand_upay_ref_amt = 0
    grand_ucash_ref_amt = 0
    total_mobile_bank_refund = 0
    grand_mobile_bank = 0
    grand_cheque_coll_amt = 0
    grand_debit_card_coll_amt = 0
    grand_credit_card_coll_amt = 0
    grand_bank_deposit_coll_amt = 0
    total_bank_coll_amt = 0
    net_bank_coll_amt = 0
    grand_cheque_ref_amt = 0
    grand_debit_card_ref_amt = 0
    grand_credit_card_ref_amt = 0
    grand_bank_deposit_ref_amt = 0
    total_bank_refund_amt = 0
    grand_total_bank_coll = 0
    grand_woinvcoll_amt = 0
    grand_woinvcoll_mb_amt = 0
    grand_woinvcoll_b_amt = 0
    grand_regclipay_amt = 0
    grand_regclipay_mb_amt = 0
    grand_regclipay_b_amt = 0
    grand_suppclipay_amt = 0
    grand_suppclipay_mb_amt = 0
    grand_suppclipay_b_amt = 0
    net_collection_cash = 0
    net_sub_total_coll_cash = 0
    total_remaining_collection = 0

    if request.method == "POST":
        try:
            start_from = request.POST.get('start_from')
            end_from = request.POST.get('end_from')
            org_id = request.POST.get('org_id')
            branch_id = request.POST.get('branch_id')

            # Parse the dates from the request POST data
            start_from = datetime.strptime(start_from, '%Y-%m-%d').date()
            end_from = datetime.strptime(end_from, '%Y-%m-%d').date()

            # Query data from your models
            payments = payment_list.objects.filter(pay_date__range=(start_from, end_from), inv_id__org_id=org_id, inv_id__branch_id=branch_id).all()
            # is_carrying_cost=False
            other_rent_exp = rent_others_exps.objects.filter(other_exps_date__range=(start_from, end_from), org_id=org_id, branch_id=branch_id, is_carrying_cost=False).all()
            carrying_cost_buyer = rent_others_exps.objects.filter(is_buyer=True, org_id=org_id, branch_id=branch_id, is_carrying_cost=True).all()
            invoice_details = invoicedtl_list.objects.filter(inv_id__org_id=org_id, inv_id__branch_id=branch_id).all()
            bank_deposits = daily_bank_statement.objects.filter(deposit_date__range=(start_from, end_from), is_bank_statement=True, org_id=org_id, branch_id=branch_id).all()
            daily_cash_on_hand = cash_on_hands.objects.filter(org_id=org_id, branch_id=branch_id)
            local_purchases = local_purchase.objects.filter(transaction_date__range=(start_from, end_from), is_approved=True, is_cash=True, id_org=org_id, branch_id=branch_id)
            local_purchasedtls = local_purchasedtl.objects.filter(lp_rec_date__range=(start_from, end_from)).select_related('lp_id').all()
            lp_returndtls = lp_return_details.objects.filter(returned_date__range=(start_from, end_from)).select_related('lp_id').all()
            manual_return_rec = manual_return_receive.objects.filter(transaction_date__range=(start_from, end_from), is_approved=True, is_cash=True, id_org=org_id, branch_id=branch_id)
            manu_return_recdtls = manual_return_receivedtl.objects.filter(manu_ret_rec_date__range=(start_from, end_from)).select_related('manu_ret_rec_id').all()
            submit_main_branch = daily_bank_statement.objects.filter(deposit_date__range=(start_from, end_from), is_branch_deposit=True, org_id=org_id, branch_id=branch_id).all()
            deposit_rec_sub_branch = daily_bank_statement.objects.filter(deposit_date__range=(start_from, end_from), is_branch_deposit_receive=True, org_id=org_id, branch_id=branch_id).all()
            carrying_cost_payment = carrying_cost_payments.objects.filter(c_cost_date__range=(start_from, end_from), org_id=org_id, branch_id=branch_id).all()
            without_inv_coll = without_invoice_collection.objects.filter(coll_date__range=(start_from, end_from), org_id=org_id, branch_id=branch_id).all()
            # registration client
            reg_client_payment = paymentsdtls.objects.filter(pay_date__range=(start_from, end_from), org_id=org_id, branch_id=branch_id, is_reg_client=True).all()
            # supplier client
            supplier_client_payment = paymentsdtls.objects.filter(pay_date__range=(start_from, end_from), org_id=org_id, branch_id=branch_id, is_supplier_party=True).all()
            # Fetch the organization and branch details
            organization = organizationlst.objects.filter(org_id=org_id).first()
            branch = branchslist.objects.filter(branch_id=branch_id).first()

            # carrying cost payments
            for carrying_pay in carrying_cost_payment:
                carrying_pay_amt = carrying_pay.c_cost_amt
                grand_carrying_pay_amt += carrying_pay_amt
                grand_carrying_pay_amt = round(grand_carrying_pay_amt, 2)
            
            # without invoice collection amt
            for woinvcoll in without_inv_coll:
                woinvcoll_paymode = str(woinvcoll.collection_mode)  # Ensure string comparison
                woinvcoll_amt = woinvcoll.collection_amt or 0  # Handle None values

                if woinvcoll_paymode == '1':  # String comparison
                    grand_woinvcoll_amt += woinvcoll_amt
                    grand_woinvcoll_amt = round(grand_woinvcoll_amt, 2)

                elif woinvcoll_paymode in ['5', '6', '7', '8']:  # String comparison
                    grand_woinvcoll_mb_amt += woinvcoll_amt
                    grand_woinvcoll_mb_amt = round(grand_woinvcoll_mb_amt, 2)

                elif woinvcoll_paymode in ['2', '3', '4', '9']:  # String comparison
                    grand_woinvcoll_b_amt += woinvcoll_amt
                    grand_woinvcoll_b_amt = round(grand_woinvcoll_b_amt, 2)
            
            # registration client payment amt
            for regclipay in reg_client_payment:
                regclipay_paymode = str(regclipay.pay_mode)  # Ensure string comparison
                regclipay_amt = regclipay.pay_amount or 0  # Handle None values

                if regclipay_paymode == '1':  # String comparison
                    grand_regclipay_amt += regclipay_amt
                    grand_regclipay_amt = round(grand_regclipay_amt, 2)

                elif regclipay_paymode in ['5', '6', '7', '8']:  # String comparison
                    grand_regclipay_mb_amt += regclipay_amt
                    grand_regclipay_mb_amt = round(grand_regclipay_mb_amt, 2)

                elif regclipay_paymode in ['2', '3', '4', '9']:  # String comparison
                    grand_regclipay_b_amt += regclipay_amt
                    grand_regclipay_b_amt = round(grand_regclipay_b_amt, 2)
            
            # Supplier client payment amt
            for suppclipay in supplier_client_payment:
                suppclipay_paymode = str(suppclipay.pay_mode)  # Ensure string comparison
                suppclipay_amt = suppclipay.pay_amount or 0  # Handle None values

                if suppclipay_paymode == '1':  # String comparison
                    grand_suppclipay_amt += suppclipay_amt
                    grand_suppclipay_amt = round(grand_suppclipay_amt, 2)

                elif suppclipay_paymode in ['5', '6', '7', '8']:  # String comparison
                    grand_suppclipay_mb_amt += suppclipay_amt
                    grand_suppclipay_mb_amt = round(grand_suppclipay_mb_amt, 2)

                elif suppclipay_paymode in ['2', '3', '4', '9']:  # String comparison
                    grand_suppclipay_b_amt += suppclipay_amt
                    grand_suppclipay_b_amt = round(grand_suppclipay_b_amt, 2)

            # manual return receive 
            for mret_rec in manual_return_rec:
                # Filter manu return recdtls
                manu_ret_rec_details = manu_return_recdtls.filter(manu_ret_rec_id=mret_rec)

                for manurrdtl in manu_ret_rec_details:
                    # Extract relevant attributes
                    mrr_qty = manurrdtl.manu_ret_rec_qty or 0  # Default to 0 if None
                    mrr_price = manurrdtl.unit_price or 0
                    mrr_discount = manurrdtl.dis_percentage or 0

                    # Calculate total amount, discount, and final amount
                    mrr_totalamt = mrr_qty * mrr_price
                    total_mrr_dis_per = mrr_discount / 100
                    total_mrr_dis_amt = mrr_totalamt * total_mrr_dis_per

                    # Accumulate the final amount
                    grand_mrr_total_amt += mrr_totalamt - total_mrr_dis_amt

            for lpdata in local_purchases:
                # Filter purchase details and return details by local purchase ID
                lp_details = local_purchasedtls.filter(lp_id=lpdata)
                lp_return_dtls = lp_returndtls.filter(lp_id=lpdata)

                for detail in lp_details:
                    # Extract relevant attributes
                    lp_qty = detail.lp_rec_qty or 0  # Default to 0 if None
                    lp_price = detail.unit_price or 0
                    lp_discount = detail.dis_percentage or 0

                    # Calculate total amount, discount, and final amount
                    lp_totalamt = lp_qty * lp_price
                    total_lp_dis_per = lp_discount / 100
                    total_dis_amt = lp_totalamt * total_lp_dis_per

                    # Accumulate the final amount
                    grand_total_amt += lp_totalamt - total_dis_amt

                for returndtls in lp_return_dtls:
                    # Fetch the relevant `local_purchasedtl` record for the returned item
                    related_detail = local_purchasedtl.objects.filter(lp_id=returndtls.lp_id, item_id=returndtls.item_id).first()

                    if related_detail:
                        # Extract attributes from the related detail instance
                        lp_ret_qty = returndtls.lp_return_qty or 0
                        lp_ret_can_qty = returndtls.is_cancel_qty or 0
                        lp_ret_price = related_detail.unit_price or 0
                        lp_ret_discount = related_detail.dis_percentage or 0

                        # Calculate total amount, discount, and final amount for return
                        lp_ret_totalamt = (lp_ret_qty - lp_ret_can_qty) * lp_ret_price
                        total_lpret_dis_per = lp_ret_discount / 100
                        total_ret_dis_amt = lp_ret_totalamt * total_lpret_dis_per

                        # Accumulate the return amount
                        grand_ret_total_amt += lp_ret_totalamt - total_ret_dis_amt

            # Sum the diposit rec from sub branch over the date range
            dep_rec_sub_branch = deposit_rec_sub_branch.aggregate(
                total_amount=Sum('deposits_amt')
            )['total_amount'] or 0  # Return 0 if no deposits are found

            # Sum the diposit of the main branch over the date range
            deposit_main_branch = submit_main_branch.aggregate(
                total_amount=Sum('deposits_amt')
            )['total_amount'] or 0  # Return 0 if no deposits are found

            # Sum the deposits_amt over the date range
            total_daily_deposit = bank_deposits.aggregate(
                total_amount=Sum('deposits_amt')
            )['total_amount'] or 0  # Return 0 if no deposits are found

            # Calculate total cash on hand
            total_cash_on_hand = round(sum(float(hands.on_hand_cash or 0) for hands in daily_cash_on_hand), 2)

            # Calculate carrying cost from buyer per inv_id
            buyer_total_cost = carrying_cost_buyer.filter(inv_id__in=payments.values_list('inv_id')).values('inv_id').annotate(
                total_cost=Sum(F('other_exps_amt'), output_field=FloatField())
            )

            # Initialize empty dictionary to group inv_details by inv_id
            inv_details = {}

            # Check if invoice_details exist
            if invoice_details.exists():
                
                for invItem in invoice_details.filter(inv_id__in=payments.values_list('inv_id', flat=True)):
                    inv_id = invItem.inv_id.inv_id

                    # Initialize list for each inv_id if not already present
                    if inv_id not in inv_details:
                        inv_details[inv_id] = []

                    # Append item details to the list under each inv_id
                    inv_details[inv_id].append({
                        'item_id': invItem.item_id.item_id,
                        'item_name': invItem.item_id.item_name,
                        'sales_rate': invItem.sales_rate,
                        'qty': invItem.qty,
                        'uom': invItem.item_id.item_uom_id.item_uom_name,
                    })

                # Calculate total sales per inv_id
                sales_totals = invoice_details.filter(inv_id__in=payments.values_list('inv_id')).values('inv_id').annotate(
                    total_sales=Sum(F('sales_rate') * F('qty'), output_field=FloatField())
                )

                item_w_discount = invoice_details.filter(inv_id__in=payments.values_list('inv_id')).values('inv_id').annotate(
                    item_disc=Sum(((F('item_w_dis') / F('qty')) * ((F('qty') - F('is_cancel_qty')))), output_field=FloatField())
                )

                gross_discount = invoice_details.filter(inv_id__in=payments.values_list('inv_id')).values('inv_id').annotate(
                    gross_disc=Sum(((F('gross_dis') / F('qty')) * ((F('qty') - F('is_cancel_qty')))), output_field=FloatField())
                )

                item_w_gross_vat_tax = invoice_details.filter(inv_id__in=payments.values_list('inv_id')).values('inv_id').annotate(
                    total_vat_tax=Sum(((F('gross_vat_tax') / F('qty')) * ((F('qty') - F('is_cancel_qty')))), output_field=FloatField())
                )

                cancel_amt = invoice_details.filter(inv_id__in=payments.values_list('inv_id')).values('inv_id').annotate(
                    total_cancel_amt=Sum((F('sales_rate') * F('is_cancel_qty')), output_field=FloatField())
                )
            else:
                # Set all totals to 0.0 if no invoice details are found
                sales_totals = [{'total_sales': 0}]
                item_w_discount = [{'item_disc': 0}]
                gross_discount = [{'gross_disc': 0}]
                item_w_gross_vat_tax = [{'total_vat_tax': 0}]
                cancel_amt = [{'total_cancel_amt': 0}]

            # Create a dictionary to store collections for each inv_id
            collections_by_inv_id = defaultdict(lambda: {
                'total_collection_amt': 0.0,
                'total_due_collection_amt': 0.0,
                'total_refund_collection_amt': 0.0,
                'total_adjust_amt': 0.0,
                'total_sales': 0.0,
                'total_cost': 0.0,
                'item_disc': 0.0,
                'gross_disc': 0.0,
                'total_vat_tax': 0.0,
                'total_cancel_amt': 0.0,
                'total_net_bill': 0.0,
                'total_bkash_coll_amt': 0.0,
                'total_nagad_coll_amt': 0.0,
                'total_upay_coll_amt': 0.0,
                'total_ucash_coll_amt': 0.0,
                'total_bkash_refund_amt': 0.0,
                'total_nagad_refund_amt': 0.0,
                'total_upay_refund_amt': 0.0,
                'total_ucash_refund_amt': 0.0,
                'total_check_coll_amt': 0.0,
                'total_debit_coll_amt': 0.0,
                'total_credit_coll_amt': 0.0,
                'bank_deposit_coll_amt': 0.0,
                'total_check_refund_amt': 0.0,
                'total_debit_refund_amt': 0.0,
                'total_credit_refund_amt': 0.0,
                'bank_deposit_refund_amt': 0.0,
                'bkash_coll_amt': 0.0,
                'nagad_coll_amt': 0.0,
                'upay_coll_amt': 0.0,
                'ucash_coll_amt': 0.0,
                'bkash_ref_amt': 0.0,
                'nagad_ref_amt': 0.0,
                'upay_ref_amt': 0.0,
                'ucash_ref_amt': 0.0,
                'cheque_coll_amt': 0.0,
                'debit_card_coll_amt': 0.0,
                'credit_card_coll_amt': 0.0,
                'bank_deposit_coll_amt': 0.0,
                'cheque_ref_amt': 0.0,
                'debit_card_ref_amt': 0.0,
                'credit_card_ref_amt': 0.0,
                'bank_deposit_ref_amt': 0.0,
                'total_collection_amt_cash': 0.0,
                'total_due_collection_amt_cash': 0.0,
                'total_refund_collection_amt_cash': 0.0,
                'coll_pay_modes': [],
                'ref_pay_modes': [],
            })

            # other rent or expence
            for otherExp in other_rent_exp:
                other_exp_amt = otherExp.other_exps_amt
                total_other_exp_amt += other_exp_amt

            # Define a Mobile Banking mapping of pay_mode to collection keys
            pay_mode_mobile_bank_key = {
                "5": 'total_bkash_coll_amt',
                "6": 'total_nagad_coll_amt',
                "7": 'total_upay_coll_amt',
                "8": 'total_ucash_coll_amt',
            }

            pay_mode_mobile_bank_key_refund = {
                "5": 'total_bkash_refund_amt',
                "6": 'total_nagad_refund_amt',
                "7": 'total_upay_refund_amt',
                "8": 'total_ucash_refund_amt',
            }

            # Define a Bank mapping of pay_mode to collection keys
            pay_mode_bank_key = {
                "2": 'total_check_coll_amt',
                "3": 'total_debit_coll_amt',
                "4": 'total_credit_coll_amt',
                "9": 'bank_deposit_coll_amt',
            }

            pay_mode_bank_key_refund = {
                "2": 'total_check_refund_amt',
                "3": 'total_debit_refund_amt',
                "4": 'total_credit_refund_amt',
                "9": 'bank_deposit_refund_amt',
            }

            for paymentData in payments:
                # Ensure pay_mode is a string for safe comparison
                pay_mode = str(paymentData.pay_mode).strip()

                # Ensure collection_mode is a string
                collection_mode = str(paymentData.collection_mode).strip()

                inv_id = paymentData.inv_id

                # Convert pay_amt to a float
                pay_amt = float(paymentData.pay_amt or 0.0)

                # pay_modes gets
                if paymentData.collection_mode in ('1','2'):
                    collections_by_inv_id[inv_id]['coll_pay_modes'].append(pay_mode)
                elif paymentData.collection_mode == "3":
                    collections_by_inv_id[inv_id]['ref_pay_modes'].append(pay_mode)
                
                # collection
                if collection_mode == "1":
                    collections_by_inv_id[inv_id]['total_collection_amt'] += pay_amt
                # due collection
                elif collection_mode == "2":
                    collections_by_inv_id[inv_id]['total_due_collection_amt'] += pay_amt

                # Refund
                elif collection_mode == "3":
                    collections_by_inv_id[inv_id]['total_refund_collection_amt'] += pay_amt
                
                # Adjust collection
                elif collection_mode == "4":
                    collections_by_inv_id[inv_id]['total_adjust_amt'] += pay_amt

                # ================= paymode "1" wise cash pay amt =================
                # cash collection
                if collection_mode == "1" and pay_mode == "1":
                    collections_by_inv_id[inv_id]['total_collection_amt_cash'] += pay_amt
                # cash due collection
                elif collection_mode == "2" and pay_mode == "1":
                    collections_by_inv_id[inv_id]['total_due_collection_amt_cash'] += pay_amt

                # cash Refund
                elif collection_mode == "3" and pay_mode == "1":
                    collections_by_inv_id[inv_id]['total_refund_collection_amt_cash'] += pay_amt
                # ================= paymode "1" wise cash pay amt =================

                # =========================== mobile bank wise collections =====================
                # mobile bank wise collections
                mobile_bank_key = pay_mode_mobile_bank_key.get(pay_mode)
                if mobile_bank_key:
                    if collection_mode in ('1','2'):
                        collections_by_inv_id[inv_id][mobile_bank_key] += pay_amt

                # =========================== mobile bank wise collections Refund=====================
                # mobile bank wise collections Refund
                mobile_bank_key_refund = pay_mode_mobile_bank_key_refund.get(pay_mode)
                if mobile_bank_key_refund:
                    if collection_mode == "3":
                        collections_by_inv_id[inv_id][mobile_bank_key_refund] += pay_amt


                # =========================== bank wise collections =====================
                # bank wise collections
                bank_key = pay_mode_bank_key.get(pay_mode)
                if bank_key:
                    if collection_mode in ('1','2'):
                        collections_by_inv_id[inv_id][bank_key] += pay_amt

                # =========================== bank wise collections Refund =====================
                # bank wise collections Refund
                bank_key_refund = pay_mode_bank_key_refund.get(pay_mode)
                if bank_key_refund:
                    if collection_mode == "3":
                        collections_by_inv_id[inv_id][bank_key_refund] += pay_amt

            for inv_id, collections in collections_by_inv_id.items():
                # Get total sales for this inv_id from the annotated values
                try:
                    sales_total_entry = sales_totals.get(inv_id=inv_id)
                    total_sales = sales_total_entry['total_sales'] if sales_total_entry else 0
                    collections['total_sales'] = total_sales
                    grandtotal_sales += total_sales
                except ObjectDoesNotExist:
                    total_sales = 0
                    collections['total_sales'] = total_sales
                    grandtotal_sales += total_sales

                try:
                    cost_entry = buyer_total_cost.get(inv_id=inv_id)
                    total_cost = cost_entry['total_cost'] if cost_entry else 0
                    collections['total_cost'] = total_cost
                    grandtotal_cost += total_cost
                except ObjectDoesNotExist:
                    total_cost = 0
                    collections['total_cost'] = total_cost
                    grandtotal_cost += total_cost
                
                # item wise discount
                try:
                    item_disc = item_w_discount.get(inv_id=inv_id)['item_disc'] if item_w_discount else 0
                    collections['item_disc'] = item_disc
                    item_disc = round(item_disc, 2)
                except ObjectDoesNotExist:
                    item_disc = 0
                    collections['item_disc'] = item_disc
                    item_disc = round(item_disc, 2)

                # gross discount
                try:
                    gross_disc = gross_discount.get(inv_id=inv_id)['gross_disc'] if gross_discount else 0
                    collections['gross_disc'] = gross_disc
                    gross_disc = round(gross_disc, 2)
                except ObjectDoesNotExist:
                    gross_disc = 0
                    collections['gross_disc'] = gross_disc
                    gross_disc = round(gross_disc, 2)

                # total discount
                total_discount = collections['item_disc'] + collections['gross_disc']
                total_discount = round(total_discount, 2)
                # total discount sun
                grand_total_discount += total_discount
                grand_total_discount = round(grand_total_discount, 2)

                # total vat tax
                try:
                    total_vat_tax = item_w_gross_vat_tax.get(inv_id=inv_id)['total_vat_tax'] if item_w_gross_vat_tax else 0
                    collections['total_vat_tax'] = total_vat_tax
                    total_vat_tax = round(total_vat_tax, 2)
                    # grand total vat tax
                    grand_total_vat_tax += total_vat_tax
                    grand_total_vat_tax = round(grand_total_vat_tax, 2)
                except ObjectDoesNotExist:
                    total_vat_tax = 0
                    collections['total_vat_tax'] = total_vat_tax
                    total_vat_tax = round(total_vat_tax, 2)
                    # grand total vat tax
                    grand_total_vat_tax += total_vat_tax
                    grand_total_vat_tax = round(grand_total_vat_tax, 2)

                # total cancel amount
                try:
                    total_cancel_amt = cancel_amt.get(inv_id=inv_id)['total_cancel_amt'] if cancel_amt else 0
                    collections['total_cancel_amt'] = total_cancel_amt
                    total_cancel_amt = round(total_cancel_amt, 2)
                    # grand total cancel amount
                    grand_total_cancel_amt += total_cancel_amt
                    grand_total_cancel_amt = round(grand_total_cancel_amt, 2)
                except ObjectDoesNotExist:
                    total_cancel_amt = 0
                    collections['total_cancel_amt'] = total_cancel_amt
                    total_cancel_amt = round(total_cancel_amt, 2)
                    # grand total cancel amount
                    grand_total_cancel_amt += total_cancel_amt
                    grand_total_cancel_amt = round(grand_total_cancel_amt, 2)

                # total net bill
                total_net_bill = ((collections['total_sales'] + collections['total_vat_tax'] + collections['total_cost']) - (collections['item_disc'] + collections['gross_disc']) - collections['total_cancel_amt'])
                total_net_bill = round(total_net_bill, 2)
                # grand total_net_bill
                grand_total_net_bill += total_net_bill
                grand_total_net_bill = round(grand_total_net_bill, 2)

                ################# mobile bank collection #######################
                # bkash coll amt
                bkash_coll_amt = collections['total_bkash_coll_amt']
                grand_bkash_coll_amt += bkash_coll_amt
                grand_bkash_coll_amt = round(grand_bkash_coll_amt, 2)
                # nagad coll amt
                nagad_coll_amt = collections['total_nagad_coll_amt']
                grand_nagad_coll_amt += nagad_coll_amt
                grand_nagad_coll_amt = round(grand_nagad_coll_amt, 2)
                # upay coll amt
                upay_coll_amt = collections['total_upay_coll_amt']
                grand_upay_coll_amt += upay_coll_amt
                grand_upay_coll_amt = round(grand_upay_coll_amt, 2)
                # ucash coll amt
                ucash_coll_amt = collections['total_ucash_coll_amt']
                grand_ucash_coll_amt += ucash_coll_amt
                grand_ucash_coll_amt = round(grand_ucash_coll_amt, 2)

                ################# mobile bank Refund #######################
                # bkash Refund amt
                bkash_ref_amt = collections['total_bkash_refund_amt']
                grand_bkash_ref_amt += bkash_ref_amt
                grand_bkash_ref_amt = round(grand_bkash_ref_amt, 2)
                # nagad Refund amt
                nagad_ref_amt = collections['total_nagad_refund_amt']
                grand_nagad_ref_amt += nagad_ref_amt
                grand_nagad_ref_amt = round(grand_nagad_ref_amt, 2)
                # upay Refund amt
                upay_ref_amt = collections['total_upay_refund_amt']
                grand_upay_ref_amt += upay_ref_amt
                grand_upay_ref_amt = round(grand_upay_ref_amt, 2)
                # ucash Refund amt
                ucash_ref_amt = collections['total_ucash_refund_amt']
                grand_ucash_ref_amt += ucash_ref_amt
                grand_ucash_ref_amt = round(grand_ucash_ref_amt, 2)

                ################# bank collection #######################
                # Cheque coll amt
                cheque_coll_amt = collections['total_check_coll_amt']
                grand_cheque_coll_amt += cheque_coll_amt
                grand_cheque_coll_amt = round(grand_cheque_coll_amt, 2)
                # Debit Card coll amt
                debit_card_coll_amt = collections['total_debit_coll_amt']
                grand_debit_card_coll_amt += debit_card_coll_amt
                grand_debit_card_coll_amt = round(grand_debit_card_coll_amt, 2)
                # Credit Card coll amt
                credit_card_coll_amt = collections['total_credit_coll_amt']
                grand_credit_card_coll_amt += credit_card_coll_amt
                grand_credit_card_coll_amt = round(grand_credit_card_coll_amt, 2)
                # Bank Deposit coll amt
                bank_deposit_coll_amt = collections['bank_deposit_coll_amt']
                grand_bank_deposit_coll_amt += bank_deposit_coll_amt
                grand_bank_deposit_coll_amt = round(grand_bank_deposit_coll_amt, 2)

                ################# bank Refund #######################
                # Cheque Refund amt
                cheque_ref_amt = collections['total_check_refund_amt']
                grand_cheque_ref_amt += cheque_ref_amt
                grand_cheque_ref_amt = round(grand_cheque_ref_amt, 2)
                # Debit Card Refund amt
                debit_card_ref_amt = collections['total_debit_refund_amt']
                grand_debit_card_ref_amt += debit_card_ref_amt
                grand_debit_card_ref_amt = round(grand_debit_card_ref_amt, 2)
                # Credit Card Refund amt
                credit_card_ref_amt = collections['total_credit_refund_amt']
                grand_credit_card_ref_amt += credit_card_ref_amt
                grand_credit_card_ref_amt = round(grand_credit_card_ref_amt, 2)
                # Bank Deposit Refund amt
                bank_deposit_ref_amt = collections['bank_deposit_refund_amt']
                grand_bank_deposit_ref_amt += bank_deposit_ref_amt
                grand_bank_deposit_ref_amt = round(grand_bank_deposit_ref_amt, 2)

                ########################################
                grand_collection = collections['total_collection_amt'] + collections['total_due_collection_amt']
                grand_collection = round(grand_collection, 2)
                # total net collection
                total_net_collection = ((collections['total_collection_amt'] + collections['total_due_collection_amt']) - (collections['total_refund_collection_amt']))
                total_net_collection = round(total_net_collection, 2)

                # total collection amt
                collection = collections['total_collection_amt']
                collection = round(collection, 2)
                total_collection += collection
                total_collection = round(total_collection, 2)

                # total due collection amt
                due_collection = collections['total_due_collection_amt']
                due_collection = round(due_collection, 2)
                total_due_collection += due_collection
                total_due_collection = round(total_due_collection, 2)

                # total collection amt + total due collection amt
                total_grand_collection += grand_collection
                total_grand_collection = round(total_grand_collection, 2)

                # total refund collection
                refund_collection = collections['total_refund_collection_amt']
                refund_collection = round(refund_collection, 2)
                total_refund_collection += refund_collection
                total_refund_collection = round(total_refund_collection, 2)


                # total Adjust collection
                adjust_collection = collections['total_adjust_amt']
                adjust_collection = round(adjust_collection, 2)
                total_adjust_collection += adjust_collection
                total_adjust_collection = round(total_adjust_collection, 2)

                # grand total net collection
                grand_total_net_collection += total_net_collection
                grand_total_net_collection = round(grand_total_net_collection, 2)

                # ================== Actual net cash collections ================
                net_collection_cash = ((collections['total_collection_amt_cash'] + collections['total_due_collection_amt_cash']) - (collections['total_refund_collection_amt_cash']))
                net_collection_cash = round(net_collection_cash, 2)

                # grand total net collection cash
                net_sub_total_coll_cash += net_collection_cash
                net_sub_total_coll_cash = round(net_sub_total_coll_cash, 2)
                # ================== Actual net cash collections ================

                combined_data.append({
                    'inv_id': inv_id.inv_id,  # Assuming inv_id is the primary key
                    'invoice_date': inv_id.invoice_date.strftime('%Y-%m-%d'),
                    'customer_name': inv_id.customer_name,
                    'address': inv_id.address,
                    'mobile_number': inv_id.mobile_number,
                    'coll_pay_modes': collections['coll_pay_modes'],
                    'ref_pay_modes': collections['ref_pay_modes'],
                    # Include other relevant fields similarly
                    'total_sales': total_sales,
                    'total_cost': total_cost,
                    'total_discount': total_discount,
                    'total_vat_tax': total_vat_tax,
                    'total_cancel_amt': total_cancel_amt,
                    'total_net_bill': total_net_bill,
                    'total_collection_amt': collections['total_collection_amt'],
                    'total_due_collection_amt': collections['total_due_collection_amt'],
                    'total_refund_collection_amt': collections['total_refund_collection_amt'],
                    'total_adjust_amt': collections['total_adjust_amt'],
                    'grand_collection': grand_collection,
                    'total_net_collection': total_net_collection,
                    'inv_details': inv_details.get(inv_id.inv_id, []),  # Grouped inv_details for each inv_id
                })
            
            # mobile bank collection
            mobile_bank_coll = grand_bkash_coll_amt + grand_nagad_coll_amt + grand_upay_coll_amt + grand_ucash_coll_amt
            net_mobile_bank_coll = ((mobile_bank_coll + grand_woinvcoll_mb_amt) - (grand_regclipay_mb_amt + grand_suppclipay_mb_amt))

            # mobile bank refund and grand collection
            total_mobile_bank_refund = grand_bkash_ref_amt + grand_nagad_ref_amt + grand_upay_ref_amt + grand_ucash_ref_amt
            grand_mobile_bank = net_mobile_bank_coll - total_mobile_bank_refund
            grand_mobile_bank_coll = round(grand_mobile_bank, 2)

            # bank collection
            total_bank_coll_amt = grand_cheque_coll_amt + grand_debit_card_coll_amt + grand_credit_card_coll_amt + grand_bank_deposit_coll_amt
            net_bank_coll_amt = ((total_bank_coll_amt + grand_woinvcoll_b_amt) - (grand_regclipay_b_amt + grand_suppclipay_b_amt))
            
            # bank refund and grand collection 
            total_bank_refund_amt = grand_cheque_ref_amt + grand_debit_card_ref_amt + grand_credit_card_ref_amt + grand_bank_deposit_ref_amt
            grand_bank_coll = net_bank_coll_amt - total_bank_refund_amt
            grand_total_bank_coll = round(grand_bank_coll, 2)

            # grand total calculations
            grand_total_collection = ((net_sub_total_coll_cash + grand_ret_total_amt + dep_rec_sub_branch + grand_woinvcoll_amt) - (total_other_exp_amt + grand_carrying_pay_amt + grand_total_amt + grand_mrr_total_amt + grand_regclipay_amt + grand_suppclipay_amt))
            grand_total_collection = round(grand_total_collection, 2)

            # Remaining Collection from Total Net Collection
            total_remaining_collection = (grand_total_collection - (deposit_main_branch + total_daily_deposit))
            total_remaining_collection = round(total_remaining_collection, 2)

            data = {
                'combined_data': combined_data,
                'total_collection': total_collection,
                'total_due_collection': total_due_collection,
                'total_grand_collection': total_grand_collection,
                'total_refund_collection': total_refund_collection,
                'total_adjust_collection': total_adjust_collection,
                'grand_total_net_collection': grand_total_net_collection,
                'grandtotal_sales': grandtotal_sales,
                'grand_total_discount': grand_total_discount,
                'grand_total_vat_tax': grand_total_vat_tax,
                'grand_total_cancel_amt': grand_total_cancel_amt,
                'grand_total_net_bill': grand_total_net_bill,
                'total_other_exp_amt': total_other_exp_amt,
                'grand_carrying_pay_amt': grand_carrying_pay_amt,
                'grand_total_collection': grand_total_collection,
                'total_remaining_collection': total_remaining_collection,
                'grandtotal_cost': grandtotal_cost,
                'total_daily_deposit': total_daily_deposit,
                'deposit_main_branch': deposit_main_branch,
                'dep_rec_sub_branch': dep_rec_sub_branch,
                'total_cash_on_hand': total_cash_on_hand,
                'grand_total_amt': grand_total_amt,
                'grand_ret_total_amt': grand_ret_total_amt,
                'grand_mrr_total_amt': grand_mrr_total_amt,
                'grand_bkash_coll_amt': grand_bkash_coll_amt,
                'grand_nagad_coll_amt': grand_nagad_coll_amt,
                'grand_upay_coll_amt': grand_upay_coll_amt,
                'grand_ucash_coll_amt': grand_ucash_coll_amt,
                'mobile_bank_coll': mobile_bank_coll,
                'net_mobile_bank_coll': net_mobile_bank_coll,
                'grand_bkash_ref_amt': grand_bkash_ref_amt,
                'grand_nagad_ref_amt': grand_nagad_ref_amt,
                'grand_upay_ref_amt': grand_upay_ref_amt,
                'grand_ucash_ref_amt': grand_ucash_ref_amt,
                'total_mobile_bank_refund': total_mobile_bank_refund,
                'grand_mobile_bank_coll': grand_mobile_bank_coll,
                'grand_cheque_coll_amt': grand_cheque_coll_amt,
                'grand_debit_card_coll_amt': grand_debit_card_coll_amt,
                'grand_credit_card_coll_amt': grand_credit_card_coll_amt,
                'grand_bank_deposit_coll_amt': grand_bank_deposit_coll_amt,
                'total_bank_coll_amt': total_bank_coll_amt,
                'net_bank_coll_amt': net_bank_coll_amt,
                'grand_cheque_ref_amt': grand_cheque_ref_amt,
                'grand_debit_card_ref_amt': grand_debit_card_ref_amt,
                'grand_credit_card_ref_amt': grand_credit_card_ref_amt,
                'grand_bank_deposit_ref_amt': grand_bank_deposit_ref_amt,
                'total_bank_refund_amt': total_bank_refund_amt,
                'grand_total_bank_coll': grand_total_bank_coll,
                'grand_total_bank_coll': grand_total_bank_coll,
                'grand_woinvcoll_amt': grand_woinvcoll_amt,
                'grand_woinvcoll_mb_amt': grand_woinvcoll_mb_amt,
                'grand_woinvcoll_b_amt': grand_woinvcoll_b_amt,
                'grand_regclipay_amt': grand_regclipay_amt,
                'grand_regclipay_mb_amt': grand_regclipay_mb_amt,
                'grand_regclipay_b_amt': grand_regclipay_b_amt,
                'grand_suppclipay_amt': grand_suppclipay_amt,
                'grand_suppclipay_mb_amt': grand_suppclipay_mb_amt,
                'grand_suppclipay_b_amt': grand_suppclipay_b_amt,
                'net_sub_total_coll_cash': net_sub_total_coll_cash,
                # org and branch info
                'start_from': start_from,
                'end_from': end_from,
                'org_name': organization.org_name if organization else '',
                'org_address': organization.address if organization else '',
                'org_email': organization.email if organization else '',
                'org_website': organization.website if organization else '',
                'org_hotline': organization.hotline if organization else '',
                'org_fax': organization.fax if organization else '',
                'branch_name': branch.branch_name if branch else '',
            }
    
            return JsonResponse(data)
        
        except Exception as e:
            # Log the exception
            print("An error occurred:", e)
            return JsonResponse({'error': str(e)}, status=500)
            # return JsonResponse({'error': 'An error occurred while processing the request'}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)


#========================================sales due collection report ========================================
@login_required()
def salesDueCollectionReportAPI(request):
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

    billingBtn_access = access_list.objects.filter(
        user_id=user,
        feature_id__feature_page_link='BILLINGFORMACCESSBTN',
        is_active=True
    ).exists()
    
    context = {
        'org_list': org_list,
        'billingBtn_access': billingBtn_access
    }

    return render(request, 'sales_coll_report/sales_due_coll_report.html', context)


@login_required()
def salesDueCollDetailsReportManagerAPI(request):
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

    return render(request, 'sales_coll_report/sales_due_coll_dtls_report.html', context)


@login_required()
def getsalesDueCollectionReportManagerAPI(request):
    due_from = None
    due_to = None

    # Initialize the grand total
    all_total_sales = 0
    all_grand_vat_tax = 0
    all_grand_cancel_amt = 0
    all_total_net_bill = 0
    all_total_discount_sum = 0
    grand_total_collection = 0
    grand_total_due_collection = 0
    grand_total_net_collection = 0
    total_other_exp_amt = 0
    total_collection = 0
    total_due_collection = 0
    total_grand_collection = 0
    total_refund_collection = 0
    grand_total_refund_collection = 0
    grand_total_dues = 0
    grand_total_cost_amt = 0
    total_cost_amt = 0
    grand_mobile_bank_coll = 0
    grand_total_bank_coll = 0
    grand_total_amt = 0
    grand_ret_total_amt = 0
    grand_mrr_total_amt = 0
    total_daily_deposit = 0
    deposit_main_branch = 0
    dep_rec_sub_branch = 0
    total_cash_on_hand = 0
    grand_net_collection = 0

    combined_data = []

    if request.method == "POST":
        due_from = request.POST.get('due_from')
        due_to = request.POST.get('due_to')
        org_id = request.POST.get('org_id')
        branch_id = request.POST.get('branch_id')

        # Parse the dates from the request POST data
        due_from = datetime.strptime(due_from, '%Y-%m-%d').date()
        due_to = datetime.strptime(due_to, '%Y-%m-%d').date()

        # Fetch the organization and branch details
        organization = organizationlst.objects.filter(org_id=org_id).first()
        branch = branchslist.objects.filter(branch_id=branch_id).first()

        # Query data from your models
        invoices = invoice_list.objects.filter(invoice_date__range=(due_from, due_to), org_id=org_id, branch_id=branch_id).all()
        invoice_details = invoicedtl_list.objects.all()
        payment_details = payment_list.objects.all()
        other_rent_exp = rent_others_exps.objects.filter(other_exps_date__range=(due_from, due_to), org_id=org_id, branch_id=branch_id).all()
        carrying_cost_buyer = rent_others_exps.objects.filter(other_exps_date__range=(due_from, due_to), is_buyer=True, org_id=org_id, branch_id=branch_id).all()
        daily_cash_on_hand = cash_on_hands.objects.filter(org_id=org_id, branch_id=branch_id)
        local_purchases = local_purchase.objects.filter(transaction_date__range=(due_from, due_to), is_approved=True, is_cash=True, id_org=org_id, branch_id=branch_id)
        local_purchasedtls = local_purchasedtl.objects.filter(lp_rec_date__range=(due_from, due_to)).select_related('lp_id').all()
        lp_returndtls = lp_return_details.objects.filter(returned_date__range=(due_from, due_to)).select_related('lp_id').all()
        manual_return_rec = manual_return_receive.objects.filter(transaction_date__range=(due_from, due_to), is_approved=True, is_cash=True, id_org=org_id, branch_id=branch_id)
        manu_return_recdtls = manual_return_receivedtl.objects.filter(manu_ret_rec_date__range=(due_from, due_to)).select_related('manu_ret_rec_id').all()
        submit_main_branch = daily_bank_statement.objects.filter(deposit_date__range=(due_from, due_to), is_branch_deposit=True, org_id=org_id, branch_id=branch_id).all()
        deposit_rec_sub_branch = daily_bank_statement.objects.filter(deposit_date__range=(due_from, due_to), is_branch_deposit_receive=True, org_id=org_id, branch_id=branch_id).all()
        bank_deposits = daily_bank_statement.objects.filter(deposit_date__range=(due_from, due_to), is_bank_statement=True, org_id=org_id, branch_id=branch_id).all()

        # other rent or expence
        for otherExp in other_rent_exp:
            other_exp_amt = otherExp.other_exps_amt
            total_other_exp_amt += other_exp_amt

        # Initialize collections
        collections_by_inv_id = {}
        total_collection = 0.0
        total_due_collection = 0.0
        total_refund_collection = 0.0

        # Define a mapping of pay_mode to collection keys
        pay_mode_mobile_bank_key = {
            "5": 'total_bkash_coll_amt',
            "6": 'total_nagad_coll_amt',
            "7": 'total_upay_coll_amt',
            "8": 'total_ucash_coll_amt',
        }

        pay_mode_bank_key = {
            "2": 'total_check_coll_amt',
            "3": 'total_debit_coll_amt',
            "4": 'total_credit_coll_amt',
            "9": 'bank_deposit_coll_amt',
        }

        invoice_costs = {}

        # manual return receive
        for mret_rec in manual_return_rec:
            # Filter manu return recdtls
            manu_ret_rec_details = manu_return_recdtls.filter(manu_ret_rec_id=mret_rec)

            for manurrdtl in manu_ret_rec_details:
                # Extract relevant attributes
                mrr_qty = manurrdtl.manu_ret_rec_qty or 0  # Default to 0 if None
                mrr_price = manurrdtl.unit_price or 0
                mrr_discount = manurrdtl.dis_percentage or 0

                # Calculate total amount, discount, and final amount
                mrr_totalamt = mrr_qty * mrr_price
                total_mrr_dis_per = mrr_discount / 100
                total_mrr_dis_amt = mrr_totalamt * total_mrr_dis_per

                # Accumulate the final amount
                grand_mrr_total_amt += mrr_totalamt - total_mrr_dis_amt

        # local purchase
        for lpdata in local_purchases:
            # Filter purchase details and return details by local purchase ID
            lp_details = local_purchasedtls.filter(lp_id=lpdata)
            lp_return_dtls = lp_returndtls.filter(lp_id=lpdata)

            for detail in lp_details:
                # Extract relevant attributes
                lp_qty = detail.lp_rec_qty or 0  # Default to 0 if None
                lp_price = detail.unit_price or 0
                lp_discount = detail.dis_percentage or 0

                # Calculate total amount, discount, and final amount
                lp_totalamt = lp_qty * lp_price
                total_lp_dis_per = lp_discount / 100
                total_dis_amt = lp_totalamt * total_lp_dis_per

                # Accumulate the final amount
                grand_total_amt += lp_totalamt - total_dis_amt

            for returndtls in lp_return_dtls:
                # Fetch the relevant `local_purchasedtl` record for the returned item
                related_detail = local_purchasedtl.objects.filter(lp_id=returndtls.lp_id, item_id=returndtls.item_id).first()

                if related_detail:
                    # Extract attributes from the related detail instance
                    lp_ret_qty = returndtls.lp_return_qty or 0
                    lp_ret_can_qty = returndtls.is_cancel_qty or 0
                    lp_ret_price = related_detail.unit_price or 0
                    lp_ret_discount = related_detail.dis_percentage or 0

                    # Calculate total amount, discount, and final amount for return
                    lp_ret_totalamt = (lp_ret_qty - lp_ret_can_qty) * lp_ret_price
                    total_lpret_dis_per = lp_ret_discount / 100
                    total_ret_dis_amt = lp_ret_totalamt * total_lpret_dis_per

                    # Accumulate the return amount
                    grand_ret_total_amt += lp_ret_totalamt - total_ret_dis_amt

        # Sum the diposit rec from sub branch over the date range
        dep_rec_sub_branch = deposit_rec_sub_branch.aggregate(
            total_amount=Sum('deposits_amt')
        )['total_amount'] or 0  # Return 0 if no deposits are found

        # Sum the diposit of the main branch over the date range
        deposit_main_branch = submit_main_branch.aggregate(
            total_amount=Sum('deposits_amt')
        )['total_amount'] or 0  # Return 0 if no deposits are found

        # Sum the deposits_amt over the date range
        total_daily_deposit = bank_deposits.aggregate(
            total_amount=Sum('deposits_amt')
        )['total_amount'] or 0  # Return 0 if no deposits are found

        # Calculate total cash on hand
        total_cash_on_hand = round(sum(float(hands.on_hand_cash or 0) for hands in daily_cash_on_hand), 2)

        # # ==========================================================================
        # # Create a dictionary to store collections for each inv_id
        # collections_by_inv_id = defaultdict(lambda: {
        #     'total_collection_amt': 0.0,
        #     'total_due_collection_amt': 0.0,
        #     'total_refund_collection_amt': 0.0,
        #     'total_adjust_amt': 0.0,
        #     'total_sales': 0.0,
        #     'total_cost': 0.0,
        #     'mb_total_cost': 0.0,
        #     'b_total_cost': 0.0,
        #     'item_disc': 0.0,
        #     'gross_disc': 0.0,
        #     'total_vat_tax': 0.0,
        #     'total_cancel_amt': 0.0,
        #     'total_net_bill': 0.0,
        #     'total_bkash_coll_amt': 0.0,
        #     'total_nagad_coll_amt': 0.0,
        #     'total_upay_coll_amt': 0.0,
        #     'total_ucash_coll_amt': 0.0,
        #     'total_check_coll_amt': 0.0,
        #     'total_debit_coll_amt': 0.0,
        #     'total_credit_coll_amt': 0.0,
        #     'bank_deposit_coll_amt': 0.0,
        # })

        # # Collect all inv_ids
        # inv_ids = invoices.values_list('inv_id', flat=True)

        # # Exclude all inv_ids at once
        # payments_due_coll = payment_details.exclude(inv_id__in=list(inv_ids)).filter(pay_date__range=(due_from, due_to))

        # for paymentData in payments_due_coll:
        #     # Convert pay_amt to a float
        #     pay_amt = float(paymentData.pay_amt)
        #     # Fetch the related rent_others_exps entry for the current payment's invoice
        #     # others_exps = rent_others_exps.objects.filter(inv_id=paymentData.inv_id).first()
                
        #     # collection
        #     if paymentData.collection_mode == "1":
        #         collections_by_inv_id[paymentData.inv_id]['total_collection_amt'] += pay_amt
        #     # due collection
        #     elif paymentData.collection_mode == "2":
        #         collections_by_inv_id[paymentData.inv_id]['total_due_collection_amt'] += pay_amt

        #     # Refund collection
        #     elif paymentData.collection_mode == "3":
        #         collections_by_inv_id[paymentData.inv_id]['total_refund_collection_amt'] += pay_amt
                
        #     # Adjust collection
        #     elif paymentData.collection_mode == "4":
        #         collections_by_inv_id[paymentData.inv_id]['total_adjust_amt'] += pay_amt
                
        #     # collection = collections['total_collection_amt']
        # # ==========================================================================

        for invoice in invoices:
            details = invoice_details.filter(inv_id=invoice).all()
            payments = payment_details.filter(inv_id=invoice).all()
            cost_buyer = carrying_cost_buyer.filter(inv_id=invoice).all()
        
            # Initialize invoice-wise totals
            total_sales = 0
            grand_total_dis = 0
            grand_vat_tax = 0
            grand_cancel_amt = 0
            refund_amt_sum = 0
            total_due_amt = 0
            grand_total_gross_dis = 0
            total_discount_sum = 0

            # Initialize collections
            total_collection = 0
            total_due_collection = 0
            total_refund_collection = 0
            total_cost_amt = 0

            for buyer in cost_buyer:
                total_cost_amt += buyer.other_exps_amt
                # Store the total cost in the dictionary with inv_id as the key
                invoice_costs[invoice.inv_id] = total_cost_amt

            # Dictionary to store details by invoice ID
            inv_details = {}

            if not details.exists():
                # If no details are found, use default values
                inv_details[invoice.inv_id] = [{
                    'item_id': None,
                    'item_name': 'N/A',
                    'sales_rate': 0,
                    'qty': 0,
                    'uom': 'N/A',
                }]
            else:
                for invdtl in details:
                    # Use the correct structure for inv_id
                    inv_id = invdtl.inv_id.inv_id  # Assuming inv_id is a field in invdtl

                    # Initialize list for each inv_id if not already present
                    if inv_id not in inv_details:
                        inv_details[inv_id] = []

                    # Safely retrieve values with default fallback
                    item_name = getattr(invdtl.item_id, 'item_name', 'N/A')
                    sales_rate = getattr(invdtl, 'sales_rate', 0)
                    qty = getattr(invdtl, 'qty', 0)
                    uom = getattr(invdtl.item_id.item_uom_id, 'item_uom_name', 'N/A')

                    # Append item details to the list under each inv_id
                    inv_details[inv_id].append({
                        'item_id': getattr(invdtl.item_id, 'item_id', None),
                        'item_name': item_name,
                        'sales_rate': sales_rate,
                        'qty': qty,
                        'uom': uom,
                    })

            # Initialize collections for the invoice if not already initialized
            if invoice.inv_id not in collections_by_inv_id:
                collections_by_inv_id[invoice.inv_id] = {
                    'total_bkash_coll_amt': 0.0,
                    'total_nagad_coll_amt': 0.0,
                    'total_upay_coll_amt': 0.0,
                    'total_ucash_coll_amt': 0.0,
                    'total_check_coll_amt': 0.0,
                    'total_debit_coll_amt': 0.0,
                    'total_credit_coll_amt': 0.0,
                    'bank_deposit_coll_amt': 0.0,
                }

            for pay in payments:
                # Convert pay_amt to a float
                pay_amt = float(pay.pay_amt)
                # Fetch rent_others_exps object for this payment
                others_exps = rent_others_exps.objects.filter(inv_id=invoice).first()

                # collection
                if pay.collection_mode == "1":
                    total_collection += pay_amt
                # due collection
                elif pay.collection_mode == "2":
                    total_due_collection += pay_amt
                # refund collection
                elif pay.collection_mode == "3":
                    total_refund_collection += pay_amt

                # =========================== mobile bank wise collections =====================
                # Mobile bank-wise collections
                mobile_bank_key = pay_mode_mobile_bank_key.get(pay.pay_mode)
                if mobile_bank_key:
                    collections_by_inv_id[invoice.inv_id][mobile_bank_key] += pay_amt

                # Bank-wise collections
                bank_key = pay_mode_bank_key.get(pay.pay_mode)
                if bank_key:
                    other_exps_amt = others_exps.other_exps_amt if others_exps else 0
                    collections_by_inv_id[invoice.inv_id][bank_key] += pay_amt - other_exps_amt

            # Item rate over invoice items
            item_total = sum(detail.sales_rate * detail.qty for detail in details)
            total_sales += item_total

            # Discount calculation
            item_w_dis = sum(((detail.item_w_dis / detail.qty) * (detail.qty - detail.is_cancel_qty)) for detail in details)
            grand_total_dis += item_w_dis
            grand_total_dis = round(grand_total_dis, 2)

            total_gross_dis = sum(((detail.gross_dis / detail.qty) * (detail.qty - detail.is_cancel_qty)) for detail in details)
            grand_total_gross_dis += total_gross_dis
            grand_total_gross_dis = round(grand_total_gross_dis, 2)

            total_discount_sum = grand_total_dis + grand_total_gross_dis
            total_discount_sum = round(total_discount_sum, 2)

            # VAT tax calculation
            item_wise_total_vat_tax = sum(((detail.gross_vat_tax / detail.qty) * (detail.qty - detail.is_cancel_qty)) for detail in details)
            grand_vat_tax += item_wise_total_vat_tax
            grand_vat_tax = round(grand_vat_tax, 2)

            # Cancel amount calculation
            total_item_cancel_amt = sum(detail.sales_rate * detail.is_cancel_qty for detail in details)
            grand_cancel_amt += total_item_cancel_amt

            # Calculate total net bill for this invoice
            total_net_bill = ((total_sales + grand_vat_tax + total_cost_amt) - (total_discount_sum + grand_cancel_amt))
            total_net_bill = round(total_net_bill, 2)

            grand_collection = total_collection + total_due_collection
            # total collection amt + total due collection amt
            
            # total net collection
            total_net_collection = (grand_collection - total_refund_collection)
            # grand total net collection
            

            # total dues bill
            total_dues = total_net_bill - total_net_collection

            # total net collection
            grand_net_collection = (grand_total_net_collection + grand_ret_total_amt + dep_rec_sub_branch) - (total_other_exp_amt + grand_total_bank_coll + grand_total_amt + grand_mrr_total_amt)

            # if total_dues > 0 or total_dues < 0:
            # Append invoice-wise data to the combined_data list
            combined_data.append({
                'invoice': invoice.inv_id,
                'customer_name': invoice.customer_name,
                'gender': invoice.gender,
                'mobile_number': invoice.mobile_number,
                'total_sales': total_sales,
                'grand_total_dis': grand_total_dis,
                'grand_vat_tax': grand_vat_tax,
                'grand_cancel_amt': grand_cancel_amt,
                'refund_amt_sum': refund_amt_sum,
                'total_net_bill': total_net_bill,
                'total_due_amt': total_due_amt,
                'grand_total_gross_dis': grand_total_gross_dis,
                'total_discount_sum': total_discount_sum,
                'total_collection_amt': total_collection,
                'total_due_collection_amt': total_due_collection,
                'total_refund_collection_amt': total_refund_collection,
                'total_cost_amt': total_cost_amt,
                'grand_collection': grand_collection,
                'total_net_collection': total_net_collection,
                'total_dues': total_dues,
                'inv_details': inv_details.get(invoice.inv_id, []),
            })

            # Update the all_grand totals
            all_total_sales += total_sales
            all_grand_vat_tax += grand_vat_tax
            all_grand_cancel_amt += grand_cancel_amt
            all_total_net_bill += total_net_bill
            all_total_discount_sum += total_discount_sum
            grand_total_collection += total_collection
            grand_total_due_collection += total_due_collection
            total_grand_collection += grand_collection
            grand_total_refund_collection += total_refund_collection
            grand_total_net_collection += total_net_collection
            grand_total_dues += total_dues
            grand_total_cost_amt += total_cost_amt

        # Ensure grand total is rounded
        grand_total_bank_coll = round(grand_total_bank_coll, 2)

        data = {
            'combined_data': combined_data,
            'all_total_sales': all_total_sales,
            'all_total_discount_sum': all_total_discount_sum,
            'all_grand_vat_tax': all_grand_vat_tax,
            'all_grand_cancel_amt': all_grand_cancel_amt,
            'all_total_net_bill': all_total_net_bill,
            'grand_total_collection': grand_total_collection,
            'total_grand_collection': total_grand_collection,
            'grand_total_due_collection': grand_total_due_collection,
            'total_refund_collection': total_refund_collection,
            'grand_total_refund_collection': grand_total_refund_collection,
            'grand_total_cost_amt': grand_total_cost_amt,
            'grand_total_net_collection': grand_total_net_collection,
            'grand_total_dues': grand_total_dues,
            'total_other_exp_amt': total_other_exp_amt,
            'total_daily_deposit': total_daily_deposit,
            'deposit_main_branch': deposit_main_branch,
            'dep_rec_sub_branch': dep_rec_sub_branch,
            'total_cash_on_hand': total_cash_on_hand,
            'grand_mobile_bank_coll': grand_mobile_bank_coll,
            'grand_total_bank_coll': grand_total_bank_coll,
            'grand_total_amt': grand_total_amt,
            'grand_ret_total_amt': grand_ret_total_amt,
            'grand_mrr_total_amt': grand_mrr_total_amt,
            'grand_net_collection': grand_net_collection,
            # org and branch info
            'due_from': due_from,
            'due_to': due_to,
            'org_name': organization.org_name if organization else '',
            'org_address': organization.address if organization else '',
            'org_email': organization.email if organization else '',
            'org_website': organization.website if organization else '',
            'org_hotline': organization.hotline if organization else '',
            'org_fax': organization.fax if organization else '',
            'branch_name': branch.branch_name if branch else '',
        }

        return JsonResponse(data)

    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)
    

@login_required()
def billingReportDashboardManagerAPI(request):
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

    billingBtn_access = access_list.objects.filter(
        user_id=user,
        feature_id__feature_page_link='BILLINGFORMACCESSBTN',
        is_active=True
    ).exists()
    
    context = {
        'org_list': org_list,
        'billingBtn_access': billingBtn_access
    }

    return render(request, 'sales_coll_report/billing_report_dashboard.html', context)


@login_required()
def sevenDaysBillingStatusViewManagerAPI(request):
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

    billingBtn_access = access_list.objects.filter(
        user_id=user,
        feature_id__feature_page_link='BILLINGFORMACCESSBTN',
        is_active=True
    ).exists()
    
    context = {
        'org_list': org_list,
        'billingBtn_access': billingBtn_access
    }

    return render(request, 'sales_coll_report/billing_seven_days_status.html', context)


@login_required()
def reportSevenDaysBillingManagerAPI(request):

    return render(request, 'sales_coll_report/report_billing_seven_days.html')
