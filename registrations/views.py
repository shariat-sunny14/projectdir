import sys
import json
from PIL import Image
from io import BytesIO
from collections import defaultdict
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
from organizations.models import branchslist, organizationlst
from class_setup.models import in_class
from groups_setup.models import in_groups
from section_setup.models import in_section
from shift_setup.models import in_shifts
from . models import in_registrations
from user_setup.models import lookup_values
from django.contrib.auth import get_user_model
User = get_user_model()

@login_required()
def RegistrationServicesManagerAPI(request):
    
    return render(request, 'registration/registration.html')


# add Registration modal
@login_required()
def addRegistrationModelManageAPI(request):
    user = request.user

    division_name = 'division'
    district_name = 'district'
    upazila_name = 'upazila'

    divisions = lookup_values.objects.filter(identify_code=division_name).all()
    districts = lookup_values.objects.filter(identify_code=district_name).all()
    upazilas = lookup_values.objects.filter(identify_code=upazila_name).all()

    context = {
        'divisions': divisions,
        'districts': districts,
        'upazilas': upazilas,
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
            reg_data.roll_no = data.get('students_roll_no')
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
            reg_data.is_versions = data.get('is_versions')

            if data.get('org_id'):
                org_obj = organizationlst.objects.get(org_id=data.get('org_id'))
                reg_data.org_id = org_obj

            if data.get('branch_id'):
                branch_obj = branchslist.objects.get(branch_id=data.get('branch_id'))
                reg_data.branch_id = branch_obj
            
            if data.get('is_class'):
                class_obj = in_class.objects.get(class_id=data.get('is_class'))
                reg_data.class_id = class_obj
            
            if data.get('is_section'):
                section_obj = in_section.objects.get(section_id=data.get('is_section'))
                reg_data.section_id = section_obj

            if data.get('is_shift'):
                shift_obj = in_shifts.objects.get(shift_id=data.get('is_shift'))
                reg_data.shift_id = shift_obj

            if data.get('is_groups'):
                try:
                    groups_obj = in_groups.objects.get(groups_id=data.get('is_groups'))
                except in_groups.DoesNotExist:
                    groups_obj = None
                reg_data.groups_id = groups_obj
            else:
                reg_data.groups_id = None

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
    is_versions = request.GET.get('is_versions', None)
    org_id = request.GET.get('org_id', None)
    branch_id = request.GET.get('branch_id', None)
    class_id = request.GET.get('class_id', None)
    section_id = request.GET.get('section_id', None)
    shift_id = request.GET.get('shift_id', None)
    groups_id = request.GET.get('groups_id', None)

    # Create an empty filter dictionary to store dynamic filter conditions
    filter_conditions = {}

    # Apply filters based on conditions
    if is_active is not None:
        # Only filter if the value is not '1', meaning we don't filter when 'All' is selected
        if is_active == 'true':
            filter_conditions['is_active'] = True
        elif is_active == 'false':
            filter_conditions['is_active'] = False
    
    if is_versions is not None:
        # Only filter if the value is not '1', meaning we don't filter when 'All' is selected
        if is_versions == 'true':
            filter_conditions['is_versions'] = True
        elif is_versions == 'false':
            filter_conditions['is_versions'] = False

    if org_id is not None and org_id != 'None':
        filter_conditions['org_id'] = org_id

    if branch_id is not None and branch_id != 'None':
        filter_conditions['branch_id'] = branch_id

    if class_id not in [None, '', 'None']:
        filter_conditions['class_id'] = class_id

    if section_id not in [None, '', 'None']:
        filter_conditions['section_id'] = section_id

    if shift_id not in [None, '', 'None']:
        filter_conditions['shift_id'] = shift_id

    if groups_id not in [None, '', 'None']:
        filter_conditions['groups_id'] = groups_id

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
            'students_no': reg.students_no,
            'full_name': reg.full_name,
            'roll_no': reg.roll_no,
            'customer_img': customer_img_url,
            'gender': reg.gender,
            'class_name': reg.class_id.class_name if reg.class_id else '',
            'section_name': reg.section_id.section_name if reg.section_id else '',
            'shift_name': reg.shift_id.shift_name if reg.shift_id else '',
            'groups_name': reg.groups_id.groups_name if reg.groups_id else 'No Groups',
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
            Q(students_no__icontains=search_query) |
            Q(mobile_number__icontains=search_query)
        )

    # Apply filters and fetch the data
    reg_data = in_registrations.objects.filter(is_active=True).filter(filter_kwargs)

    for reg in reg_data:
        data.append({
            'reg_id': reg.reg_id,
            'students_no': reg.students_no,
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
                'students_no': selected_register.students_no,
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
