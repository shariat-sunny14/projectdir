import sys
import json
from PIL import Image
from io import BytesIO
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Prefetch
from django.db.models.functions import Concat
from django.db.models import F, CharField, Value
from django.db.models import Count
from audioop import reverse
from django.shortcuts import render, redirect, HttpResponseRedirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.forms import UserCreationForm
from class_setup.models import in_class
from groups_setup.models import in_groups
from section_setup.models import in_section
from shift_setup.models import in_shifts
from user_auth.utils.save_navbar_context import save_navbar_json_for_user
from user_auth.utils.save_othersaccess_context import save_othersaccess_json_for_user
from .forms import UserRegisterForm, UserUpgrationForm
from django.contrib import messages
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from module_setup.models import module_type, module_list, feature_list
from organizations.models import organizationlst, branchslist
from . models import access_list, others_access_list
from django.contrib.auth import get_user_model
User = get_user_model()

@login_required()
def user_setup(request):
    
    return render(request, 'user_list/user_setup.html')


# get organzations value and show in the dropdown
# @login_required()
# def getOrganizationOptionAPI(request):
#     if request.method == 'GET':
#         user = request.user
#         org_id = request.GET.get('org_id', None)

#         if user.is_superuser:
#             # Superuser can see all branches of the selected organization
#             if org_id:
#                 org_options = organizationlst.objects.filter(is_active=True, org_id=org_id).values('org_id', 'org_name')
#             else:
#                 org_options = []
#         elif user.org_id:
#             org_options = organizationlst.objects.filter(is_active=True, org_id=user.org_id).values('org_id', 'org_name')
            
#         else:
#             org_options = []

#         return JsonResponse({'org_Data': list(org_options)})
#     return JsonResponse({'error': 'Invalid request'})


# # get user wise organzations value and show in the dropdown
# @login_required()
# def getUserWiseOrgOptionAPI(request):
#     if request.method == 'GET':
#         user = request.user

#         if user.is_superuser:
#             # Superuser can see all branches of the selected organization
#             org_options = organizationlst.objects.filter(is_active=True).values('org_id', 'org_name')
#         elif user.org_id:
#             org_options = organizationlst.objects.filter(is_active=True, org_id=user.org_id).values('org_id', 'org_name')
            
#         else:
#             org_options = []

#         return JsonResponse({'store_acc_org': list(org_options)})
#     return JsonResponse({'error': 'Invalid request'})


@login_required()
def getUserListsAPI(request):
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

    # Apply dynamic filters to user_list
    user_data = user_list.filter(**filter_conditions).all()
    
    # Convert user data to a list of dictionaries
    users_data = []

    for user in user_data:
        org_name = ''
        branch_name = ''
        profile_img_url = ''

        if user.org_id:
            org_name = organizationlst.objects.get(org_id=user.org_id).org_name

        if user.branch_id:
            branch_name = branchslist.objects.get(branch_id=user.branch_id).branch_name

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
    
    return render(request, 'user_list/add_user_modal.html')

# edit user modal
@login_required()
def editUserManageAPI(request):
        
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
                            user_instance.ss_creator = None  # Handle the case where request.user is not available
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
                            filename = default_storage.save('user_profile/' + image_file.name, ContentFile(output.read()))
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
                    up_form = UserUpgrationForm(request.POST or None, instance=update_user)
                    if up_form.is_valid():
                        instance = up_form.save(commit=False)

                        # Check if a new profile image is provided and it's different
                        if 'profile_img' in request.FILES:
                            new_image_file = request.FILES['profile_img']
                            
                            if instance.profile_img and instance.profile_img.name != new_image_file.name:
                                # Delete existing profile image before saving the new one
                                default_storage.delete(instance.profile_img.path)

                            # Resize the image to fit within 300x300 while maintaining aspect ratio
                            image = Image.open(new_image_file)
                            image.thumbnail((300, 300))

                            # Convert the image to BytesIO and save to Django's ContentFile
                            output = BytesIO()
                            image.save(output, format='JPEG')
                            output.seek(0)

                            # Save the new profile image
                            filename = default_storage.save('user_profile/' + new_image_file.name, ContentFile(output.getvalue()))
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
                    filename = default_storage.save('user_profile/' + new_image_file.name, ContentFile(output.getvalue()))
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


# ==============================================access list======================================
@login_required()
def useraccessManageAPI(request):
    user_id = request.GET.get('user_id', None)

    # Step 1: Initialize access-related lists
    access = None
    access_features = []

    active_class_ids = []
    default_class_id = None

    active_section_ids = []
    default_section_id = None

    active_shift_ids = []
    default_shift_id = None

    active_group_ids = []
    default_group_id = None

    # Step 2: Fetch Module Data with nested prefetches
    module_data = module_list.objects.prefetch_related(
        Prefetch(
            'module_id2moduletype',
            queryset=module_type.objects.filter(is_active=True).prefetch_related(
                Prefetch(
                    'type_id2feature_list',
                    queryset=feature_list.objects.filter(is_active=True)
                ),
                Prefetch(
                    'type_id2feature_list__feature_id2access_list',
                    queryset=access_list.objects.filter(is_active=True)
                )
            )
        ),
        'ss_creator'
    ).filter(is_active=True)

    # Step 3: If valid user_id, fetch user and their access
    if user_id and user_id.isnumeric():
        user_obj = User.objects.filter(user_id=user_id).first()

        if user_obj:
            access = user_obj

            # Feature-level access
            access_features = user_obj.user_id2access_list.filter(is_active=True).values_list('feature_id', flat=True)

            # Class/Section/Shift/Group-level access
            access_entries = others_access_list.objects.filter(user_id=user_obj)

            for entry in access_entries:
                if entry.class_id:
                    active_class_ids.append(entry.class_id.class_id)
                    if entry.is_defaults:
                        default_class_id = entry.class_id.class_id

                if entry.section_id:
                    active_section_ids.append(entry.section_id.section_id)
                    if entry.is_defaults:
                        default_section_id = entry.section_id.section_id

                if entry.shifts_id:
                    active_shift_ids.append(entry.shifts_id.shift_id)
                    if entry.is_defaults:
                        default_shift_id = entry.shifts_id.shift_id

                if entry.groups_id:
                    active_group_ids.append(entry.groups_id.groups_id)
                    if entry.is_defaults:
                        default_group_id = entry.groups_id.groups_id

    # Step 4: Static dropdown data
    classlist = in_class.objects.filter(is_active=True)
    sectionlist = in_section.objects.filter(is_active=True)
    shiftslist = in_shifts.objects.filter(is_active=True)
    groupslist = in_groups.objects.filter(is_active=True)

    # Step 5: Return to template
    context = {
        'access': access,
        'module_data': module_data,
        'access_features': access_features,
        'classlist': classlist,
        'sectionlist': sectionlist,
        'shiftslist': shiftslist,
        'groupslist': groupslist,

        'active_class_ids': active_class_ids,
        'default_class_id': default_class_id,

        'active_section_ids': active_section_ids,
        'default_section_id': default_section_id,

        'active_shift_ids': active_shift_ids,
        'default_shift_id': default_shift_id,

        'active_group_ids': active_group_ids,
        'default_group_id': default_group_id,
    }

    return render(request, 'user_list/user_access.html', context)



# def useraccessManageAPI(request):
#     access = {}
#     # Fetch module_list data and related data using prefetch_related with Prefetch objects
#     module_data = module_list.objects.prefetch_related(
#         Prefetch(
#             'module_id2moduletype',
#             queryset=module_type.objects.filter(is_active=True).prefetch_related(
#                 Prefetch(
#                     'type_id2feature_list',
#                     queryset=feature_list.objects.filter(is_active=True)
#                 )
#             ).prefetch_related(
#                 Prefetch(
#                     'type_id2feature_list__feature_id2access_list',
#                     queryset=access_list.objects.filter(is_active=True)
#                 )
#             )
#         ),
#         'ss_creator'
#     ).filter(is_active=True).all()

#     if request.method == 'GET':
#         data = request.GET
#         user_id = ''
#         if 'user_id' in data:
#             user_id = data['user_id']
#         if user_id.isnumeric() and int(user_id) > 0:
#             access = User.objects.filter(user_id=user_id).first()
#             # Fetch access_list objects for the current user
#             access_features = access.user_id2access_list.filter(is_active=True).values_list('feature_id', flat=True)
#     else:
#         access_features = []  # Initialize an empty list if not in GET request
        
#     classlist = in_class.objects.filter(is_active=True).all()
#     sectionlist = in_section.objects.filter(is_active=True).all()
#     shiftslist = in_shifts.objects.filter(is_active=True).all()
#     groupslist = in_groups.objects.filter(is_active=True).all()
    
#     context = {
#         'access': access,
#         'module_data': module_data,
#         'access_features': access_features,
#         'classlist': classlist,
#         'sectionlist': sectionlist,
#         'shiftslist': shiftslist,
#         'groupslist': groupslist,
#     }
#     return render(request, 'user_list/user_access.html', context)


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

# ============================================== others access ======================================
@csrf_exempt
@login_required
def saveUpdateOthersAccessManagerAPI(request):
    if request.method == "POST":
        try:
            user_id = request.POST.get('user_id')
            user = User.objects.filter(pk=user_id).first()

            if not user:
                return JsonResponse({'success': False, 'error_message': 'User not found.'})

            # Extract all IDs
            class_ids = request.POST.getlist('is_class_id[]')
            section_ids = request.POST.getlist('is_section_id[]')
            shift_ids = request.POST.getlist('is_shift_id[]')
            group_ids = request.POST.getlist('is_groups_id[]')

            default_class_id = request.POST.get('default_class_id', '')
            default_section_id = request.POST.get('default_section_id', '')
            default_shift_id = request.POST.get('default_shift_id', '')
            default_group_id = request.POST.get('default_group_id', '')

            # Clear old entries
            others_access_list.objects.filter(user_id=user).delete()

            # Helper to create access
            def create_access(class_id=None, section_id=None, shift_id=None, groups_id=None, is_default=False):
                others_access_list.objects.create(
                    user_id=user,
                    class_id=in_class.objects.filter(pk=class_id).first() if class_id else None,
                    section_id=in_section.objects.filter(pk=section_id).first() if section_id else None,
                    shifts_id=in_shifts.objects.filter(pk=shift_id).first() if shift_id else None,
                    groups_id=in_groups.objects.filter(pk=groups_id).first() if groups_id else None,
                    is_active=True,
                    is_defaults=is_default,
                    ss_creator=request.user,
                    ss_modifier=request.user
                )

            # Create records
            for cid in class_ids:
                if cid and cid != 'undefined':
                    create_access(class_id=cid, is_default=(cid == default_class_id))

            for sid in section_ids:
                if sid and sid != 'undefined':
                    create_access(section_id=sid, is_default=(sid == default_section_id))

            for shid in shift_ids:
                if shid and shid != 'undefined':
                    create_access(shift_id=shid, is_default=(shid == default_shift_id))

            for gid in group_ids:
                if gid and gid != 'undefined':
                    create_access(groups_id=gid, is_default=(gid == default_group_id))
            
            save_othersaccess_json_for_user(user)

            return JsonResponse({'success': True, 'msg': 'Others Access saved successfully.'})

        except Exception as e:
            return JsonResponse({'success': False, 'error_message': str(e)})

    return JsonResponse({'success': False, 'error_message': 'Invalid request method'})

# ============================================== others access ======================================

# ============================================== testing ======================================

# test perpose
@login_required
def testing_user_access_list(request):
    
    return render(request, 'user_list/test_access_list.html')