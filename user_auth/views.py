import json
import sys
import pytz
import logging
from django.shortcuts import render, redirect, HttpResponseRedirect
from datetime import date, datetime, timedelta
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.forms import UserCreationForm
from .forms import UserLoginForm
from django.contrib import messages
from collections import defaultdict
from decimal import Decimal
from django.utils.timezone import now
from django.contrib.sessions.models import Session
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django_ratelimit.decorators import ratelimit
from django.views.decorators.csrf import csrf_protect
from django.db.models import Q, ExpressionWrapper, F, FloatField, Sum, Count
from user_setup.models import access_list
from organizations.models import organizationlst
from django.http import HttpResponseNotFound
from .decorators import login_required_with_timeout
from user_auth.utils.save_user_context import save_user_context_to_json
from user_auth.utils.save_navbar_context import save_navbar_json_for_user
from . models import SystemShutdown
from django.contrib.auth import get_user_model
User = get_user_model()


def ratelimited_view(request, exception):
    return JsonResponse({'success': False, 'errmsg': 'Too many requests. Please try again later.'}, status=429)

# login page render
def user_loginManagerAPI(request):
    # Set the timezone to Dhaka
    dhaka_tz = pytz.timezone('Asia/Dhaka')
    present_time = timezone.now().astimezone(dhaka_tz).date()  # Convert to date

    # Retrieve the latest `SystemShutdown` record (for sys_validity check)
    sys_expiry = SystemShutdown.objects.order_by('-sys_id').first()
    
    # Check if `sys_validity` is set and has not expired
    if sys_expiry and sys_expiry.sys_validity and present_time > sys_expiry.sys_validity:
        return render(request, 'sys_shut_down/sys_shut_down.html')

    # Retrieve the first active system shutdown record for is_sys_shut_down=True
    shutdown_data = SystemShutdown.objects.filter(is_sys_shut_down=True).order_by('-sys_id').first()

    # Check if there is an active shutdown and validate its down-time validity
    present_time_datetime = timezone.now().astimezone(dhaka_tz)  # Original datetime for datetime comparisons
    if shutdown_data:
        if present_time_datetime > shutdown_data.sys_down_time_validity:
            return render(request, 'logger/singin_form.html')
        else:
            return render(request, 'sys_shut_down/sys_shut_down.html')
    
    # Default to the login page if no active shutdown or validity check conditions are met
    return render(request, 'logger/singin_form.html')

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
            organizations = organizationlst.objects.filter(org_id=user.org_id).values('org_id', 'org_name')

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



logger = logging.getLogger(__name__)
@csrf_protect
@ratelimit(key='user', rate='100/m', method='POST', block=True)
def user_loginAPI(request):
    resp = {'success': False, 'errmsg': 'Invalid Username and Password. Please Try Again.'}
    present_date = datetime.now().date()
    
    if request.method == 'POST':
        logout(request)
        username = request.POST.get('username')
        password = request.POST.get('password')
        org_name = request.POST.get('org_name')
        
        # Fetch organization based on org_name
        try:
            organization = organizationlst.objects.get(org_id=org_name)
        except organizationlst.DoesNotExist:
            return JsonResponse({'success': False, 'errmsg': 'Organization not found.'})
        
        # Fetch user based on the username (case-insensitive)
        try:
            user = User.objects.get(username__iexact=username)
        except User.DoesNotExist:
            user = None
        
        # Authenticate user with the provided password
        if user is not None and user.check_password(password):
            # Check if the user's org_id matches the organization's org_id
            if user.org_id == organization.org_id:
                # Check if the user's expiry_date is less than the present_date
                if user.expiry_date and user.expiry_date < present_date:
                    return JsonResponse({'success': False, 'errmsg': 'User account has expired. Please contact the administration.'})
                
                user.is_login_status = True
                user.save()
                
                login(request, user)
                # Optional helpers
                save_user_context_to_json(user)
                save_navbar_json_for_user(user)
                
                logger.info(f"User {user.username} logged in success.")
                return JsonResponse({'success': True, 'msg': 'Login Successful.'})
            else:
                logger.warning(f"User {username} provided an invalid organization.")
                return JsonResponse({'success': False, 'errmsg': 'Invalid organization.'})
        else:
            logger.warning(f"Invalid login attempt for username: {username}")
            return JsonResponse({'success': False, 'errmsg': 'Invalid Username and Password. Please Try Again.'})
    
    return JsonResponse(resp)


@login_required_with_timeout
def main_dashboard(request):
    active_access_list_data = []

    if request.user.is_authenticated:
        access_list_data = access_list.objects.filter(
            user_id=request.user,
            feature_id__is_active=True,
            feature_id__module_id__is_active=True,
            feature_id__module_id__module_id2feature_list__is_active=True,
            feature_id__type_id__is_active=True,  # Check is_active on the related module_type
            feature_id__feature_type="Form",
        ).select_related(
            'feature_id__type_id',  # Select the related module_type
            'feature_id__module_id',  # Select the related module_list
        )

        active_access_list_data = access_list_data.filter(
            feature_id__is_active=True,
            feature_id__module_id__is_active=True,
            feature_id__module_id__module_id2feature_list__is_active=True,
            feature_id__type_id__is_active=True,  # Apply the same is_active filter here
        ).distinct()

    context = {
        'active_access_list_data': active_access_list_data,
    }

    return render(request, 'main_dashboard/main_dashboard.html', context)


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