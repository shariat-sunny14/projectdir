import sys
import json
import calendar
from PIL import Image
from io import BytesIO
from decimal import Decimal
from datetime import date, datetime, timedelta
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Prefetch
from django.db.models.functions import Concat
from django.db.models import F, CharField, Value
from django.db.models import Count
from audioop import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, redirect, HttpResponseRedirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.forms import UserCreationForm
from bank_statement.models import cash_on_hands
from store_setup.models import store
from .forms import UserRegisterForm, UserUpgrationForm
from django.contrib import messages
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from module_setup.models import module_type, module_list, feature_list
from organizations.models import organizationlst, branchslist
from user_auth.utils.save_navbar_context import save_navbar_json_for_user
from . models import access_list, serviceChargePayment, store_access
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def user_setup(request):
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
    return render(request, 'user_list/user_setup.html', context)


# get branch value and show in the dropdown
@login_required()
def getBranchOptionsAPI(request):
    if request.method == 'GET':
        user = request.user
        org_id = request.GET.get('org_id', None)

        if user.is_staff:
            # Staff can see all branches of the selected organization
            if org_id:
                branch_options = branchslist.objects.filter(
                    is_active=True, org_id=org_id).values('branch_id', 'branch_name')
            else:
                branch_options = []
        elif user.branch_id:
            branch_options = branchslist.objects.filter(
                is_active=True, branch_id=user.branch_id).values('branch_id', 'branch_name')

        else:
            branch_options = []

        return JsonResponse({'branch_list': list(branch_options)})
    return JsonResponse({'error': 'Invalid request'})

# get organzations value and show in the dropdown


@login_required()
def getOrganizationOptionAPI(request):
    if request.method == 'GET':
        user = request.user
        org_id = request.GET.get('org_id', None)

        if user.is_superuser:
            # Superuser can see all branches of the selected organization
            if org_id:
                org_options = organizationlst.objects.filter(
                    is_active=True, org_id=org_id).values('org_id', 'org_name')
            else:
                org_options = []
        elif user.org_id:
            org_options = organizationlst.objects.filter(
                is_active=True, org_id=user.org_id).values('org_id', 'org_name')

        else:
            org_options = []

        return JsonResponse({'org_Data': list(org_options)})
    return JsonResponse({'error': 'Invalid request'})


# get user wise organzations value and show in the dropdown
@login_required()
def getUserWiseOrgOptionAPI(request):
    if request.method == 'GET':
        user = request.user

        if user.is_superuser:
            # Superuser can see all branches of the selected organization
            org_options = organizationlst.objects.filter(
                is_active=True).values('org_id', 'org_name')
        elif user.org_id:
            org_options = organizationlst.objects.filter(
                is_active=True, org_id=user.org_id).values('org_id', 'org_name')

        else:
            org_options = []

        return JsonResponse({'store_acc_org': list(org_options)})
    return JsonResponse({'error': 'Invalid request'})


@login_required()
def getUserListsAPI(request):
    user = request.user
    user_list = User.objects.all()

    # Retrieve filter parameters from the frontend
    is_active = request.GET.get('is_active', None)
    org_id = request.GET.get('org_id', None)
    branch_id = request.GET.get('branch_id', None)

    # Create an empty filter dictionary to store dynamic filter conditions
    filter_conditions = {}

    # Apply filters based on conditions
    if is_active is not None:
        filter_conditions['is_active'] = is_active

    if org_id is not None:
        filter_conditions['org_id'] = org_id

    if branch_id is not None:
        filter_conditions['branch_id'] = branch_id

    if user.is_superuser:
        # Apply dynamic filters to user_list
        user_data = user_list.filter(**filter_conditions).all()
    elif user.org_id is not None:
        # If the user has an associated organization, filter by that organization
        user_data = user_list.filter(**filter_conditions, is_superuser=False).all()

    # Convert user data to a list of dictionaries
    users_data = []

    for user in user_data:
        org_name = ''
        branch_name = ''
        profile_img_url = ''

        if user.org_id:
            org_name = organizationlst.objects.get(org_id=user.org_id).org_name

        if user.branch_id:
            branch_name = branchslist.objects.get(
                branch_id=user.branch_id).branch_name

        if user.profile_img:
            profile_img_url = user.profile_img.url

        users_data.append({
            'user_id': user.user_id,
            'username': user.username,
            'profile_img': profile_img_url,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'designation': user.designation,
            'email': user.email,
            'phone_no': user.phone_no,
            'org_name': org_name,
            'branch_name': branch_name,
            'expiry_status': user.expiry_status,
            'is_active': user.is_active,
            'is_login_status': user.is_login_status,
        })

    # Return the filtered data as JSON
    return JsonResponse({'users_data': users_data})


# add user modal
@login_required()
def addUserManageAPI(request):
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
    return render(request, 'user_list/add_user_modal.html', context)

# edit user modal


@login_required()
def editUserManageAPI(request):
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

        user_data = {}
    if request.method == 'GET':
        data = request.GET
        user_id = ''
        if 'user_id' in data:
            user_id = data['user_id']
        if user_id.isnumeric() and int(user_id) > 0:
            user_data = User.objects.filter(user_id=user_id).first()

    context = {
        'user_data': user_data,
        'org_list': org_list,
    }
    return render(request, 'user_list/edit_user_modal.html', context)

# change password


@login_required()
def passwordChangeManageAPI(request):
    user_data = {}
    if request.method == 'GET':
        data = request.GET
        user_id = ''
        if 'user_id' in data:
            user_id = data['user_id']
        if user_id.isnumeric() and int(user_id) > 0:
            user_data = User.objects.filter(user_id=user_id).first()

    context = {
        'user_data': user_data
    }

    return render(request, 'user_list/password_change.html', context)


# change password
@login_required()
def passwordChangingByUserManageAPI(request):
    user_data = {}
    if request.method == 'GET':
        data = request.GET
        user_id = ''
        if 'user_id' in data:
            user_id = data['user_id']
        if user_id.isnumeric() and int(user_id) > 0:
            user_data = User.objects.filter(user_id=user_id).first()

    context = {
        'user_data': user_data
    }

    return render(request, 'user_list/password_change_by_user.html', context)

# change user info by user


@login_required()
def userInfoUpdateByUserManageAPI(request):
    user_data = {}
    if request.method == 'GET':
        data = request.GET
        user_id = ''
        if 'user_id' in data:
            user_id = data['user_id']
        if user_id.isnumeric() and int(user_id) > 0:
            user_data = User.objects.filter(user_id=user_id).first()

    context = {
        'user_data': user_data
    }

    return render(request, 'user_list/edit_user_info_by_user.html', context)

# update password save


@login_required()
def passwordUpdateManageAPI(request):
    resp = {'success': 'failed', 'errmsg': 'Fails ...'}
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        new_password = request.POST.get('password1')

        # Retrieve the user based on the user_id
        user_instance = User.objects.filter(user_id=user_id).first()

        if user_instance:
            try:
                with transaction.atomic():
                    # Update the password for the user
                    user_instance.password = make_password(new_password)
                    user_instance.save()
                    return JsonResponse({'success': True, 'msg': 'Password changed successfully'})
            except Exception as e:
                resp['errmsg'] = str(e)
        else:
            return JsonResponse({'success': False, 'msg': 'User not found'})
    else:
        return JsonResponse(resp)


@login_required()
def saveUserAPI(request):
    resp = {'success': 'failed', 'errmsg': 'Fails ...'}

    if request.method == "POST":
        username = request.POST.get('username')
        org = request.POST.get('org')
        branch_name = request.POST.get('branch_name')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        is_active = request.POST.get('is_active')
        designation = request.POST.get('designation')
        phone_no = request.POST.get('phone_no')
        expiry_date_str = request.POST.get('expiry_date')
        expiry_status = request.POST.get('expiry_status')

        # Parse expiry_date_str to the desired format (YYYY-MM-DD)
        try:
            expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'success': False, 'errmsg': 'Invalid date format. Please provide the date in YYYY-MM-DD format'})

        # Check if phone_no is empty
        if phone_no == '':
            return JsonResponse({'success': False, 'errmsg': 'Phone number cannot be empty'})

        # Validate phone_no as a number
        try:
            phone_no = int(phone_no)
        except ValueError:
            return JsonResponse({'success': False, 'errmsg': 'Phone number should be a valid number'})

        if password1 == password2:
            if User.objects.filter(username=username).exists():
                return JsonResponse({'success': False, 'errmsg': 'User Name already exists'})
            elif User.objects.filter(email=email).exists():
                return JsonResponse({'success': False, 'errmsg': 'Email Address already exists'})
            elif User.objects.filter(phone_no=phone_no).exists():
                return JsonResponse({'success': False, 'errmsg': 'Phone number already exists'})

            else:
                try:
                    with transaction.atomic():
                        user_instance = User(
                            username=username,
                            org_id=org,
                            branch_id=branch_name,
                            first_name=first_name,
                            last_name=last_name,
                            email=email,
                            password=make_password(password1),
                            is_active=is_active,
                            designation=designation,
                            phone_no=phone_no,
                            expiry_date=expiry_date,
                            expiry_status=expiry_status,
                        )
                        # Ensure request.user is available before setting ss_creator
                        if request.user.is_authenticated:
                            user_instance.ss_creator = request.user
                        else:
                            # Handle the case where request.user is not available
                            user_instance.ss_creator = None
                        # Save the image file
                        if 'profile_img' in request.FILES:
                            image_file = request.FILES['profile_img']
                            image = Image.open(image_file)

                            # Resize the image to fit within 300x300 while maintaining aspect ratio
                            image.thumbnail((300, 300))

                            # Convert the image to BytesIO and save to Django's ContentFile
                            output = BytesIO()
                            image.save(output, format='JPEG')
                            output.seek(0)

                            # Save the resized image to the user profile_img field
                            filename = default_storage.save(
                                'user_profile/' + image_file.name, ContentFile(output.read()))
                            user_instance.profile_img = filename
                        # Save the user
                        user_instance.save()

                        resp['success'] = 'success'
                        return JsonResponse({'success': True, 'msg': 'Account Created Successfully'})
                except Exception as e:
                    resp['errmsg'] = str(e)
        else:
            return JsonResponse({'success': False, 'errmsg': 'Password Not Matching. Please Try Again'})
    else:
        resp['errmsg'] = 'Fails ...'

    return JsonResponse(resp)

# update user


@login_required()
def updateUserAPI(request, user_id):
    resp = {'success': 'failed', 'errmsg': 'Failed...'}
    up_type_context = {}

    update_user = get_object_or_404(User, pk=user_id)

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')

        if User.objects.exclude(username=update_user.username).filter(username=username).exists():
            return JsonResponse({'success': False, 'errmsg': 'Username already exists'})
        elif User.objects.exclude(email=update_user.email).filter(email=email).exists():
            return JsonResponse({'success': False, 'errmsg': 'Email address already exists'})
        else:
            try:
                with transaction.atomic():
                    up_form = UserUpgrationForm(
                        request.POST or None, instance=update_user)
                    if up_form.is_valid():
                        instance = up_form.save(commit=False)

                        # Check if a new profile image is provided and it's different
                        if 'profile_img' in request.FILES:
                            new_image_file = request.FILES['profile_img']

                            if instance.profile_img and instance.profile_img.name != new_image_file.name:
                                # Delete existing profile image before saving the new one
                                default_storage.delete(
                                    instance.profile_img.path)

                            # Resize the image to fit within 300x300 while maintaining aspect ratio
                            image = Image.open(new_image_file)
                            image.thumbnail((300, 300))

                            # Convert the image to BytesIO and save to Django's ContentFile
                            output = BytesIO()
                            image.save(output, format='JPEG')
                            output.seek(0)

                            # Save the new profile image
                            filename = default_storage.save(
                                'user_profile/' + new_image_file.name, ContentFile(output.getvalue()))
                            instance.profile_img = filename

                        instance.ss_modifier = request.user  # Set ss_modifier to the current user
                        instance.save()

                        resp['success'] = 'success'
                        return JsonResponse({'success': True, 'msg': 'Update successfully'})
                    else:
                        # Add this line to include form errors in the response
                        resp['errors'] = up_form.errors
                        return JsonResponse({'success': False, 'errmsg': 'Form is not valid. Update failed.'})
            except Exception as e:
                resp['errmsg'] = str(e)
    else:
        up_form = UserUpgrationForm(instance=update_user)
        up_type_context = {
            'update_user': update_user,
            'up_form': up_form,
        }
    resp['up_type_context'] = up_type_context
    resp['errmsg'] = 'Fails ...'

    return JsonResponse(resp)


# user info update by user
@login_required()
def updateUserInfoByUserManagerAPI(request, user_id):
    resp = {'success': 'failed', 'errmsg': 'Failed...'}

    update_user = get_object_or_404(User, pk=user_id)

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        designation = request.POST.get('designation')
        phone_no = request.POST.get('phone_no')

        # Check if the username or email already exists for another user
        if (username and User.objects.exclude(username=update_user.username).filter(username=username).exists()) or \
           (email and User.objects.exclude(email=update_user.email).filter(email=email).exists()):
            return JsonResponse({'success': False, 'errmsg': 'Username or Email already exists'})
        else:
            try:
                # Update user instance with new data
                update_user.username = username or update_user.username
                update_user.email = email or update_user.email
                update_user.first_name = first_name or update_user.first_name
                update_user.last_name = last_name or update_user.last_name
                update_user.designation = designation or update_user.designation
                update_user.phone_no = phone_no or update_user.phone_no
                # Check if a new profile image is provided and it's different
                if 'profile_img' in request.FILES:
                    new_image_file = request.FILES['profile_img']

                    if update_user.profile_img and update_user.profile_img.name != new_image_file.name:
                        # Delete existing profile image before saving the new one
                        default_storage.delete(update_user.profile_img.path)

                    # Resize the image to fit within 300x300 while maintaining aspect ratio
                    image = Image.open(new_image_file)
                    image.thumbnail((300, 300))

                    # Convert the image to BytesIO and save to Django's ContentFile
                    output = BytesIO()
                    image.save(output, format='JPEG')
                    output.seek(0)

                    # Save the new profile image
                    filename = default_storage.save(
                        'user_profile/' + new_image_file.name, ContentFile(output.getvalue()))
                    update_user.profile_img = filename

                # Save the updated user
                update_user.save()

                resp['success'] = 'success'
                return JsonResponse({'success': True, 'msg': 'Update successfully'})
            except Exception as e:
                resp['errmsg'] = str(e)
    else:
        resp['errmsg'] = 'Invalid request method'

    return JsonResponse(resp)


# ============================================== access list ======================================
@login_required()
def useraccessManageAPI(request):
    access = {}
    # Fetch module_list data and related data using prefetch_related with Prefetch objects
    module_data = module_list.objects.prefetch_related(
        Prefetch(
            'module_id2moduletype',
            queryset=module_type.objects.filter(is_active=True).prefetch_related(
                Prefetch(
                    'type_id2feature_list',
                    queryset=feature_list.objects.filter(is_active=True)
                )
            ).prefetch_related(
                Prefetch(
                    'type_id2feature_list__feature_id2access_list',
                    queryset=access_list.objects.filter(is_active=True)
                )
            )
        ),
        'ss_creator'
    ).filter(is_active=True).all()

    if request.method == 'GET':
        data = request.GET
        user_id = ''
        if 'user_id' in data:
            user_id = data['user_id']
        if user_id.isnumeric() and int(user_id) > 0:
            access = User.objects.filter(user_id=user_id).first()
            # Fetch access_list objects for the current user
            access_features = access.user_id2access_list.filter(
                is_active=True).values_list('feature_id', flat=True)
    else:
        access_features = []  # Initialize an empty list if not in GET request

    context = {
        'access': access,
        'module_data': module_data,
        'access_features': access_features,
    }
    return render(request, 'user_list/user_access.html', context)


@login_required
@csrf_exempt
@require_POST
def saveAccessAPI(request):
    resp = {'status': 'failed'}
    data = request.POST

    is_active_list = data.getlist('is_active[]')
    feature_id_list = data.getlist('feature_id[]')

    user_id = int(data.get('user_id'))
    try:
        user_instance = get_object_or_404(User, pk=user_id)
        with transaction.atomic():
            # First, delete all existing access records for the user
            access_list.objects.filter(user_id=user_instance).delete()

            # Then create new access records based on the submitted data
            for is_active, feature_id in zip(is_active_list, feature_id_list):
                feature_instance = get_object_or_404(
                    feature_list, pk=feature_id)
                access_item = access_list(
                    user_id=user_instance,
                    is_active=is_active,
                    feature_id=feature_instance,
                    ss_creator=request.user,
                    ss_modifier=request.user,
                )
                access_item.save()
                print('User Access:', 'user_id:', user_id, 'is_active:',
                      is_active, 'feature_id:', feature_id)

            # Save navbar context as JSON for the user
            save_navbar_json_for_user(user_instance)

            resp['status'] = 'success'
            return JsonResponse({'success': True, 'msg': 'Successful'})
    except Exception as e:
        print("Exception:", str(e))
        resp['status'] = 'failed'
        # Include the error message in the response
        resp['error_message'] = str(e)
    return HttpResponse(json.dumps(resp), content_type="application/json")


# ============================================== Store Access ======================================
# for store access get organzations value
@login_required()
@require_GET
def getStoreAccessOrgDataAPI(request):
    if request.method == 'GET':
        user = request.user
        search_term = request.GET.get('search', '')

        if user.is_superuser:
            # Superuser can see all branches of the selected organization
            org_options = organizationlst.objects.filter(
                is_active=True, org_name__icontains=search_term).values('org_id', 'org_name')
        elif user.org_id:
            org_options = organizationlst.objects.filter(
                is_active=True, org_id=user.org_id, org_name__icontains=search_term).values('org_id', 'org_name')
        else:
            org_options = []

        return JsonResponse({'org_Data': list(org_options)})
    return JsonResponse({'error': 'Invalid request'})


# click org_id wise show store value
@login_required()
def getOrgIdWiseStoreValueAPI(request, org_id):
    # Retrieve user_id from the request parameters
    user_id = request.GET.get('user_id')
    org_store_list = []
    branch_store_list = []
    select_store_access_data = {}

    if org_id:
        org = organizationlst.objects.filter(
            org_id=org_id, is_active=True).first()
        if org:
            store_list = store.objects.filter(org_id=org_id, is_org_store=True, is_active=True).values(
                'store_id', 'org_id', 'store_no', 'store_name', 'is_branch_store'
            )

            org_store_detail = {
                'org_id': org.org_id,
                'org_id__org_name': org.org_name,
                'org_storeDtl': list(store_list)
            }
            org_store_list.append(org_store_detail)

            branches = branchslist.objects.filter(
                org_id=org.org_id, is_active=True)
            for branch in branches:
                store_list = store.objects.filter(branch_id=branch.branch_id, is_branch_store=True, is_active=True).values(
                    'org_id', 'store_id', 'branch_id', 'store_no', 'store_name', 'is_org_store'
                )

                branch_store_detail = {
                    'org_id': branch.org_id.org_id,
                    'branch_id': branch.branch_id,
                    'branch_id__branch_name': branch.branch_name,
                    'branch_storeDtl': list(store_list)
                }
                branch_store_list.append(branch_store_detail)

            # Filter store access data by org_id and user_id (if provided)
            storeacc_data = store_access.objects.filter(org_id=org_id)
            if user_id:
                storeacc_data = storeacc_data.filter(user_id=user_id)

            storeacc_data = storeacc_data.values(
                'store_id', 'org_id', 'user_id', 'is_default')

            # Serialize queryset to a list of dictionaries
            storeacc_data_serialized = list(storeacc_data)
            select_store_access_data['storeacc_data'] = storeacc_data_serialized

    response_data = {
        'org_store_list': org_store_list,
        'branch_store_list': branch_store_list,
        'select_store_access_data': select_store_access_data
    }

    return JsonResponse(response_data)


@login_required
@csrf_exempt
@require_POST
def saveStoreAccessAPI(request):
    resp = {'status': 'failed'}
    data = request.POST

    store_ids = data.getlist('store_ids[]')
    is_defaults = data.getlist('is_default[]')

    user_id = int(data.get('user_id'))
    org_id = int(data.get('org_id'))

    try:
        user_instance = get_object_or_404(User, user_id=user_id)
        org_instance = get_object_or_404(organizationlst, org_id=org_id)

        with transaction.atomic():
            store_access.objects.filter(user_id=user_instance).delete()
            # Iterate over the submitted data and process each entry
            for store_id, is_default in zip(store_ids, is_defaults):
                store_instance = get_object_or_404(store, store_id=store_id)

                # Check if the record already exists, and if so, update the 'is_default' value
                store_access.objects.update_or_create(
                    user_id=user_instance,
                    org_id=org_instance,
                    store_id=store_instance,
                    defaults={
                        'is_default': is_default,
                        'ss_creator': request.user,
                        'ss_modifier': request.user,
                    }
                )

            resp['status'] = 'success'
            return JsonResponse({'success': True, 'msg': 'Successful'})
    except Exception as e:
        print("Exception:", str(e))
        resp['status'] = 'failed'
        # Include the error message in the response
        resp['error_message'] = str(e)
        return JsonResponse(resp, status=500)

# ============================================== Store Access ======================================


# ============================================== testing ======================================


# ======================================== Service Charge Payment ==============================
@login_required
def serviceChargePaymentManagerAPI(request):
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
    return render(request, 'service_charge_payment/service_charge_payment.html', context)


@login_required
def getServiceChargebyOrg(request):
    org_id = request.GET.get('org_id')
    try:
        org = organizationlst.objects.get(org_id=org_id)
        return JsonResponse({'service_charge': org.service_charge or 0})
    except organizationlst.DoesNotExist:
        return JsonResponse({'service_charge': 0})


@login_required
def getPaidServiceMonths(request):
    org_id = request.GET.get('org_id')
    service_year = request.GET.get('service_year') or str(now().year)

    filters = {
        # 'is_approved': True,
        'service_year': service_year,
    }

    if org_id:
        filters['org_id'] = org_id

    paid_months = list(
        serviceChargePayment.objects
        .filter(**filters)
        .values_list('service_month', flat=True)
    )

    return JsonResponse({'paid_months': paid_months})


@login_required()
def getServiceChargePaymentListManagerAPI(request):
    # Retrieve filter parameters from the frontend
    org_id_filter = request.GET.get('org_id', '').strip()
    service_year_filter = request.GET.get('service_year', '').strip()

    filter_kwargs = {}

    if org_id_filter:
        filter_kwargs['org_id'] = org_id_filter
    if service_year_filter:
        filter_kwargs['service_year'] = service_year_filter

    dataDtls = serviceChargePayment.objects.filter(**filter_kwargs).order_by('-creater_date')

    serviceData = [
        {
            'service_id': service.service_id,
            'creater_date': service.creater_date if service.creater_date else None,
            'org_id': service.org_id.org_id if service.org_id else None,
            'org_name': service.org_id.org_name if service.org_id else None,
            'branch_id': service.branch_id.branch_id if service.branch_id else None,
            'branch_name': service.branch_id.branch_name if service.branch_id else None,
            'is_passing': service.is_passing if service.is_passing else None,
            'is_approved': service.is_approved if service.is_approved else None,
            'service_month': service.service_month if service.service_month else None,
            'service_year': service.service_year if service.service_year else None,
            'service_amt': service.service_amt if service.service_amt else None,
            'service_payment': service.service_payment if service.service_payment else None,
            'payment_trans_id': service.payment_trans_id if service.payment_trans_id else None,
            'reference': service.reference if service.reference else None,
        }
        for service in dataDtls
    ]

    return JsonResponse({'service_val': serviceData})

@login_required()
def saveServiceChargePaymentManagementAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    
    if request.method != 'POST':
        resp['errmsg'] = 'Only POST requests are allowed'
        return JsonResponse(resp)

    data = request.POST
    
    org_id = data.get('org_id')
    service_amt = data.get('service_amt')
    service_payment = data.get('service_payment')
    service_month_list = data.getlist('service_month[]')
    service_year = data.get('service_year')
    reference = data.get('reference', '')
    payment_trans_id = data.get('payment_trans_id', '')
    is_passing = data.get('is_passing', False)
    is_approved = data.get('is_approved', False)

    try:
        with transaction.atomic():
            # Validate required fields
            if not (org_id and service_amt and service_payment and service_month_list and service_year):
                resp['errmsg'] = 'Missing required fields'
                return JsonResponse(resp)

            # Get organization instance
            org_instance = organizationlst.objects.get(org_id=org_id)
            for smonth in service_month_list:
                service_obj = serviceChargePayment(
                    org_id=org_instance,
                    service_amt=Decimal(service_amt),
                    service_payment=Decimal(service_amt),
                    service_month=smonth,
                    service_year=service_year,
                    reference=reference,
                    payment_trans_id=payment_trans_id,
                    is_passing=is_passing,
                    is_approved=is_approved,
                    ss_creator=request.user,
                    ss_modifier=request.user,
                )
                service_obj.save()

            resp['success'] = True
            resp['msg'] = 'Saved successfully'

    except Exception as e:
        resp['errmsg'] = str(e)

    return JsonResponse(resp)


@login_required()
def getDeleteServiceChargePaymentModelAPI(request):
    service_data = {}
    if request.method == 'GET':
        data = request.GET
        service_id = ''
        if 'service_id' in data:
            service_id = data['service_id']
        if service_id.isnumeric() and int(service_id) > 0:
            service_data = serviceChargePayment.objects.filter(service_id=service_id).first()

    context = {
        'service_data': service_data,
    }
    return render(request, 'service_charge_payment/delete_confirmation.html', context)


@method_decorator(csrf_exempt, name='dispatch')
@require_http_methods(["DELETE"])
def serviceChargePaymentDtlDeleteAPI(request, service_id):
    try:
        # Try to find the record
        service_obj = serviceChargePayment.objects.filter(service_id=service_id).first()

        if not service_obj:
            return JsonResponse({'success': False, 'errmsg': f'Service record with ID {service_id} not found.'}, status=404)

        # Delete the record
        service_obj.delete()

        return JsonResponse({'success': True, 'msg': 'Successfully deleted.'})

    except Exception as e:
        return JsonResponse({'success': False, 'errmsg': f'Error occurred: {str(e)}'}, status=500)
    

@login_required()
def getServiceChargePaymentAlertModelAPI(request):

    return render(request, 'service_charge_payment/service_charge_alert.html')


# MONTHS_LIST = [
#     'january', 'february', 'march', 'april', 'may', 'june',
#     'july', 'august', 'september', 'october', 'november', 'december'
# ]

# @login_required
# def getOrgServiceChargeDetailsInfoManagerAPI(request):
#     user = request.user

#     if user.org_id is not None:
#         try:
#             org = organizationlst.objects.get(is_active=True, org_id=user.org_id)

#             # Basic data
#             is_start_up = org.is_start_up
#             service_charge = org.service_charge or 0
#             is_alert_start = org.is_alert_start or 1
#             is_alert_end = org.is_alert_end or 1
#             today = date.today()

#             # Alert period dates
#             current_year, current_month = today.year, today.month
#             alert_start_date = date(current_year, current_month, min(is_alert_start, calendar.monthrange(current_year, current_month)[1]))
#             if current_month == 12:
#                 next_month, next_year = 1, current_year + 1
#             else:
#                 next_month, next_year = current_month + 1, current_year
#             alert_end_date = date(next_year, next_month, min(is_alert_end, calendar.monthrange(next_year, next_month)[1]))

#             # --- Remaining days between now and alert_end_date ---
#             remaining_alert_days = 0
#             if today <= alert_end_date:
#                 remaining_alert_days = (alert_end_date - today).days
                
#             # Initialize due_amount
#             total_months = 0
#             paid_months = set()
#             unpaid_months = []

#             if is_start_up:
#                 # 1. Get all months from is_start_up to today (inclusive)
#                 current_pointer = date(is_start_up.year, is_start_up.month, 1)
#                 last_pointer = date(today.year, today.month, 1)

#                 all_months = []
#                 while current_pointer <= last_pointer:
#                     y = current_pointer.year
#                     m = current_pointer.month
#                     all_months.append((y, MONTHS_LIST[m - 1]))
#                     if m == 12:
#                         current_pointer = date(y + 1, 1, 1)
#                     else:
#                         current_pointer = date(y, m + 1, 1)

#                 total_months = len(all_months)

#                 # 2. Get all paid months for this org
#                 paid_records = serviceChargePayment.objects.filter(org_id=org, is_approved=True)
#                 for p in paid_records:
#                     if p.service_year and p.service_month:
#                         paid_months.add((int(p.service_year), p.service_month.lower().strip()))

#                 # 3. Subtract paid from total
#                 unpaid_months = [m for m in all_months if m not in paid_months]
#                 due_amount = len(unpaid_months) * service_charge

#             return JsonResponse({
#                 'is_start_up': is_start_up,
#                 'service_charge': service_charge,
#                 'is_alert_start': alert_start_date.strftime("%d %B %Y"),
#                 'alert_start_isoformat': alert_start_date.isoformat(),
#                 'is_alert_end': alert_end_date.strftime("%d %B %Y"),
#                 'alert_end_isoformat': alert_end_date.isoformat(),
#                 'remaining_alert_days': remaining_alert_days,
#                 'total_months': total_months,
#                 'paid_months': list(paid_months),
#                 'unpaid_months': unpaid_months,
#                 'due_amount': due_amount
#             })

#         except organizationlst.DoesNotExist:
#             return JsonResponse({'error': 'Organization not found or inactive.'}, status=404)

#     return JsonResponse({'error': 'User has no associated organization.'}, status=400)

# ======================================== Service Charge Payment ==============================

# test perpose


@login_required
def testing_user_access_list(request):

    return render(request, 'user_list/test_access_list.html')
