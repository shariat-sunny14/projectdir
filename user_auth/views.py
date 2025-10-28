import json
import sys
import pytz
import logging
import calendar
from decimal import Decimal
from .forms import UserLoginForm
from django.contrib import messages
from collections import defaultdict
from django.utils import timezone
from django.utils.timezone import now
from datetime import date, datetime, timedelta
from django_ratelimit.decorators import ratelimit
from django.contrib.sessions.models import Session
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, HttpResponseRedirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.db.models import Q, ExpressionWrapper, F, FloatField, Sum, Count
from module_setup.models import module_type, module_list, feature_list
from user_setup.models import access_list, serviceChargePayment
from organizations.models import organizationlst
from django.http import HttpResponseNotFound
from .decorators import login_required_with_timeout
from stock_list.models import in_stock, stock_lists
from item_pos.models import invoice_list, invoicedtl_list, payment_list, rent_others_exps
from jarvis_assistant.views import export_voice_commands
from user_auth.utils.save_user_context import save_user_context_to_json
from user_auth.utils.save_navbar_context import save_navbar_json_for_user
from user_auth.utils.save_service_charge_context import save_org_service_charge_to_json
from user_auth.utils.notification_data_context import save_notification_data_json
from item_setup.models import items
from . models import SystemShutdown
from login_theme.models import login_themes
from django.contrib.auth import get_user_model
User = get_user_model()


def ratelimited_view(request, exception):
    return JsonResponse({'success': False, 'errmsg': 'Too many requests. Please try again later.'}, status=429)

# login page render
def user_loginManagerAPI(request):

    # Retrieve the latest login theme, or use a default if none exists
    logintheme = login_themes.objects.all()
    
    if logintheme.exists():
        latest_theme = logintheme.latest('login_theme_id')
        login_template = f'logger/{latest_theme.login_theme_name}.html' if latest_theme.login_theme_name else 'logger/login_theme1.html'
    else:
        login_template = 'logger/login_theme1.html'

    # Set the timezone to Dhaka
    dhaka_tz = pytz.timezone('Asia/Dhaka')
    present_time = timezone.now().astimezone(dhaka_tz).date()  # Convert to date for sys_validity check

    # Retrieve the latest SystemShutdown record for sys_validity check
    sys_expiry = SystemShutdown.objects.order_by('-sys_id').first()
    
    # Check if sys_validity is set and has not expired
    if sys_expiry and sys_expiry.sys_validity and present_time > sys_expiry.sys_validity:
        return render(request, 'sys_shut_down/sys_validity.html')

    # Retrieve the first active system shutdown record for is_sys_shut_down=True
    shutdown_data = SystemShutdown.objects.filter(is_sys_shut_down=True).order_by('-sys_id').first()

    # If there is an active shutdown, check if the down-time validity has passed
    if shutdown_data:
        present_time_datetime = timezone.now().astimezone(dhaka_tz)  # Get the current datetime for comparison
        if present_time_datetime > shutdown_data.sys_down_time_validity:
            return render(request, login_template)
        else:
            return render(request, 'sys_shut_down/sys_shut_down.html')

    # Default to the login page if no active shutdown or valid condition is met
    return render(request, login_template)


# organization data informations
def fetch_organizations(request):
    if request.method == 'POST':
        username = request.POST.get('username')

        # Fetch the user object
        try:
            user = User.objects.get(username__iexact=username)
        except User.DoesNotExist:
            return JsonResponse({'organizations': []})

        # Check if the user has an org_id
        if user.org_id:
            # Fetch organizations based on the user's org_id
            organizations = organizationlst.objects.filter(org_id=user.org_id, is_active=True).values('org_id', 'org_name')

            if organizations.exists():
                organizations_list = list(organizations)
                return JsonResponse({'organizations': organizations_list})
        
        return JsonResponse({'organizations': []})

    return JsonResponse({'error': 'Invalid request'})


# checked user is authenticated or not
def check_session_status(request):
    # Session expired is or not
    if not request.user.is_authenticated:
        return JsonResponse({'is_authenticated': False})

    expiry_age = request.session.get_expiry_age()
    expiry_date = request.session.get_expiry_date()
    is_expired = expiry_age <= 0 or now() > expiry_date

    if is_expired:
        # Forcefully clear session if expired
        request.session.flush()
        return JsonResponse({'is_authenticated': False})
    
    return JsonResponse({'is_authenticated': True})


def getBlockedWithoutServiceChargePayment(request):
    
    return render(request, 'service_charge_payment/service_charge_date_over.html')

# List of months for service charge payment validation
MONTHS_LIST = [
    'january', 'february', 'march', 'april', 'may', 'june',
    'july', 'august', 'september', 'october', 'november', 'december'
]

# system log in function
@csrf_protect
@ratelimit(key='user', rate='100/m', method='POST', block=True)
def user_loginAPI(request):
    resp = {'success': False, 'errmsg': 'Invalid Username and Password. Please Try Again.'}
    today = date.today()

    if request.method == 'POST':
        logout(request)

        username = request.POST.get('username')
        password = request.POST.get('password')
        org_name = request.POST.get('org_name')

        try:
            user = User.objects.get(username__iexact=username)
        except User.DoesNotExist:
            return JsonResponse(resp)

        if user and user.check_password(password):
            try:
                organization = organizationlst.objects.get(org_id=org_name)

                if user.org_id != organization.org_id:
                    return JsonResponse({'success': False, 'errmsg': 'Invalid Organization.'})

                if user.expiry_date and user.expiry_date < today:
                    return JsonResponse({'success': False, 'errmsg': 'User Account Expired. Please Contact Administrator.'})

                if not user.is_active:
                    return JsonResponse({'success': False, 'errmsg': 'User Account is Inactive. Please Contact Administrator.'})

                # Only for normal users (not superusers)
                if not user.is_superuser:
                    is_start_up = organization.is_start_up
                    is_alert_end = organization.is_alert_end or 1

                    # Build alert_end_date
                    alert_day = min(is_alert_end, calendar.monthrange(today.year, today.month)[1])
                    alert_end_date = date(today.year, today.month, alert_day)

                    if today > alert_end_date:
                        if not is_start_up:
                            return JsonResponse({
                                'success': False,
                                'errmsg': 'Startup date not configured.',
                                'redirect_url': '/get_blocked_without_service_charge_payment/'
                            })

                        # Calculate months from is_start_up to previous month of today
                        prev_month = today.replace(day=1) - timedelta(days=1)
                        pointer = is_start_up.replace(day=1)
                        required_months = []
                        while pointer <= prev_month:
                            required_months.append((pointer.year, MONTHS_LIST[pointer.month - 1].lower()))
                            pointer = (pointer.replace(day=28) + timedelta(days=4)).replace(day=1)

                        # Get all service payments for this org
                        all_payments = serviceChargePayment.objects.filter(
                            org_id=organization,
                            service_year__isnull=False,
                            service_month__isnull=False
                        )

                        if not all_payments.exists():
                            return JsonResponse({
                                'success': False,
                                'errmsg': 'No service charge payments found.',
                                'redirect_url': '/get_blocked_without_service_charge_payment/'
                            })

                        # Filter approved or passed payments
                        approved_or_passing = all_payments.filter(Q(is_approved=True) | Q(is_passing=True))

                        # Normalize paid months
                        paid_months = set(
                            (int(p.service_year), p.service_month.strip().lower())
                            for p in approved_or_passing
                            if p.service_year and p.service_month
                        )

                        # Detect unpaid months
                        missing_months = [m for m in required_months if m not in paid_months]

                        if missing_months:
                            return JsonResponse({
                                'success': False,
                                'errmsg': 'Missing approved or passed service charge for some months.',
                                'redirect_url': '/get_blocked_without_service_charge_payment/'
                            })

                        # All required months are paid (approved or passed)

                # Login success
                user.is_login_status = True
                user.save()
                login(request, user)

                # Optional helpers
                save_user_context_to_json(user)
                save_navbar_json_for_user(user)
                save_org_service_charge_to_json(user)
                # export_voice_commands()
                save_notification_data_json()

                return JsonResponse({'success': True, 'msg': 'Login Successful.', 'redirect_url': '/accounts/profile/'})

            except organizationlst.DoesNotExist:
                return JsonResponse({'success': False, 'errmsg': 'Organization not found.'})

    return JsonResponse(resp)


@csrf_exempt
def get_blocked_service_data_public(request):
    org_id = request.GET.get('org_name') or request.POST.get('org_name')
    if not org_id:
        return render(request, 'page_notFound/page_not_found.html')

    org = get_object_or_404(organizationlst, org_id=org_id, is_active=True)

    is_start_up = org.is_start_up
    service_charge = org.service_charge or 0
    is_alert_start = org.is_alert_start or 1
    is_alert_end = org.is_alert_end or 1
    today = date.today()

    current_year, current_month = today.year, today.month
    alert_start_date = date(current_year, current_month, min(is_alert_start, calendar.monthrange(current_year, current_month)[1]))
    next_month = 1 if current_month == 12 else current_month + 1
    next_year = current_year + 1 if current_month == 12 else current_year
    alert_end_date = date(next_year, next_month, min(is_alert_end, calendar.monthrange(next_year, next_month)[1]))

    remaining_alert_days = max((alert_end_date - today).days, 0)

    unpaid_months = []
    paid_months = set()
    due_amount = 0
    total_months = 0

    if is_start_up:
        current_pointer = date(is_start_up.year, is_start_up.month, 1)
        last_pointer = date(today.year, today.month, 1)
        all_months = []

        while current_pointer <= last_pointer:
            y = current_pointer.year
            m = current_pointer.month
            all_months.append((y, MONTHS_LIST[m - 1]))
            current_pointer = date(y + 1, 1, 1) if m == 12 else date(y, m + 1, 1)

        total_months = len(all_months)

        paid_records = serviceChargePayment.objects.filter(
            org_id=org, is_approved=True,
            service_year__isnull=False,
            service_month__isnull=False
        )
        for p in paid_records:
            paid_months.add((int(p.service_year), p.service_month.lower().strip()))

        unpaid_months = [m for m in all_months if m not in paid_months]
        due_amount = len(unpaid_months) * service_charge

    return JsonResponse({
        'success': True,
        'is_start_up_date': is_start_up.strftime('%d %B %Y') if is_start_up else None,
        'service_charge': service_charge,
        'due_amount': due_amount,
        'is_alert_start': alert_start_date.strftime('%d %B %Y'),
        'is_alert_end': alert_end_date.strftime('%d %B %Y'),
        'remaining_alert_days': remaining_alert_days,
        'total_months': total_months,
        'paid_months': list(paid_months),
        'unpaid_months': unpaid_months,
    })

@login_required_with_timeout
def main_dashboard(request):
    
    return render(request, 'main_dashboard/main_dashboard.html')

@login_required()
def logoutuser(request):
    # Fetch the current user
    current_user = request.user

    # Update the user's login status to False upon logout
    if current_user.is_authenticated:
        current_user.is_login_status = False
        current_user.save()

    logout(request)
    messages.success(request, 'Logout success!')
    return redirect('login')

@login_required
def logout_all_users(request):
    current_user = request.user

    # Update the user's login status to False upon logout
    if current_user.is_authenticated:
        current_user.is_login_status = False
        current_user.save()

    # Store the current user's session key to avoid deleting it prematurely
    current_session_key = request.session.session_key

    # Fetch all active sessions except the current user's
    sessions = Session.objects.filter(expire_date__gte=timezone.now()).exclude(session_key=current_session_key)

    # Log out all other users by updating their is_login_status and deleting their sessions
    for session in sessions:
        data = session.get_decoded()
        user_id = data.get('_auth_user_id')

        if user_id:
            try:
                # Use 'user_id' instead of 'id'
                user = User.objects.get(user_id=user_id)  # Reference user_id directly
                user.is_login_status = False  # Update login status
                user.save()
            except User.DoesNotExist:
                continue

    # Delete all other sessions
    sessions.delete()
    
    # Create or update the SystemShutdown record
    dhaka_tz = pytz.timezone('Asia/Dhaka')

    # Get the current time in Dhaka timezone
    current_time_dhaka = timezone.now().astimezone(dhaka_tz)

    # Create or update the record
    system_shutdown, created = SystemShutdown.objects.get_or_create(
        sys_id=334455560000,  # Use a predefined ID for the unique record
        defaults={
            'sys_down_time_validity': current_time_dhaka + timezone.timedelta(hours=6),  # Set to 6 hours later
            'is_sys_shut_down': True,
            'ss_creator': current_user
        }
    )

    # If the record already exists, update it
    if not created:
        system_shutdown.sys_down_time_validity = current_time_dhaka + timezone.timedelta(hours=6)  # Update to 6 hours later
        system_shutdown.is_sys_shut_down = True
        system_shutdown.ss_modifier = current_user
        system_shutdown.save()

    # Log out the current user properly
    logout(request)

    # Success message and redirect
    messages.success(request, 'All users, including yourself, have been logged out successfully!')
    return redirect('login')


@login_required()
def statisticsManagerAPI(request):
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

    return render(request, 'statistics/statistics.html', context)

@login_required()
def get_total_itemsManagerAPI(request):

    total_items_count = items.objects.filter(is_active=True).count()

    data = {'total_items_count': total_items_count}

    return JsonResponse(data)

@login_required()
def getConsumptionManagerAPI(request):
    static_start = 0
    static_end = 0
    if request.method == "POST":
        today = date.today()
        sales_total_qty = 0

        static_start = request.POST.get('static_start')
        static_end = request.POST.get('static_end')

        # Parse the dates from the request POST data
        static_start = datetime.strptime(static_start, '%Y-%m-%d').date()
        static_end = datetime.strptime(static_end, '%Y-%m-%d').date()
        
        # Fetch all invoices for the specified date range
        invoices = invoice_list.objects.filter(invoice_date__range=(static_start, static_end)).all()
        
        # Calculate total sales quantity for each invoice
        for inv in invoices:
            invoice_details = invoicedtl_list.objects.filter(inv_id=inv).all()
            total_qty = invoice_details.aggregate(
                total_qty=Sum(ExpressionWrapper(F('qty') - F('is_cancel_qty'), output_field=FloatField()))
            )['total_qty'] or 0
            
            # Accumulate the total sales quantity
            sales_total_qty += total_qty

        data = {'sales_total_qty': sales_total_qty}

        return JsonResponse(data)
    
    # Return an empty response if the request method is not 'POST'
    return JsonResponse({'message': 'Invalid request method'}, status=200)


@login_required()
def storeWiseStockQtyManagerAPI(request):
    store_id = request.GET.get('store_id', None)  # Get store_id from the request
    
    # Initialize item_quantities as an empty list
    item_quantities = []

    if store_id:
        # Filter based on the selected store
        item_quantities = in_stock.objects.filter(store_id=store_id).values('item_id__item_name').annotate(total_quantity=Sum('stock_qty'))

    labels = []
    sizes = []

    # Only process item_quantities if it contains data
    for item_quantity in item_quantities:
        item_name = item_quantity['item_id__item_name']  # Get item name
        quantity = item_quantity['total_quantity']  # Get stock quantity for this item
        labels.append(item_name)
        sizes.append(quantity)

    data = {
        'labels': labels,
        'sizes': sizes,
    }

    return JsonResponse(data)


@login_required()
def getDetailsSalesManagerAPI(request):
    static_start = 0
    static_end = 0
    if request.method == "POST":
        today = datetime.now().date()
        invoice_timestamps = defaultdict(set)  # Store timestamps for each inv_id
        details_sales_amt = []

        static_start = request.POST.get('static_start')
        static_end = request.POST.get('static_end')

        # Parse the dates from the request POST data
        static_start = datetime.strptime(static_start, '%Y-%m-%d').date()
        static_end = datetime.strptime(static_end, '%Y-%m-%d').date()

        # Fetch all invoices for today
        invoices = invoice_list.objects.filter(invoice_date__range=(static_start, static_end)).all()

        # Calculate total sales quantity for each invoice
        for inv in invoices:
            invoice_details = invoicedtl_list.objects.filter(inv_id=inv).all()
            total_sales_amt = 0
            timestamps = set()  # Store timestamps for the current inv_id
            for detail in invoice_details:
                # Convert the UTC time to local time zone
                local_time = timezone.localtime(detail.ss_created_on)
                
                # Retrieve timestamp_field and format it to display only time
                timestamp = local_time.strftime('%I.%M %p')  # Format time as '12.15 AM'
                timestamps.add(timestamp)

                # Calculate sales amount per detail and accumulate in total_sales_amt
                sales_amt = (detail.qty - detail.is_cancel_qty) * detail.sales_rate
                total_sales_amt += sales_amt

            # Store timestamps for the current inv_id
            invoice_timestamps[inv.inv_id] = timestamps
            
            # Append total sales amount for the invoice after processing all details
            details_sales_amt.append(total_sales_amt)

        # Flatten the timestamps for each inv_id
        timestamps = [timestamp for timestamps_set in invoice_timestamps.values() for timestamp in timestamps_set]

        data = {'timestamps': timestamps, 'details_sales_amt': details_sales_amt}

        return JsonResponse(data)
    
    # Return an empty response if the request method is not 'POST'
    return JsonResponse({'message': 'Invalid request method'}, status=200)


@login_required()
def getItemWiseSalesManagerAPI(request):
    if request.method == "POST":
        static_start = request.POST.get('static_start')
        static_end = request.POST.get('static_end')

        # Parse the dates from the request POST data
        static_start = datetime.strptime(static_start, '%Y-%m-%d').date()
        static_end = datetime.strptime(static_end, '%Y-%m-%d').date()

        # Fetch all invoices for the specified date range
        invoices = invoice_list.objects.filter(invoice_date__range=(static_start, static_end)).all()

        # Calculate total sales quantity for each item_id across all invoices
        item_wise_sales = defaultdict(float)

        for inv in invoices:
            invoice_details = invoicedtl_list.objects.filter(inv_id=inv).all()
            for detail in invoice_details:
                item_id = detail.item_id.item_name  # Get the item_id for the detail
                sales_amt = (detail.qty - detail.is_cancel_qty) * detail.sales_rate
                item_wise_sales[item_id] += sales_amt  # Accumulate sales amount for each item_id

        data = {'item_wise_sales': dict(item_wise_sales)}
        print(data)
        return JsonResponse(data)
    
    # Return an empty response if the request method is not 'POST'
    return JsonResponse({'message': 'Invalid request method'}, status=200)

# get user org information
@login_required()
def getUserInfoAPI(request):
    user = request.user

    # Access user data
    user_data = {
        'user_id': user.user_id,
        'org_id': user.org_id,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'designation': user.designation,
    }

    # Fetch organization information
    try:
        organization = organizationlst.objects.get(org_id=user.org_id)
        org_data = {
            'org_id': organization.org_id,
            'org_name': organization.org_name,
            'address': organization.address,
            'phone': organization.phone,
            'hotline': organization.hotline,
            'fax': organization.fax,
            'email': organization.email,
            'website': organization.website,
            'org_logo': organization.org_logo.url if organization.org_logo else None,  # Get the URL of the image
        }
    except organizationlst.DoesNotExist:
        org_data = {
            'org_id': None,
            'org_name': None,
            'address': None,
            'phone': None,
            'hotline': None,
            'fax': None,
            'email': None,
            'website': None,
            'org_logo': None,
        }

    # Combine user and organization data
    result_data = {**user_data, **org_data}

    return JsonResponse(result_data, encoder=DjangoJSONEncoder)

# ======================================testing===================================
def testLogin(request):

    return render(request, 'logger/test.html')