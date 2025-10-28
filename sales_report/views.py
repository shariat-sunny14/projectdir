from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.db.models import Q, F, Sum, Prefetch
from collections import defaultdict
from django.db.models import FloatField
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from item_pos.models import invoice_list, invoicedtl_list, payment_list, rent_others_exps
from organizations.models import branchslist, organizationlst
from user_setup.models import access_list
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def salesReportAPI(request):
    
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

    return render(request, 'sales_coll_report/sales_report.html', context)


@login_required()
def salesDetailsReportManagerAPI(request):
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

    return render(request, 'sales_coll_report/sales_dtls_report.html', context)

@login_required()
def duesDetailsReportManagerAPI(request):
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

    return render(request, 'sales_coll_report/dues_dtls_report.html', context)


@login_required()
def getSalesReportManagerAPI(request):
    start_from = None
    end_from = None

    # Initialize the grand total
    all_grand_total = 0
    all_grand_vat_tax = 0
    all_grand_cancel_amt = 0
    all_total_net_bill = 0
    all_total_discount_sum = 0
    grand_total_cost_amt = 0

    combined_data = []

    if request.method == "POST":
        start_from = request.POST.get('start_from')
        end_from = request.POST.get('end_from')
        org_id = request.POST.get('org_id')
        branch_id = request.POST.get('branch_id')

        # Parse the dates from the request POST data
        start_from = datetime.strptime(start_from, '%Y-%m-%d').date()
        end_from = datetime.strptime(end_from, '%Y-%m-%d').date()

        # Fetch the organization and branch details
        organization = organizationlst.objects.filter(org_id=org_id).first()
        branch = branchslist.objects.filter(branch_id=branch_id).first()

        # Query data from your models
        invoices = invoice_list.objects.filter(invoice_date__range=(start_from, end_from), org_id=org_id, branch_id=branch_id).all()
        invoice_details = invoicedtl_list.objects.all()
        payments = payment_list.objects.all()
        carrying_cost_buyer = rent_others_exps.objects.filter(is_buyer=True, org_id=org_id, branch_id=branch_id).all()

        for invoice in invoices:
            details = invoice_details.filter(inv_id=invoice).all()
            cost_buyer = carrying_cost_buyer.filter(inv_id=invoice).all()

            # Initialize invoice-wise totals
            grand_total = 0
            grand_total_dis = 0
            grand_vat_tax = 0
            grand_cancel_amt = 0
            refund_amt_sum = 0
            total_collection_amt = 0
            total_due_amt = 0
            grand_total_gross_dis = 0
            total_discount_sum = 0
            total_cost_amt = 0

            # Dictionary to store details by invoice ID
            inv_details = {}

            for invdtl in details:
                # Use the correct structure for inv_id
                inv_id = invdtl.inv_id.inv_id  # Assuming inv_id is a field in invdtl

                # Initialize list for each inv_id if not already present
                if inv_id not in inv_details:
                    inv_details[inv_id] = []

                # Append item details to the list under each inv_id
                inv_details[inv_id].append({
                    'item_id': invdtl.item_id.item_id,
                    'item_name': invdtl.item_id.item_name,
                    'sales_rate': invdtl.sales_rate,
                    'qty': invdtl.qty,
                    'uom': invdtl.item_id.item_uom_id.item_uom_name,
                })

            for buyer in cost_buyer:
                cost_amt = buyer.other_exps_amt
                total_cost_amt += cost_amt

            # Item rate over invoice items
            item_total = sum(detail.sales_rate * detail.qty for detail in details)
            grand_total += item_total

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
            total_net_bill = ((grand_total + grand_vat_tax + total_cost_amt) - (total_discount_sum + grand_cancel_amt))
            total_net_bill = round(total_net_bill, 2)

            # Append invoice-wise data to the combined_data list
            combined_data.append({
                'invoice': invoice.inv_id,
                'invoice_date': invoice.invoice_date,
                'customer_name': invoice.customer_name,
                'gender': invoice.gender,
                'mobile_number': invoice.mobile_number,
                'grand_total': grand_total,
                'total_cost_amt': + total_cost_amt,
                'grand_total_dis': grand_total_dis,
                'grand_vat_tax': grand_vat_tax,
                'grand_cancel_amt': grand_cancel_amt,
                'refund_amt_sum': refund_amt_sum,
                'total_net_bill': total_net_bill,
                'total_collection_amt': total_collection_amt,
                'total_due_amt': total_due_amt,
                'grand_total_gross_dis': grand_total_gross_dis,
                'total_discount_sum': total_discount_sum,
                'inv_details': inv_details.get(invoice.inv_id, []),
            })

            # Update the all_grand totals
            all_grand_total += grand_total
            all_grand_vat_tax += grand_vat_tax
            all_grand_cancel_amt += grand_cancel_amt
            all_total_net_bill += total_net_bill
            all_total_discount_sum += total_discount_sum
            grand_total_cost_amt += total_cost_amt

        data = {
            'combined_data': combined_data,
            'all_grand_total': all_grand_total,
            'grand_total_cost_amt': grand_total_cost_amt,
            'all_total_discount_sum': all_total_discount_sum,
            'all_grand_vat_tax': all_grand_vat_tax,
            'all_grand_cancel_amt': all_grand_cancel_amt,
            'all_total_net_bill': all_total_net_bill,
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

    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)
    


# # due report
@login_required()
def dueReportAPI(request):
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

    return render(request, 'sales_coll_report/due_report.html', context)

@login_required()
def getDueReportManagerAPI(request):
    start_from = None
    end_from = None

    # Initialize the grand total
    all_total_sales = 0
    all_grand_vat_tax = 0
    all_grand_cancel_amt = 0
    all_total_net_bill = 0
    all_total_discount_sum = 0
    grand_total_collection = 0
    grand_total_due_collection = 0
    grand_total_net_collection = 0
    total_collection = 0
    total_due_collection = 0
    total_grand_collection = 0
    total_refund_collection = 0
    grand_total_refund_collection = 0
    grand_total_dues = 0
    grand_total_cost_amt = 0

    combined_data = []

    if request.method == "POST":
        start_from = request.POST.get('start_from')
        end_from = request.POST.get('end_from')
        org_id = request.POST.get('org_id')
        branch_id = request.POST.get('branch_id')

        # Parse the dates from the request POST data
        start_from = datetime.strptime(start_from, '%Y-%m-%d').date()
        end_from = datetime.strptime(end_from, '%Y-%m-%d').date()

        # Fetch the organization and branch details
        organization = organizationlst.objects.filter(org_id=org_id).first()
        branch = branchslist.objects.filter(branch_id=branch_id).first()

        # Query data from your models with prefetch_related for optimization
        invoices = invoice_list.objects.filter(
            invoice_date__range=(start_from, end_from), 
            org_id=org_id, 
            branch_id=branch_id
        ).prefetch_related(
            Prefetch(
                'invoicedtl_list_set', 
                queryset=invoicedtl_list.objects.select_related('item_id', 'item_uom_id'), 
                to_attr='details'
            ),
            Prefetch(
                'payment_list_set', 
                queryset=payment_list.objects.all(), 
                to_attr='payments'
            ),
            Prefetch(
                'rent_others_exps_set', 
                queryset=rent_others_exps.objects.filter(is_buyer=True), 
                to_attr='cost_buyer'
            )
        )

        for invoice in invoices:
            details = invoice.details
            payments = invoice.payments
            cost_buyer = invoice.cost_buyer

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

            for pay in payments:
                # Convert pay_amt to a float
                pay_amt = float(pay.pay_amt)
                # collection
                if pay.collection_mode == "1":
                    total_collection += pay_amt
                # due collection
                elif pay.collection_mode == "2":
                    total_due_collection += pay_amt
                # refund collection
                elif pay.collection_mode == "3":
                    total_refund_collection += pay_amt

            # Dictionary to store details by invoice ID
            inv_details = {}

            for invdtl in details:
                # Use the correct structure for inv_id
                inv_id = invdtl.inv_id.inv_id  # Assuming inv_id is a field in invdtl

                # Initialize list for each inv_id if not already present
                if inv_id not in inv_details:
                    inv_details[inv_id] = []

                # Append item details to the list under each inv_id
                inv_details[inv_id].append({
                    'item_id': invdtl.item_id.item_id,
                    'item_name': invdtl.item_id.item_name,
                    'sales_rate': invdtl.sales_rate,
                    'qty': invdtl.qty,
                    'uom': invdtl.item_id.item_uom_id.item_uom_name,
                })

            for buyer in cost_buyer:
                cost_amt = buyer.other_exps_amt
                total_cost_amt += cost_amt

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
            total_dues = round(total_dues, 0)

            if total_dues > 0 or total_dues < 0:
                # Append invoice-wise data to the combined_data list
                combined_data.append({
                    'invoice': invoice.inv_id,
                    'invoice_date': invoice.invoice_date,
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
                all_total_net_bill = round(all_total_net_bill, 2)
                all_total_discount_sum += total_discount_sum
                grand_total_collection += total_collection
                grand_total_due_collection += total_due_collection
                total_grand_collection += grand_collection
                grand_total_refund_collection += total_refund_collection
                grand_total_net_collection += total_net_collection
                grand_total_net_collection = round(grand_total_net_collection, 2)
                grand_total_dues += total_dues
                grand_total_dues = round(grand_total_dues, 0)
                grand_total_cost_amt += total_cost_amt
                

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

    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)
    # start_from = None
    # end_from = None

    # # Initialize the grand total
    # all_total_sales = 0
    # all_grand_vat_tax = 0
    # all_grand_cancel_amt = 0
    # all_total_net_bill = 0
    # all_total_discount_sum = 0
    # grand_total_collection = 0
    # grand_total_due_collection = 0
    # grand_total_net_collection = 0
    # total_collection = 0
    # total_due_collection = 0
    # total_grand_collection = 0
    # total_refund_collection = 0
    # grand_total_refund_collection = 0
    # grand_total_dues = 0
    # grand_total_cost_amt = 0

    # combined_data = []

    # if request.method == "POST":
    #     start_from = request.POST.get('start_from')
    #     end_from = request.POST.get('end_from')
    #     org_id = request.POST.get('org_id')
    #     branch_id = request.POST.get('branch_id')

    #     # Parse the dates from the request POST data
    #     start_from = datetime.strptime(start_from, '%Y-%m-%d').date()
    #     end_from = datetime.strptime(end_from, '%Y-%m-%d').date()

    #     # Fetch the organization and branch details
    #     organization = organizationlst.objects.filter(org_id=org_id).first()
    #     branch = branchslist.objects.filter(branch_id=branch_id).first()

    #     # Query data from your models
    #     invoices = invoice_list.objects.filter(invoice_date__range=(start_from, end_from), org_id=org_id, branch_id=branch_id).all()
    #     invoice_details = invoicedtl_list.objects.all()
    #     payment_details = payment_list.objects.all()
    #     carrying_cost_buyer = rent_others_exps.objects.filter(is_buyer=True, org_id=org_id, branch_id=branch_id).all()

    #     for invoice in invoices:
    #         details = invoice_details.filter(inv_id=invoice).all()
    #         payments = payment_details.filter(inv_id=invoice).all()
    #         cost_buyer = carrying_cost_buyer.filter(inv_id=invoice).all()

    #         # Initialize invoice-wise totals
    #         total_sales = 0
    #         grand_total_dis = 0
    #         grand_vat_tax = 0
    #         grand_cancel_amt = 0
    #         refund_amt_sum = 0
    #         total_due_amt = 0
    #         grand_total_gross_dis = 0
    #         total_discount_sum = 0

    #         # Initialize collections
    #         total_collection = 0
    #         total_due_collection = 0
    #         total_refund_collection = 0
    #         total_cost_amt = 0

    #         for pay in payments:
    #             # Convert pay_amt to a float
    #             pay_amt = float(pay.pay_amt)
    #             # collection
    #             if pay.collection_mode == "1":
    #                 total_collection += pay_amt
    #             # due collection
    #             elif pay.collection_mode == "2":
    #                 total_due_collection += pay_amt
    #             # refund collection
    #             elif pay.collection_mode == "3":
    #                 total_refund_collection += pay_amt

    #         # Dictionary to store details by invoice ID
    #         inv_details = {}

    #         for invdtl in details:
    #             # Use the correct structure for inv_id
    #             inv_id = invdtl.inv_id.inv_id  # Assuming inv_id is a field in invdtl

    #             # Initialize list for each inv_id if not already present
    #             if inv_id not in inv_details:
    #                 inv_details[inv_id] = []

    #             # Append item details to the list under each inv_id
    #             inv_details[inv_id].append({
    #                 'item_id': invdtl.item_id.item_id,
    #                 'item_name': invdtl.item_id.item_name,
    #                 'sales_rate': invdtl.sales_rate,
    #                 'qty': invdtl.qty,
    #                 'uom': invdtl.item_id.item_uom_id.item_uom_name,
    #             })

    #         for buyer in cost_buyer:
    #             cost_amt = buyer.other_exps_amt
    #             total_cost_amt += cost_amt

    #         # Item rate over invoice items
    #         item_total = sum(detail.sales_rate * detail.qty for detail in details)
    #         total_sales += item_total

    #         # Discount calculation
    #         item_w_dis = sum(((detail.item_w_dis / detail.qty) * (detail.qty - detail.is_cancel_qty)) for detail in details)
    #         grand_total_dis += item_w_dis
    #         grand_total_dis = round(grand_total_dis, 2)

    #         total_gross_dis = sum(((detail.gross_dis / detail.qty) * (detail.qty - detail.is_cancel_qty)) for detail in details)
    #         grand_total_gross_dis += total_gross_dis
    #         grand_total_gross_dis = round(grand_total_gross_dis, 2)

    #         total_discount_sum = grand_total_dis + grand_total_gross_dis
    #         total_discount_sum = round(total_discount_sum, 2)

    #         # VAT tax calculation
    #         item_wise_total_vat_tax = sum(((detail.gross_vat_tax / detail.qty) * (detail.qty - detail.is_cancel_qty)) for detail in details)
    #         grand_vat_tax += item_wise_total_vat_tax
    #         grand_vat_tax = round(grand_vat_tax, 2)

    #         # Cancel amount calculation
    #         total_item_cancel_amt = sum(detail.sales_rate * detail.is_cancel_qty for detail in details)
    #         grand_cancel_amt += total_item_cancel_amt

    #         # Calculate total net bill for this invoice
    #         total_net_bill = ((total_sales + grand_vat_tax + total_cost_amt) - (total_discount_sum + grand_cancel_amt))
    #         total_net_bill = round(total_net_bill, 2)

    #         grand_collection = total_collection + total_due_collection
    #         # total collection amt + total due collection amt
            
    #         # total net collection
    #         total_net_collection = (grand_collection - total_refund_collection)
    #         # grand total net collection
            

    #         # total dues bill
    #         total_dues = total_net_bill - total_net_collection
    #         total_dues = round(total_dues, 0)

    #         if total_dues > 0 or total_dues < 0:
    #             # Append invoice-wise data to the combined_data list
    #             combined_data.append({
    #                 'invoice': invoice.inv_id,
    #                 'invoice_date': invoice.invoice_date,
    #                 'customer_name': invoice.customer_name,
    #                 'gender': invoice.gender,
    #                 'mobile_number': invoice.mobile_number,
    #                 'total_sales': total_sales,
    #                 'grand_total_dis': grand_total_dis,
    #                 'grand_vat_tax': grand_vat_tax,
    #                 'grand_cancel_amt': grand_cancel_amt,
    #                 'refund_amt_sum': refund_amt_sum,
    #                 'total_net_bill': total_net_bill,
    #                 'total_due_amt': total_due_amt,
    #                 'grand_total_gross_dis': grand_total_gross_dis,
    #                 'total_discount_sum': total_discount_sum,
    #                 'total_collection_amt': total_collection,
    #                 'total_due_collection_amt': total_due_collection,
    #                 'total_refund_collection_amt': total_refund_collection,
    #                 'total_cost_amt': total_cost_amt,
    #                 'grand_collection': grand_collection,
    #                 'total_net_collection': total_net_collection,
    #                 'total_dues': total_dues,
    #                 'inv_details': inv_details.get(invoice.inv_id, []),
    #             })

    #             # Update the all_grand totals
    #             all_total_sales += total_sales
    #             all_grand_vat_tax += grand_vat_tax
    #             all_grand_cancel_amt += grand_cancel_amt
    #             all_total_net_bill += total_net_bill
    #             all_total_net_bill = round(all_total_net_bill, 2)
    #             all_total_discount_sum += total_discount_sum
    #             grand_total_collection += total_collection
    #             grand_total_due_collection += total_due_collection
    #             total_grand_collection += grand_collection
    #             grand_total_refund_collection += total_refund_collection
    #             grand_total_net_collection += total_net_collection
    #             grand_total_net_collection = round(grand_total_net_collection, 2)
    #             grand_total_dues += total_dues
    #             grand_total_dues = round(grand_total_dues, 0)
    #             grand_total_cost_amt += total_cost_amt
                

    #     data = {
    #         'combined_data': combined_data,
    #         'all_total_sales': all_total_sales,
    #         'all_total_discount_sum': all_total_discount_sum,
    #         'all_grand_vat_tax': all_grand_vat_tax,
    #         'all_grand_cancel_amt': all_grand_cancel_amt,
    #         'all_total_net_bill': all_total_net_bill,
    #         'grand_total_collection': grand_total_collection,
    #         'total_grand_collection': total_grand_collection,
    #         'grand_total_due_collection': grand_total_due_collection,
    #         'total_refund_collection': total_refund_collection,
    #         'grand_total_refund_collection': grand_total_refund_collection,
    #         'grand_total_cost_amt': grand_total_cost_amt,
    #         'grand_total_net_collection': grand_total_net_collection,
    #         'grand_total_dues': grand_total_dues,
    #         # org and branch info
    #         'start_from': start_from,
    #         'end_from': end_from,
    #         'org_name': organization.org_name if organization else '',
    #         'org_address': organization.address if organization else '',
    #         'org_email': organization.email if organization else '',
    #         'org_website': organization.website if organization else '',
    #         'org_hotline': organization.hotline if organization else '',
    #         'org_fax': organization.fax if organization else '',
    #         'branch_name': branch.branch_name if branch else '',
    #     }

    #     return JsonResponse(data)

    # else:
    #     return JsonResponse({'error': 'Invalid request'}, status=400)


# # due report
# @login_required()
# def dueReportAPI(request):
#     if request.method == "POST":
#         resp = {'status': 'failed', 'msg': ''}

#     due_from = None
#     due_to = None

#     # Define context here
#     combined_data = []
#     context = {}

#     grand_total_net_collection = 0
#     total_collection = 0
#     total_due_collection = 0
#     total_grand_collection = 0
#     total_refund_collection = 0
#     grandtotal_sales = 0
#     grand_total_discount = 0
#     grand_total_vat_tax = 0
#     grand_total_cancel_amt = 0
#     grand_total_net_bill = 0
#     grand_total_dues = 0

#     if request.method == "POST":
#         due_from = request.POST.get('due_from')
#         due_to = request.POST.get('due_to')

#         # Parse the dates from the request POST data
#         due_from = datetime.strptime(due_from, '%Y-%m-%d').date()
#         due_to = datetime.strptime(due_to, '%Y-%m-%d').date()

#         # Query data from your models
#         payments = payment_list.objects.filter(pay_date__range=(due_from, due_to)).all()
#         invoice_details = invoicedtl_list.objects.all()

#         if payments.exists():
#             # Calculate total sales per inv_id
#             sales_totals = invoice_details.filter(inv_id__in=payments.values_list('inv_id')).values('inv_id').annotate(
#                 total_sales=Sum(F('sales_rate') * F('qty'), output_field=FloatField())
#             )

#             item_w_discount = invoice_details.filter(inv_id__in=payments.values_list('inv_id')).values('inv_id').annotate(
#                 item_disc=Sum(((F('item_w_dis') / F('qty')) * ((F('qty') - F('is_cancel_qty')))), output_field=FloatField())
#             )

#             gross_discount = invoice_details.filter(inv_id__in=payments.values_list('inv_id')).values('inv_id').annotate(
#                 gross_disc=Sum(((F('gross_dis') / F('qty')) * ((F('qty') - F('is_cancel_qty')))), output_field=FloatField())
#             )

#             item_w_gross_vat_tax = invoice_details.filter(inv_id__in=payments.values_list('inv_id')).values('inv_id').annotate(
#                 total_vat_tax=Sum(((F('gross_vat_tax') / F('qty')) * ((F('qty') - F('is_cancel_qty')))), output_field=FloatField())
#             )

#             cancel_amt = invoice_details.filter(inv_id__in=payments.values_list('inv_id')).values('inv_id').annotate(
#                 total_cancel_amt=Sum((F('sales_rate') * F('is_cancel_qty')), output_field=FloatField())
#             )
#         else:
#             # If there are no payments within the specified date range, retrieve data directly from invoice_details
#             sales_totals = invoice_details.values('inv_id').annotate(
#                 total_sales=Sum(F('sales_rate') * F('qty'), output_field=FloatField())
#             )

#             item_w_discount = invoice_details.values('inv_id').annotate(
#                 item_disc=Sum(((F('item_w_dis') / F('qty')) * ((F('qty') - F('is_cancel_qty')))), output_field=FloatField())
#             )

#             gross_discount = invoice_details.values('inv_id').annotate(
#                 gross_disc=Sum(((F('gross_dis') / F('qty')) * ((F('qty') - F('is_cancel_qty')))), output_field=FloatField())
#             )

#             item_w_gross_vat_tax = invoice_details.values('inv_id').annotate(
#                 total_vat_tax=Sum(((F('gross_vat_tax') / F('qty')) * ((F('qty') - F('is_cancel_qty')))), output_field=FloatField())
#             )

#             cancel_amt = invoice_details.values('inv_id').annotate(
#                 total_cancel_amt=Sum((F('sales_rate') * F('is_cancel_qty')), output_field=FloatField())
#             )

#         # Create a dictionary to store collections for each inv_id
#         collections_by_inv_id = defaultdict(lambda: {
#             'total_collection_amt': 0.0,
#             'total_due_collection_amt': 0.0,
#             'total_refund_collection_amt': 0.0,
#             'total_sales': 0.0,
#             'item_disc': 0.0,
#             'gross_disc': 0.0,
#             'total_vat_tax': 0.0,
#             'total_cancel_amt': 0.0,
#             'total_net_bill': 0.0,
#             'total_dues': 0.0,
#         })

#         for paymentData in payments:
#             # Convert pay_amt to a float
#             pay_amt = float(paymentData.pay_amt)
#             # collection
#             if paymentData.collection_mode == "1":
#                 collections_by_inv_id[paymentData.inv_id]['total_collection_amt'] += pay_amt
#             # due collection
#             elif paymentData.collection_mode == "2":
#                 collections_by_inv_id[paymentData.inv_id]['total_due_collection_amt'] += pay_amt

#             # due collection
#             elif paymentData.collection_mode == "3":
#                 collections_by_inv_id[paymentData.inv_id]['total_refund_collection_amt'] += pay_amt

#         for inv_id, collections in collections_by_inv_id.items():
#             if payments.exists():
#                 # Get total sales for this inv_id from the annotated values
#                 total_sales = sales_totals.get(inv_id=inv_id)['total_sales']
#             else:
#                 total_sales = sales_totals.get(inv_id=inv_id)['total_sales']

#             collections['total_sales'] = total_sales
#             grandtotal_sales += total_sales

#             # item wise discount
#             item_disc = item_w_discount.get(inv_id=inv_id)['item_disc']
#             item_disc = round(item_disc, 2)
#             collections['item_disc'] = item_disc

#             # gross discount
#             gross_disc = gross_discount.get(inv_id=inv_id)['gross_disc']
#             gross_disc = round(gross_disc, 2)
#             collections['gross_disc'] = gross_disc

#             # total discount
#             total_discount = collections['item_disc'] + collections['gross_disc']
#             # total discount sun
#             grand_total_discount += total_discount

#             # total vat tax
#             total_vat_tax = item_w_gross_vat_tax.get(inv_id=inv_id)['total_vat_tax']
#             total_vat_tax = round(total_vat_tax, 2)
#             collections['total_vat_tax'] = total_vat_tax

#             # grand total vat tax
#             grand_total_vat_tax += total_vat_tax

#             # total cancel amount
#             total_cancel_amt = cancel_amt.get(inv_id=inv_id)['total_cancel_amt']
#             total_cancel_amt = round(total_cancel_amt, 2)
#             collections['total_cancel_amt'] = total_cancel_amt
#             # grand total cancel amount
#             grand_total_cancel_amt += total_cancel_amt

#             # total net bill
#             total_net_bill = ((collections['total_sales'] + collections['total_vat_tax']) - (
#                         collections['item_disc'] + collections['gross_disc']) - collections['total_cancel_amt'])
#             total_net_bill = round(total_net_bill, 2)
#             # grand total_net_bill
#             grand_total_net_bill += total_net_bill

#             ########################################
#             # total collection amt
#             collection = collections['total_collection_amt']
#             total_collection += collection

#             # total due collection amt
#             due_collection = collections['total_due_collection_amt']
#             total_due_collection += due_collection

#             # total refund collection
#             refund_collection = collections['total_refund_collection_amt']
#             total_refund_collection += refund_collection

#             grand_collection = collections['total_collection_amt'] + collections['total_due_collection_amt']
#             # total collection amt + total due collection amt
#             total_grand_collection += grand_collection
#             # total net collection
#             total_net_collection = (
#                         (collections['total_collection_amt'] + collections['total_due_collection_amt']) - collections[
#                     'total_refund_collection_amt'])
            
#             # grand total net collection
#             grand_total_net_collection += total_net_collection

#             # total dues bill
#             total_dues = total_net_bill - total_net_collection
#             # grand total dues bill
#             grand_total_dues += total_dues

#             combined_data.append({
#                 'inv_id': inv_id,
#                 'total_sales': total_sales,
#                 'total_discount': total_discount,
#                 'total_vat_tax': total_vat_tax,
#                 'total_cancel_amt': total_cancel_amt,
#                 'total_net_bill': total_net_bill,
#                 'total_collection_amt': collections['total_collection_amt'],
#                 'total_due_collection_amt': collections['total_due_collection_amt'],
#                 'total_refund_collection_amt': collections['total_refund_collection_amt'],
#                 'grand_collection': grand_collection,
#                 'total_net_collection': total_net_collection,
#                 'total_dues': total_dues,
#             })

#         context = {
#             'combined_data': combined_data,
#             'total_collection': total_collection,
#             'total_due_collection': total_due_collection,
#             'total_grand_collection': total_grand_collection,
#             'total_refund_collection': total_refund_collection,
#             'grand_total_net_collection': grand_total_net_collection,
#             'grandtotal_sales': grandtotal_sales,
#             'grand_total_discount': grand_total_discount,
#             'grand_total_vat_tax': grand_total_vat_tax,
#             'grand_total_cancel_amt': grand_total_cancel_amt,
#             'grand_total_net_bill': grand_total_net_bill,
#             'grand_total_dues': grand_total_dues,
#         }
#     else:
#         # If not a POST request or no date range specified, retrieve all invoices
#         combined_data = []

#     return render(request, 'sales_coll_report/due_report.html', context)
