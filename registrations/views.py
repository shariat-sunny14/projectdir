import sys
import json
from PIL import Image
from io import BytesIO
from datetime import date, datetime
from django.db.models import Q, F, Sum, Prefetch, ExpressionWrapper, fields, FloatField
from django.db import models
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils.dateparse import parse_date
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from organizations.models import organizationlst
from item_pos.models import invoice_list, invoicedtl_list, payment_list, rent_others_exps
from clients_transection.models import opening_balance
from local_purchase.models import local_purchase, local_purchasedtl
from . models import in_registrations
from user_setup.models import lookup_values
from django.contrib.auth import get_user_model
User = get_user_model()

@login_required()
def customerRegistrationManagerAPI(request):
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
    return render(request, 'registration/registration.html', context)


# add Registration modal
@login_required()
def addRegistrationModelManageAPI(request):
    user = request.user

    division_name = 'division'
    district_name = 'district'
    upazila_name = 'upazila'

    if user.is_superuser:
        # If the user is a superuser, retrieve all organizations
        org_list = organizationlst.objects.filter(is_active=True).all()
    elif user.org_id is not None:
        # If the user has an associated organization, retrieve only that organization
        org_list = organizationlst.objects.filter(is_active=True, org_id=user.org_id).all()
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
    return render(request, 'registration/add_registration.html', context)



@login_required()
def saveRegistrationsAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST
    reg_id = data.get('reg_id')

    try:
        with transaction.atomic():
            # Check if reg_id is provided for an update or add operation
            if reg_id and reg_id.isnumeric() and int(reg_id) > 0:
                reg_data = in_registrations.objects.get(reg_id=reg_id)
                check_phone = in_registrations.objects.exclude(reg_id=reg_id).filter(mobile_number=data.get('mobile_number')).exists()

                if check_phone:
                    return JsonResponse({'success': False, 'errmsg': 'Mobile Number Already Exists'})
            else:
                check_phone = in_registrations.objects.filter(mobile_number=data.get('mobile_number')).exists()

                if check_phone:
                    return JsonResponse({'success': False, 'errmsg': 'Mobile Number Already Exists'})

                reg_data = in_registrations()

            # Update or set the fields based on request data
            reg_data.full_name = data.get('full_name')
            reg_data.gender = data.get('gender')
            reg_data.marital_status = data.get('marital_status')
            reg_data.mobile_number = data.get('mobile_number')
            reg_data.dateofbirth = data.get('dateofbirth')
            reg_data.blood_group = data.get('blood_group')
            reg_data.patient_type = data.get('patient_type')
            reg_data.co_name = data.get('co_name')
            reg_data.co_relationship = data.get('co_relationship')
            reg_data.co_mobile_number = data.get('co_mobile_number')
            reg_data.division = data.get('division')
            reg_data.district = data.get('district')
            reg_data.thana_upazila = data.get('thana_upazila')
            reg_data.address = data.get('address')
            reg_data.occupation = data.get('occupation')
            reg_data.religion = data.get('religion')
            reg_data.nationality = data.get('nationality')
            reg_data.email = data.get('email')
            reg_data.identity_mark = data.get('identity_mark')
            reg_data.father_name = data.get('father_name')
            reg_data.mother_name = data.get('mother_name')
            reg_data.emergency_con_name = data.get('emergency_con_name')
            reg_data.emergency_con_mobile = data.get('emergency_con_mobile')
            reg_data.emergency_con_rel = data.get('emergency_con_rel')
            reg_data.emergency_con_address = data.get('emergency_con_address')

            if data.get('org_id'):
                org_obj = organizationlst.objects.get(org_id=data.get('org_id'))
                reg_data.org_id = org_obj

            # Handle image if provided
            if 'customer_img' in request.FILES:
                logo_file = request.FILES['customer_img']
                logo_image = Image.open(logo_file)
                if logo_image.mode in ('RGBA', 'LA') or (logo_image.mode == 'P' and 'transparency' in logo_image.info):
                    logo_image = logo_image.convert('RGB')
                logo_image.thumbnail((300, 300))
                output = BytesIO()
                logo_image.save(output, format='JPEG')
                output.seek(0)
                filename = default_storage.save('customer_imgs/' + logo_file.name, ContentFile(output.read()))
                if reg_data.customer_img and reg_data.customer_img.name != filename:
                    default_storage.delete(reg_data.customer_img.path)
                reg_data.customer_img = filename

            reg_data.ss_creator = request.user
            reg_data.ss_modifier = request.user
            reg_data.save()

            resp['success'] = True
            resp['msg'] = "Data saved successfully"

    except Exception as e:
        resp['success'] = False
        resp['errmsg'] = str(e)

    return JsonResponse(resp)


@login_required()
def getCustomerRegistrationsListAPI(request):
    reg_list = in_registrations.objects.all()

    # Retrieve filter parameters from the frontend
    is_active = request.GET.get('is_active', None)
    org_id = request.GET.get('org_id', None)
    start_date = request.GET.get('startDate', None)
    end_date = request.GET.get('endDate', None)

    # Create an empty filter dictionary to store dynamic filter conditions
    filter_conditions = {}

    # Apply filters based on conditions
    if is_active is not None:
        # Only filter if the value is not '1', meaning we don't filter when 'All' is selected
        if is_active == 'true':
            filter_conditions['is_active'] = True
        elif is_active == 'false':
            filter_conditions['is_active'] = False

    if org_id is not None and org_id != 'None':
        filter_conditions['org_id'] = org_id

    # Convert startDate and endDate from strings to dates and apply the filter
    if start_date:
        start_date = parse_date(start_date)
        filter_conditions['reg_date__gte'] = start_date
    if end_date:
        end_date = parse_date(end_date)
        filter_conditions['reg_date__lte'] = end_date

    # Apply dynamic filters to reg_list
    reg_data = reg_list.filter(**filter_conditions)

    # Convert reg data to a list of dictionaries
    regs_data = []
    for reg in reg_data:
        org_name = ''
        customer_img_url = ''

        if reg.org_id:
            org_name = reg.org_id.org_name

        if reg.customer_img:
            customer_img_url = reg.customer_img.url

        regs_data.append({
            'reg_id': reg.reg_id,
            'customer_no': reg.customer_no,
            'full_name': reg.full_name,
            'customer_img': customer_img_url,
            'gender': reg.gender,
            'marital_status': reg.marital_status,
            'mobile_number': reg.mobile_number,
            'dateofbirth': reg.dateofbirth,
            'blood_group': reg.blood_group,
            'org_name': org_name,
            'patient_type': reg.patient_type,
            'reg_date': reg.reg_date,
            'address': reg.address,
            'is_active': reg.is_active,
        })

    # Return the filtered data as JSON
    return JsonResponse({'regs_data': regs_data})


@login_required()
def editRegistrationModelManageAPI(request):
    user = request.user

    division_name = 'division'
    district_name = 'district'
    upazila_name = 'upazila'
    
    if user.is_superuser:
        # If the user is a superuser, retrieve all organizations
        org_list = organizationlst.objects.filter(is_active=True).all()
    elif user.org_id is not None:
        # If the user has an associated organization, retrieve only that organization
        org_list = organizationlst.objects.filter(is_active=True, org_id=user.org_id).all()
    else:
        # If neither a superuser nor associated with an organization, set organizations to an empty list or handle as needed
        org_list = []
        
        reg_data = {}
    if request.method == 'GET':
        data = request.GET
        reg_id = ''
        if 'reg_id' in data:
            reg_id = data['reg_id']
        if reg_id.isnumeric() and int(reg_id) > 0:
            reg_data = in_registrations.objects.filter(reg_id=reg_id).first()
    
    divisions = lookup_values.objects.filter(identify_code=division_name).all()
    districts = lookup_values.objects.filter(identify_code=district_name).all()
    upazilas = lookup_values.objects.filter(identify_code=upazila_name).all()

    context = {
        'reg_data': reg_data,
        'org_list': org_list,
        'divisions': divisions,
        'districts': districts,
        'upazilas': upazilas,
    }
    return render(request, 'registration/edit_registration.html', context)


@login_required()
def activeRegistrationManagerAPI(request):
    reg_data = {}
    if request.method == 'GET':
        data = request.GET
        reg_id = ''
        if 'reg_id' in data:
            reg_id = data['reg_id']
        if reg_id.isnumeric() and int(reg_id) > 0:
            reg_data = in_registrations.objects.filter(reg_id=reg_id).first()

    context = {
        'reg_data': reg_data,
    }
    return render(request, 'registration/active_registrations.html', context)


@login_required()
def activeRegSubmissionAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST
    reg_id = data.get('reg_id')

    try:
        with transaction.atomic():
            # Retrieve the in_registrations object based on reg_id
            reg_data = in_registrations.objects.get(reg_id=reg_id)
            
            # Update the fields
            reg_data.is_active = True
            reg_data.ss_modifier = request.user  # Set the user who is modifying

            reg_data.save()  # Save the changes to the database

            resp['success'] = True
            resp['msg'] = "Customer Activated successfully"

    except in_registrations.DoesNotExist:
        resp['errmsg'] = "Registration not found"
    except Exception as e:
        resp['errmsg'] = str(e)

    return JsonResponse(resp)


@login_required()
def inactiveRegistrationManagerAPI(request):
    reg_data = {}
    if request.method == 'GET':
        data = request.GET
        reg_id = ''
        if 'reg_id' in data:
            reg_id = data['reg_id']
        if reg_id.isnumeric() and int(reg_id) > 0:
            reg_data = in_registrations.objects.filter(reg_id=reg_id).first()

    context = {
        'reg_data': reg_data,
    }
    return render(request, 'registration/inactive_registrations.html', context)


@login_required()
def inactiveRegSubmissionAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST
    reg_id = data.get('reg_id')

    try:
        with transaction.atomic():
            # Retrieve the in_registrations object based on reg_id
            reg_data = in_registrations.objects.get(reg_id=reg_id)
            
            # Update the fields
            reg_data.is_active = False
            reg_data.ss_modifier = request.user  # Set the user who is modifying

            reg_data.save()  # Save the changes to the database

            resp['success'] = True
            resp['msg'] = "Customer inactivated successfully"

    except in_registrations.DoesNotExist:
        resp['errmsg'] = "Registration not found"
    except Exception as e:
        resp['errmsg'] = str(e)

    return JsonResponse(resp)


@login_required()
def searchCustomerRegistrationAPI(request):
    data = []

    org_id_wise_filter = request.GET.get('org_filter', '')
    search_query = request.GET.get('query', '')

    # Initialize an empty Q object for dynamic filters
    filter_kwargs = Q()

    # Add org_id filter condition if provided
    if org_id_wise_filter:
        filter_kwargs &= Q(org_id=org_id_wise_filter)

    # Add search condition for name, customerNo, or mobileNumber
    if search_query:
        filter_kwargs &= (
            Q(full_name__icontains=search_query) |
            Q(customer_no__icontains=search_query) |
            Q(mobile_number__icontains=search_query)
        )

    # Apply filters and fetch the data
    reg_data = in_registrations.objects.filter(is_active=True).filter(filter_kwargs)

    for reg in reg_data:
        data.append({
            'reg_id': reg.reg_id,
            'customer_no': reg.customer_no,
            'full_name': reg.full_name,
            'mobile_number': reg.mobile_number,
        })

    return JsonResponse({'data': data})


@login_required()
def selectCustomerRegistrationDtlsAPI(request):
    if request.method == 'GET' and 'selectedRegister' in request.GET:
        selected_register_id = request.GET.get('selectedRegister')

        try:
            selected_register = in_registrations.objects.get(reg_id=selected_register_id)

            register_details = {
                'reg_id': selected_register.reg_id,
                'customer_no': selected_register.customer_no,
                'full_name': selected_register.full_name,
                'mobile_number': selected_register.mobile_number or '',
                'gender': selected_register.gender or '',
                'address': selected_register.address or '',
                'emergency_person': selected_register.emergency_con_name or '',
                'emergency_mobile': selected_register.emergency_con_mobile or '',
            }

            return JsonResponse({'data': register_details})
        except in_registrations.DoesNotExist:
            return JsonResponse({'error': 'Registration not found'}, status=404)
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)





    # if request.method == 'GET' and 'selectedRegisterId' in request.GET:
    #     selected_register_id = request.GET.get('selectedRegisterId')

    #     try:
    #         # Fetch the selected registration record
    #         selected_register = in_registrations.objects.get(reg_id=selected_register_id)

    #         # Prepare the registration details
    #         register_details = {
    #             'reg_id': selected_register.reg_id,
    #             'customer_no': selected_register.customer_no,
    #             'full_name': selected_register.full_name,
    #             'mobile_number': selected_register.mobile_number or '',
    #             'gender': selected_register.gender or '',
    #             'address': selected_register.address or '',
    #         }

    #         # Return the registration details as JSON
    #         return JsonResponse({'data': register_details})

    #     except in_registrations.DoesNotExist:
    #         # Return a 404 error if the registration is not found
    #         return JsonResponse({'error': 'Registration not found'}, status=404)
    
    # # Return a 400 error for invalid requests
    # return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required()
def regClientSummaryReportsAPI(request, reg_id=None):
    user = request.user
    
    if user.org_id is not None:
        # If the user has an associated organization, retrieve only that organization
        org_list = organizationlst.objects.filter(is_active=True, org_id=user.org_id).all()
    else:
        # If neither a superuser nor associated with an organization, set organizations to an empty list or handle as needed
        org_list = []

    reg_data = in_registrations.objects.filter(is_active=True, reg_id=reg_id).first()

    context = {
        'org_data': org_list,
        'reg_data': reg_data,
    }

    return render(request, 'reg_client_reports/clients_summary_report.html', context)


@login_required()
def regClientsDetailsReportsAPI(request, reg_id=None):
    user = request.user
    
    if user.org_id is not None:
        # If the user has an associated organization, retrieve only that organization
        org_list = organizationlst.objects.filter(is_active=True, org_id=user.org_id).all()
    else:
        # If neither a superuser nor associated with an organization, set organizations to an empty list or handle as needed
        org_list = []

    reg_data = in_registrations.objects.filter(is_active=True, reg_id=reg_id).first()

    context = {
        'org_data': org_list,
        'reg_data': reg_data,
    }

    return render(request, 'reg_client_reports/clients_details_report.html', context)


# get clients transaction summary
@login_required()
def getClientsTransactionsSummaryAPI(request):

    combined_data = []

    if request.method == "GET":
        reg_id = request.GET.get('reg_id')
        org_id = request.GET.get('org_id')

        # Filter credited opening transactions
        opening_credited = opening_balance.objects.filter(reg_id=int(reg_id), is_credited=True)
        if org_id and org_id.isdigit():
            opening_credited = opening_credited.filter(org_id=int(org_id))
                
        for open_cr in opening_credited:
            combined_data.append({
                'trans_id': open_cr.opb_id,
                'trans_date': open_cr.opb_date,
                'ac_head': 'Opening Credit Balance',
                'op_debit_amt': '0',
                'op_credit_amt': open_cr.opb_amount,
                'trns_debit_amt': '0',
                'trns_credit_amt': '0',
            })

        # Filter debited opening transactions
        opening_debited = opening_balance.objects.filter(reg_id=int(reg_id), is_debited=True)
        if org_id and org_id.isdigit():
            opening_debited = opening_debited.filter(org_id=int(org_id))
        for open_deb in opening_debited:
            combined_data.append({
                'trans_id': open_deb.opb_id,
                'trans_date': open_deb.opb_date,
                'ac_head': 'Opening Debit Balance',
                'op_debit_amt': open_deb.opb_amount,
                'op_credit_amt': '0',
                'trns_debit_amt': '0',
                'trns_credit_amt': '0',
            })

        # Query data from your models
        invoices = invoice_list.objects.filter(org_id=org_id, reg_id=reg_id).all()
        invoice_details = invoicedtl_list.objects.all()
        payment_details = payment_list.objects.all()
        carrying_cost_buyer = rent_others_exps.objects.filter(is_buyer=True, org_id=org_id).all()
        local_purchases = local_purchase.objects.filter(id_org=org_id, reg_id=reg_id, is_approved=True).all()
        lpdata_details = local_purchasedtl.objects.all()

        # =========================== Local Purchase ===========================
        for lp_data in local_purchases:
            # Reset grand total for each lp_data (invoice)
            grand_lp_total = 0

            lp_details = lpdata_details.filter(lp_id=lp_data).all()

            for lpdetail in lp_details:
                # Calculate the total amount for the current row
                total_amount = lpdetail.unit_price * lpdetail.lp_rec_qty

                # Calculate the discount for the current row
                dis_percent = lpdetail.dis_percentage or 0
                total_dis_percent = dis_percent / 100
                total_dis_amt = total_amount * total_dis_percent

                # Calculate the total after discount for the current row
                row_totalAmount = total_amount - total_dis_amt

                # Add to the grand total for the current lp_data
                grand_lp_total += row_totalAmount

            # Append invoice-wise data to the combined_data list
            if lp_data.is_credit and grand_lp_total > 0:
                combined_data.append({
                    'trans_id': lp_data.lp_id,
                    'trans_date': lp_data.transaction_date,
                    'ac_head': 'Local Purchase Credited (Non-Current Asset)',
                    'op_debit_amt': '0',
                    'op_credit_amt': '0',
                    'trns_debit_amt': '0',
                    'trns_credit_amt': grand_lp_total,
                })
            else:
                combined_data.append({
                    'trans_id': lp_data.lp_id,
                    'trans_date': lp_data.transaction_date,
                    'ac_head': 'Local Purchase Debited (Non-Current Asset)',
                    'op_debit_amt': '0',
                    'op_credit_amt': '0',
                    'trns_debit_amt': grand_lp_total,
                    'trns_credit_amt': grand_lp_total,
                })

        # =========================== Invoice Details ===========================
        for invoice in invoices:
            details = invoice_details.filter(inv_id=invoice).all()
            paymentsData = payment_details.filter(inv_id=invoice).all()
            cost_buyer = carrying_cost_buyer.filter(inv_id=invoice).all()

            # Initialize invoice-wise totals
            grand_total = 0
            grand_total_dis = 0
            grand_vat_tax = 0
            grand_cancel_amt = 0
            grand_total_gross_dis = 0
            total_discount_sum = 0
            total_cost_amt = 0
            grand_can_total_dis = 0
            grand_can_total_gross_dis = 0
            can_total_discount_sum = 0
            grand_can_vat_tax = 0
            total_can_net_bill = 0

            for buyer in cost_buyer:
                cost_amt = buyer.other_exps_amt
                total_cost_amt += cost_amt

            # Item rate over invoice items
            item_total = sum(detail.sales_rate * detail.qty for detail in details)
            grand_total += item_total

            # item wise Discount calculation
            item_w_dis = sum((detail.item_w_dis / detail.qty) * detail.qty for detail in details)

            grand_total_dis += item_w_dis
            grand_total_dis = round(grand_total_dis, 2)

            # cancel item wise Discount calculation
            can_item_w_dis = sum((detail.item_w_dis / detail.qty) * detail.is_cancel_qty for detail in details)

            grand_can_total_dis += can_item_w_dis
            grand_can_total_dis = round(grand_can_total_dis, 2)

            # gross Discount calculation
            total_gross_dis = sum((detail.gross_dis / detail.qty) * detail.qty for detail in details)

            grand_total_gross_dis += total_gross_dis
            grand_total_gross_dis = round(grand_total_gross_dis, 2)

            # cancel gross Discount calculation
            can_total_gross_dis = sum((detail.gross_dis / detail.qty) * detail.is_cancel_qty for detail in details)

            grand_can_total_gross_dis += can_total_gross_dis
            grand_can_total_gross_dis = round(grand_can_total_gross_dis, 2)

            # total Discount sum
            total_discount_sum = grand_total_dis + grand_total_gross_dis
            total_discount_sum = round(total_discount_sum, 2)

            # total cancel Discount sum
            can_total_discount_sum = grand_can_total_dis + grand_can_total_gross_dis
            can_total_discount_sum = round(can_total_discount_sum, 2)

            # VAT tax calculation
            item_wise_total_vat_tax = sum((detail.gross_vat_tax / detail.qty) * detail.qty for detail in details)

            grand_vat_tax += item_wise_total_vat_tax
            grand_vat_tax = round(grand_vat_tax, 2)

            # cancel VAT tax calculation
            can_item_wise_total_vat_tax = sum((detail.gross_vat_tax / detail.qty) * detail.is_cancel_qty for detail in details)

            grand_can_vat_tax += can_item_wise_total_vat_tax
            grand_can_vat_tax = round(grand_can_vat_tax, 2)

            # Cancel amount calculation
            total_item_cancel_amt = sum(detail.sales_rate * detail.is_cancel_qty for detail in details)
            grand_cancel_amt += total_item_cancel_amt

            # Calculate total net bill for this invoice
            total_net_bill = ((grand_total + grand_vat_tax + total_cost_amt) - total_discount_sum)
            total_net_bill = round(total_net_bill, 2)

            # Calculate total cancel net bill for this invoice
            total_can_net_bill = ((grand_cancel_amt + grand_can_vat_tax) - can_total_discount_sum)
            total_can_net_bill = round(total_can_net_bill, 2)

            # Append invoice-wise data to the combined_data list
            combined_data.append({
                'trans_id': invoice.inv_id,
                'trans_date': invoice.invoice_date,
                'ac_head': 'Sales (Non-Current Asset)',
                'op_debit_amt': '0',
                'op_credit_amt': '0',
                'trns_debit_amt': total_net_bill,
                'trns_credit_amt': '0',
            })

            if total_can_net_bill > 0:
                combined_data.append({
                    'trans_id': invoice.inv_id,
                    'trans_date': invoice.invoice_date,
                    'ac_head': 'Sales Return (Non-Current Asset)',
                    'op_debit_amt': '0',
                    'op_credit_amt': '0',
                    'trns_debit_amt': '0',
                    'trns_credit_amt': total_can_net_bill,
                })

            for payment in paymentsData:
                if payment.collection_mode == "1":
                    combined_data.append({
                            'trans_id': payment.inv_id.inv_id,
                            'trans_date': payment.pay_date,
                            'ac_head': 'Sales Collection (Non-Current Asset)',
                            'op_debit_amt': '0',
                            'op_credit_amt': '0',
                            'trns_debit_amt': '0',
                            'trns_credit_amt': payment.pay_amt, 
                        })

                elif payment.collection_mode == "2":
                    combined_data.append({
                            'trans_id': payment.inv_id.inv_id,
                            'trans_date': payment.pay_date,
                            'ac_head': 'Sales Due Collection (Non-Current Asset)',
                            'op_debit_amt': '0',
                            'op_credit_amt': '0',
                            'trns_debit_amt': '0',
                            'trns_credit_amt': payment.pay_amt,
                            
                        })
                    
                elif payment.collection_mode == "3":
                    combined_data.append({
                            'trans_id': payment.inv_id.inv_id,
                            'trans_date': payment.pay_date,
                            'ac_head': 'Sales Collection Refunded (Non-Current Asset)',
                            'op_debit_amt': '0',
                            'op_credit_amt': '0',
                            'trns_debit_amt': payment.pay_amt,
                            'trns_credit_amt': '0',
                        })
        

        data = {
            'combined_data': combined_data,
        }
        return JsonResponse(data, safe=False)

    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)
    

# get clients transaction Details
@login_required()
def getClientsTransactionsDetailsAPI(request):
    try:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            reg_id = request.GET.get('reg_id')
            org_id = request.GET.get('org_id')

            if not reg_id or not reg_id.isdigit():
                return JsonResponse({'error': 'Invalid or missing reg_id'}, status=400)

            data = []

            local_purchases = local_purchase.objects.filter(id_org=org_id, reg_id=reg_id, is_approved=True).all()
            lpdata_details = local_purchasedtl.objects.all()
            # Filter credited opening transactions
            opening_credited = opening_balance.objects.filter(reg_id=int(reg_id), is_credited=True)
            if org_id and org_id.isdigit():
                opening_credited = opening_credited.filter(org_id=int(org_id))
                
            for open_cr in opening_credited:
                data.append({
                    'trans_id': open_cr.opb_id,
                    'trans_date': open_cr.opb_date,
                    'ac_head': 'Opening Credit Balance',
                    'description': open_cr.descriptions,
                    'op_debit_amt': '0',
                    'op_credit_amt': open_cr.opb_amount,
                    'trns_debit_amt': '0',
                    'trns_credit_amt': '0',
                })

            # Filter debited opening transactions
            opening_debited = opening_balance.objects.filter(reg_id=int(reg_id), is_debited=True)
            if org_id and org_id.isdigit():
                opening_debited = opening_debited.filter(org_id=int(org_id))
            for open_deb in opening_debited:
                data.append({
                    'trans_id': open_deb.opb_id,
                    'trans_date': open_deb.opb_date,
                    'ac_head': 'Opening Debit Balance',
                    'description': open_deb.descriptions,
                    'op_debit_amt': open_deb.opb_amount,
                    'op_credit_amt': '0',
                    'trns_debit_amt': '0',
                    'trns_credit_amt': '0',
                })


            # =========================== Local Purchase ===========================
            for lp_data in local_purchases:
                # Reset grand total for each lp_data (invoice)
                grand_lp_total = 0
                pur_details = []

                lp_details = lpdata_details.filter(lp_id=lp_data).all()

                for lpdetail in lp_details:
                    
                    pur_details.append({
                            'item_id': lpdetail.item_id.item_id,
                            'item_name': lpdetail.item_id.item_name,
                            'sales_rate': lpdetail.unit_price,
                            'qty': lpdetail.lp_rec_qty,
                            'dis_perc': lpdetail.dis_percentage if lpdetail.dis_percentage else 0,
                        })

                    # Calculate the total amount for the current row
                    total_amount = lpdetail.unit_price * lpdetail.lp_rec_qty

                    # Calculate the discount for the current row
                    dis_percent = lpdetail.dis_percentage or 0
                    total_dis_percent = dis_percent / 100
                    total_dis_amt = total_amount * total_dis_percent

                    # Calculate the total after discount for the current row
                    row_totalAmount = total_amount - total_dis_amt

                    # Add to the grand total for the current lp_data
                    grand_lp_total += row_totalAmount

                # Append invoice-wise data to the combined_data list
                if lp_data.is_credit and grand_lp_total > 0:
                    data.append({
                        'trans_id': lp_data.lp_id,
                        'trans_date': lp_data.transaction_date,
                        'ac_head': 'Local Purchase Credited (Non-Current Asset)',
                        'op_debit_amt': '0',
                        'op_credit_amt': '0',
                        'trns_debit_amt': '0',
                        'trns_credit_amt': grand_lp_total,
                        'details_data': pur_details,
                    })
                else:
                    data.append({
                        'trans_id': lp_data.lp_id,
                        'trans_date': lp_data.transaction_date,
                        'ac_head': 'Local Purchase Debited (Non-Current Asset)',
                        'op_debit_amt': '0',
                        'op_credit_amt': '0',
                        'trns_debit_amt': grand_lp_total,
                        'trns_credit_amt': grand_lp_total,
                        'details_data': pur_details,
                    })
                # =========================== Local Purchase end ===========================

            # Fetching invoice_list based on reg_id
            invoice_datas = invoice_list.objects.filter(reg_id=int(reg_id))

            if org_id and org_id.isdigit():
                invoice_datas = invoice_datas.filter(org_id_id=int(org_id))

            for invoice in invoice_datas:
                payment_details = payment_list.objects.filter(inv_id=invoice)
                sales_details = invoicedtl_list.objects.filter(inv_id=invoice)
                other_expense = rent_others_exps.objects.filter(inv_id=invoice, is_buyer=True)

                # Initialize totals
                grand_sale_amt = 0
                grand_total_dis = 0
                grand_total_gross_dis = 0
                grand_vat_tax = 0
                grand_cancel_amt = 0
                tot_buyer_carryin_cost = 0
                grand_total_net_bill = 0
                grand_total_can_net_bill = 0
                grand_total_can_dis = 0
                grand_total_can_gross_dis = 0
                grand_can_vat_tax = 0

                # Calculate other expenses
                for other_exp in other_expense:
                    tot_buyer_carryin_cost += other_exp.other_exps_amt

                # Collect unique item_ids and their names
                details_data = []
                cancel_details = []

                for sales in sales_details:
                    # Update unique item count
                    details_data.append({
                        'item_id': sales.item_id.item_id,
                        'item_name': sales.item_id.item_name,
                        'sales_rate': sales.sales_rate,
                        'qty': sales.qty,
                    })

                    if sales.is_cancel_qty > 0:
                        cancel_details.append({
                            'item_id': sales.item_id.item_id,
                            'item_name': sales.item_id.item_name,
                            'sales_rate': sales.sales_rate,
                            'qty': sales.is_cancel_qty,
                        })

                    # Calculate sale amount
                    grand_sale_amt += sales.qty * sales.sales_rate

                    # Calculate item-wise discount
                    grand_total_dis += sales.item_w_dis

                    # Calculate item-wise cancel discount
                    grand_total_can_dis += (sales.item_w_dis / sales.qty) * sales.is_cancel_qty

                    # Calculate total gross discount
                    grand_total_gross_dis += sales.gross_dis

                    # Calculate total cancel gross discount
                    grand_total_can_gross_dis += (sales.gross_dis / sales.qty) * sales.is_cancel_qty

                    # Calculate total VAT tax
                    grand_vat_tax += sales.gross_vat_tax

                    # Calculate total cancel VAT tax
                    grand_can_vat_tax += (sales.gross_vat_tax / sales.qty) * sales.is_cancel_qty

                    # Calculate total cancel amount
                    grand_cancel_amt += sales.sales_rate * sales.is_cancel_qty

                # Count total unique items for this invoice
                item_count = len(sales_details)

                # Calculate total net bill for this invoice
                total_net_bill = (
                    (grand_sale_amt + grand_vat_tax + tot_buyer_carryin_cost) -
                    (grand_total_dis + grand_total_gross_dis)
                )
                grand_total_net_bill = round(total_net_bill, 2)

                # Calculate total cancel net bill for this invoice
                total_can_net_bill = (
                    (grand_cancel_amt + grand_can_vat_tax) -
                    (grand_total_can_dis + grand_total_can_gross_dis)
                )
                grand_total_can_net_bill = round(total_can_net_bill, 2)

                data.append({
                    'trans_id': invoice.inv_id,
                    'trans_date': invoice.invoice_date,
                    'item_count': item_count,
                    'ac_head': 'Sales (Non-Current Asset)',
                    'op_debit_amt': '0',
                    'op_credit_amt': '0',
                    'trns_debit_amt': grand_total_net_bill,
                    'trns_credit_amt': '0',
                    'details_data': details_data,
                })

                if grand_total_can_net_bill > 0:
                    data.append({
                        'trans_id': invoice.inv_id,
                        'trans_date': invoice.invoice_date,
                        'item_count': item_count,
                        'ac_head': 'Sales Return (Non-Current Asset)',
                        'op_debit_amt': '0',
                        'op_credit_amt': '0',
                        'trns_debit_amt': '0',
                        'trns_credit_amt': grand_total_can_net_bill,
                        'details_data': cancel_details,
                    })

                # Append payment details
                for payment in payment_details:
                    if payment.collection_mode == "1":
                        data.append({
                            'trans_id': payment.inv_id.inv_id,
                            'trans_date': payment.pay_date,
                            'ac_head': 'Sales Collection (Non-Current Asset)',
                            'op_debit_amt': '0',
                            'op_credit_amt': '0',
                            'trns_debit_amt': '0',
                            'trns_credit_amt': payment.pay_amt,
                        })

                    elif payment.collection_mode == "2":
                        data.append({
                            'trans_id': payment.inv_id.inv_id,
                            'trans_date': payment.pay_date,
                            'ac_head': 'Sales Due Collection (Non-Current Asset)',
                            'op_debit_amt': '0',
                            'op_credit_amt': '0',
                            'trns_debit_amt': '0',
                            'trns_credit_amt': payment.pay_amt,
                        })

                    elif payment.collection_mode == "3":
                        data.append({
                            'trans_id': payment.inv_id.inv_id,
                            'trans_date': payment.pay_date,
                            'ac_head': 'Sales Collection Refunded (Non-Current Asset)',
                            'op_debit_amt': '0',
                            'op_credit_amt': '0',
                            'trns_debit_amt': payment.pay_amt,
                            'trns_credit_amt': '0',
                        })

            return JsonResponse(data, safe=False)

        return JsonResponse({'error': 'Invalid request'}, status=400)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)





















    