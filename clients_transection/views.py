import sys
import json
from django.db.models import Q, F, Sum, ExpressionWrapper, fields, FloatField, IntegerField, Case, When, Value, CharField
from django.db import transaction
from datetime import date, datetime
from collections import defaultdict
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
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
from registrations.models import in_registrations
from bank_statement.models import cash_on_hands
from . models import opening_balance, paymentsdtls
from supplier_setup.models import suppliers
from organizations.models import branchslist, organizationlst
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def openingBalanceManagerAPI(request):
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

    return render(request, 'clients_transection/add_opening_balance.html', context)


# get registration list
@login_required()
def getRegistrationsListAPI(request):
    search_query = request.GET.get('search_query', '')
    org_id_wise_filter = request.GET.get('org_filter', '')

    # Initialize an empty Q object for dynamic filters
    filter_kwargs = Q()

    # Add search conditions only if search_query is not empty
    if search_query:
        filter_kwargs |= Q(full_name__icontains=search_query) | Q(customer_no__icontains=search_query) | Q(mobile_number__icontains=search_query)

    # Add org_id filter condition only if org_id_wise_filter is not empty
    if org_id_wise_filter:
        filter_kwargs &= Q(org_id=org_id_wise_filter)

    # Apply filter_kwargs to the query
    reg_data = in_registrations.objects.filter(is_active=True).filter(filter_kwargs)

    data = []
    for reg in reg_data:
        data.append({
            'reg_id': reg.reg_id,
            'customer_no': reg.customer_no,
            'full_name': reg.full_name,
            'mobile_number': reg.mobile_number,
        })

    return JsonResponse({'data': data})


# registration value click to show
@login_required()
def selectRegistrationListAPI(request, reg_id):

    try:
        reg_list = get_object_or_404(in_registrations, reg_id=reg_id)

        regis_Dtls = []

        regis_Dtls.append({
            'reg_id': reg_list.reg_id,
            'customer_no': reg_list.customer_no,
            'mobile_number': reg_list.mobile_number,
            'full_name': reg_list.full_name,
            'address': reg_list.address,
            'gender': reg_list.gender,
            'marital_status': reg_list.marital_status,
            'blood_group': reg_list.blood_group,
            'dateofbirth': reg_list.dateofbirth,
        })

        context = {
            'regis_Dtls': regis_Dtls,
        }

        return JsonResponse(context)
    except Exception as e:
        return JsonResponse({'error': str(e)})
    

# opening balance transaction add view
@login_required()
def saveOpBalanceTransactionAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST
    org_id=data.get('filter_org')
    reg_id=data.get('reg_id')
    is_debited=data.get('is_debited', False)
    is_credited=data.get('is_credited', False)
    op_amount = data.get('op_amount')
    descriptions = data.get('descriptions')

    try:
        org_instance = organizationlst.objects.get(org_id=org_id)
    except organizationlst.DoesNotExist:
        resp['errmsg'] = 'Organization not found'
        return JsonResponse(resp)

    try:
        reg_instance = in_registrations.objects.get(reg_id=reg_id)
    except in_registrations.DoesNotExist:
        resp['errmsg'] = 'Registration not found'
        return JsonResponse(resp)

    opb_trans = opening_balance(
        org_id=org_instance,
        reg_id=reg_instance,
        opb_amount=op_amount,
        is_debited=is_debited,
        is_credited=is_credited,
        descriptions=descriptions,
        ss_creator = request.user,
        ss_modifier = request.user,
    )
    opb_trans.save()

    resp = {'success': True, 'msg': 'Saved successfully'}

    return JsonResponse(resp)


@login_required()
def getOpeningBalancesAmountAPI(request):
    if request.method == "GET":
        # Get the organization and registration IDs from the query parameters
        org_id = request.GET.get('org_id')
        reg_id = request.GET.get('reg_id')

        # Filter the opening balances based on org_id and reg_id
        opening_balances = opening_balance.objects.all()

        if org_id:
            opening_balances = opening_balances.filter(org_id=org_id)

        if reg_id:
            opening_balances = opening_balances.filter(reg_id=reg_id)

        # Retrieve the values to return
        opening_balances = opening_balances.values(
            'opb_id',
            'opb_date',
            'org_id',
            'reg_id',
            'is_debited',
            'is_credited',
            'descriptions',
            'opb_amount',
        )
        
        data = list(opening_balances)  # Convert queryset to a list of dictionaries
        return JsonResponse(data, safe=False)
    

@login_required()
def deleteopeningBalancesDetailsModalAPI(request):
    opb_data = {}
    if request.method == 'GET':
        data = request.GET
        opb_id = ''
        if 'opb_id' in data:
            opb_id = data['opb_id']
        if opb_id.isnumeric() and int(opb_id) > 0:
            opb_data = opening_balance.objects.filter(opb_id=opb_id).first()

    context = {
        'opb_data': opb_data,
    }
    return render(request, 'clients_transection/delete_confirmation.html', context)
    

@method_decorator(csrf_exempt, name='dispatch')
@require_http_methods(["DELETE"])
def openingBalancesDetailsDeleteAPI(request, opb_id):
    if request.method == 'DELETE':
        try:
            # Get all the matching chalan details
            opening_DtlIDs = opening_balance.objects.filter(opb_id=opb_id)
            if opening_DtlIDs.exists():
                # Delete the current opening_DtlIDs entry
                opening_DtlIDs.delete()
                return JsonResponse({'success': True, 'msg': 'Successfully deleted'})
            else:
                return JsonResponse({'success': False, 'errmsg': f'Opening Balance details with ID {opb_id} not found.'})
        except Exception as e:
            return JsonResponse({'success': False, 'errmsg': f'Error occurred: {str(e)}'})
    

# ===================================== Reg clients payments =====================================

@login_required()
def regClientsPaymentManagerAPI(request):
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

    return render(request, 'reg_client_payment/reg_clients_payment.html', context)

# save payment data
@login_required()
def saveregClientsPaymentTransactionAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST
    org_id=data.get('filter_org')
    branch_id=data.get('branch_id')
    reg_id=data.get('reg_id')
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
        reg_instance = in_registrations.objects.get(reg_id=reg_id)
    except in_registrations.DoesNotExist:
        resp['errmsg'] = 'Registration not found'
        return JsonResponse(resp)

    pay_trans = paymentsdtls(
        org_id=org_instance,
        branch_id=branch_instance,
        reg_id=reg_instance,
        is_reg_client=True,
        is_supplier_party=False,
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

# get payment dtls
@login_required()
def getpaymentDtlsDataAPI(request):

    if request.method == "GET":
        # Get the organization and registration IDs from the query parameters
        org_id = request.GET.get('org_id')
        reg_id = request.GET.get('reg_id')
        start_date_filter = request.GET.get('start_date', '').strip()
        end_date_filter = request.GET.get('end_date', '').strip()

        # Filter the opening balances based on org_id and reg_id
        paymentDtls = paymentsdtls.objects.filter(is_reg_client=True).all()

        if org_id:
            paymentDtls = paymentDtls.filter(org_id=org_id)

        if reg_id:
            paymentDtls = paymentDtls.filter(reg_id=reg_id)

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


@login_required()
def deletepaymentDetailsModalAPI(request):
    pay_data = {}
    if request.method == 'GET':
        data = request.GET
        pay_id = ''
        if 'pay_id' in data:
            pay_id = data['pay_id']
        if pay_id.isnumeric() and int(pay_id) > 0:
            pay_data = paymentsdtls.objects.filter(pay_id=pay_id).first()

    context = {
        'pay_data': pay_data,
    }
    return render(request, 'reg_client_payment/delete_confirmation.html', context)


@method_decorator(csrf_exempt, name='dispatch')
@require_http_methods(["DELETE"])
def paymentDetailsDeleteAPI(request, pay_id):
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
        payment_Dtl = paymentsdtls.objects.filter(pay_id=pay_id).first()

        if not payment_Dtl:
            return JsonResponse({'success': False, 'errmsg': f'Payments details with ID {pay_id} not found.'}, status=404)

        # Retrieve values before deletion
        pay_mode = payment_Dtl.pay_mode
        pay_amount = payment_Dtl.pay_amount
        pay_date = payment_Dtl.pay_date
        present_date = date.today()
        
        if present_date == pay_date:
            # Handle cash payment case
            if pay_mode == "1" and pay_amount:  # Assuming "1" represents cash payments
                cashOnHands, created = cash_on_hands.objects.get_or_create(
                    org_id=org_id,
                    branch_id=branch_id,
                    defaults={'on_hand_cash': 0}
                )

                # Update the on_hand_cash value
                cashOnHands.on_hand_cash = F('on_hand_cash') + pay_amount
                cashOnHands.save(update_fields=['on_hand_cash'])

            # Delete the payment record
            payment_Dtl.delete()

            return JsonResponse({'success': True, 'msg': 'Successfully deleted'})
        else:
            return JsonResponse({'success': False, 'errmsg': 'Only Present Date Payment Transaction Can Be Deleted...'}, status=400)

    except Exception as e:
        return JsonResponse({'success': False, 'errmsg': f'Error occurred: {str(e)}'}, status=500)