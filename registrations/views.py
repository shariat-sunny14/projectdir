import sys
import json
from PIL import Image
from io import BytesIO
from collections import defaultdict
from datetime import date, datetime
from django.db.models.functions import Cast
from django.db.models import Q, F, Sum, Prefetch, ExpressionWrapper, fields, FloatField, IntegerField, Value, Case, When
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
from subject_setup.models import in_subjects
from . models import in_registrations
from user_setup.models import access_list, lookup_values
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
    mobile_number = data.get('mobile_number')

    try:
        with transaction.atomic():
            
            if reg_id and reg_id.isnumeric() and int(reg_id) > 0:
                reg_data = in_registrations.objects.get(reg_id=reg_id)

                if mobile_number:  # শুধুমাত্র যদি mobile number থাকে তখনই চেক করবে
                    check_phone = in_registrations.objects.exclude(reg_id=reg_id).filter(mobile_number=mobile_number).exists()
                    if check_phone:
                        return JsonResponse({'success': False, 'errmsg': 'Mobile Number Already Exists'})
            else:
                if mobile_number:  # শুধুমাত্র যদি mobile number থাকে তখনই চেক করবে
                    check_phone = in_registrations.objects.filter(mobile_number=mobile_number).exists()
                    if check_phone:
                        return JsonResponse({'success': False, 'errmsg': 'Mobile Number Already Exists'})

                reg_data = in_registrations()

            # Update or set the fields based on request data
            reg_data.full_name = data.get('full_name')
            reg_data.roll_no = data.get('students_roll_no')
            reg_data.gender = data.get('gender')
            reg_data.marital_status = data.get('marital_status')
            reg_data.mobile_number = data.get('mobile_number')
            reg_data.dateofbirth = data.get('dateofbirth') or None
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
            reg_data.is_english = data.get('is_english', 0)
            reg_data.is_bangla = data.get('is_bangla', 0)

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
                
            if data.get('is_optional_sub'):
                try:
                    optional_sub_obj = in_subjects.objects.get(subjects_id=data.get('is_optional_sub'))
                except in_subjects.DoesNotExist:
                    optional_sub_obj = None
                reg_data.is_optional_sub = optional_sub_obj
            else:
                reg_data.is_optional_sub = None

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


def get_restriction_name(reg):
    restrictions = [
        ("Transferred (TC)", reg.is_transferred),
        ("Promoted & Passed Out", reg.is_promoted_passed_out),
        ("Fail & Removed", reg.is_fail_removed),
        ("Lack of Attendance", reg.is_lack_of_attendance),
        ("Rusticated", reg.is_rusticated),
        ("Expelled", reg.is_expelled),
        ("Misbehavior", reg.is_misbehavior),
        ("Policy Violation", reg.is_policy_violation),
        ("Family Shift", reg.is_family_shift),
        ("Financial Problem", reg.is_financial_problem),
        ("Personal Health Problem", reg.is_personal_health_problem),
        ("Family Decision", reg.is_family_decision),
        ("Court Ordered", reg.is_court_ordered),
        ("Government Directive", reg.is_government_directive),
        ("Death", reg.is_death),
        ("Missing", reg.is_missing),
        ("Admission Cancelled", reg.is_admission_cancelled),
        ("Unauthorized Absent", reg.is_unauthorized_absent),
    ]
    for name, flag in restrictions:
        if flag:
            return name
    return None


@login_required()
def getCustomerRegistrationsListAPI(request):
    
    user = request.user
    
    reg_list = in_registrations.objects.all()

    # Retrieve filter parameters from the frontend
    is_option = request.GET.get('is_option', None)
    is_versions = request.GET.get('is_versions', None)
    org_id = request.GET.get('org_id', None)
    branch_id = request.GET.get('branch_id', None)
    class_id = request.GET.get('class_id', None)
    section_id = request.GET.get('section_id', None)
    shift_id = request.GET.get('shift_id', None)
    groups_id = request.GET.get('groups_id', None)
    
    has_access = access_list.objects.filter(
        user_id=user,
        feature_id__feature_page_link='RESTRICTIONCONACCESSBTN',
        is_active=True
    ).exists()

    # Start with an empty Q object for dynamic filtering
    filter_kwargs = Q()

    # Apply filters based on conditions
    if is_option is not None:
        if is_option == 'true':
            filter_kwargs &= Q(is_active=True)
        elif is_option == 'false':
            filter_kwargs &= Q(is_active=False)
            filter_kwargs &= Q(
                is_transferred=False,
                is_promoted_passed_out=False,
                is_fail_removed=False,
                is_lack_of_attendance=False,
                is_rusticated=False,
                is_expelled=False,
                is_misbehavior=False,
                is_policy_violation=False,
                is_family_shift=False,
                is_financial_problem=False,
                is_personal_health_problem=False,
                is_family_decision=False,
                is_court_ordered=False,
                is_government_directive=False,
                is_death=False,
                is_missing=False,
                is_admission_cancelled=False,
                is_unauthorized_absent=False,
            )
        elif is_option == 'is_restrictioned':
            filter_kwargs &= Q(
                Q(is_transferred=True) |
                Q(is_promoted_passed_out=True) |
                Q(is_fail_removed=True) |
                Q(is_lack_of_attendance=True) |
                Q(is_rusticated=True) |
                Q(is_expelled=True) |
                Q(is_misbehavior=True) |
                Q(is_policy_violation=True) |
                Q(is_family_shift=True) |
                Q(is_financial_problem=True) |
                Q(is_personal_health_problem=True) |
                Q(is_family_decision=True) |
                Q(is_court_ordered=True) |
                Q(is_government_directive=True) |
                Q(is_death=True) |
                Q(is_missing=True) |
                Q(is_admission_cancelled=True) |
                Q(is_unauthorized_absent=True)
            )
            

    if is_versions is not None:
        if is_versions == 'english':
            filter_kwargs &= Q(is_english=True)
        elif is_versions == 'bangla':
            filter_kwargs &= Q(is_bangla=True)
        elif is_versions == 1:  # All
            # This will match records where both are True
            filter_kwargs &= Q(is_english=True, is_bangla=True)

    if org_id and org_id != 'None':
        filter_kwargs &= Q(org_id=org_id)

    if branch_id and branch_id != 'None':
        filter_kwargs &= Q(branch_id=branch_id)

    if class_id not in [None, '', 'None']:
        filter_kwargs &= Q(class_id=class_id)

    if section_id not in [None, '', 'None']:
        filter_kwargs &= Q(section_id=section_id)

    if shift_id not in [None, '', 'None']:
        filter_kwargs &= Q(shift_id=shift_id)

    if groups_id not in [None, '', 'None']:
        filter_kwargs &= Q(groups_id=groups_id)

    # Apply Q filter to the queryset
    reg_data = (
        reg_list.filter(filter_kwargs)
        .annotate(
            is_numeric=Case(
                When(roll_no__regex=r'^\d+$', then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            ),
            roll_as_int=Case(
                When(roll_no__regex=r'^\d+$', then=Cast('roll_no', IntegerField())),
                default=Value(999999999),
                output_field=IntegerField(),
            ),
        )
        .order_by('-is_numeric', 'roll_as_int', 'roll_no')   # numeric → string fallback
    )

    # Convert reg data to a list of dictionaries
    regs_data = []
    for reg in reg_data:
        restriction_name = get_restriction_name(reg)
        org_name = reg.org_id.org_name if reg.org_id else ''
        customer_img_url = reg.customer_img.url if reg.customer_img else ''

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
            # Restriction Flags
            'restriction_name': restriction_name,
            'has_access': has_access,
        })

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
def restrictionRegistrationManagerAPI(request):
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
    return render(request, 'registration/restriction_registrations.html', context)


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
            reg_data.is_transferred = False
            reg_data.is_promoted_passed_out = False
            reg_data.is_fail_removed = False
            reg_data.is_lack_of_attendance = False
            # Disciplinary
            reg_data.is_rusticated = False
            reg_data.is_expelled = False
            reg_data.is_misbehavior = False
            reg_data.is_policy_violation = False
            # Personal
            reg_data.is_family_shift = False
            reg_data.is_financial_problem = False
            reg_data.is_personal_health_problem = False
            reg_data.is_family_decision = False
            # Legal / Official
            reg_data.is_court_ordered = False
            reg_data.is_government_directive = False
            # Misc
            reg_data.is_death = False
            reg_data.is_missing = False
            reg_data.is_admission_cancelled = False
            reg_data.is_unauthorized_absent = False
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
def restrictionConfirmSubmissionAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}

    reg_id = request.POST.get('reg_id')
    reason = request.POST.get('restriction_reason')  # <-- ONE FIELD ONLY

    if not reg_id or not reason:
        resp['errmsg'] = "Invalid request or reason not selected"
        return JsonResponse(resp)

    try:
        reg = in_registrations.objects.get(pk=reg_id)

        # সব ফ্ল্যাগ false করে দিচ্ছি
        flags = [
            'is_transferred', 'is_promoted_passed_out', 'is_fail_removed',
            'is_lack_of_attendance', 'is_rusticated', 'is_expelled',
            'is_misbehavior', 'is_policy_violation', 'is_family_shift',
            'is_financial_problem', 'is_personal_health_problem',
            'is_family_decision', 'is_court_ordered', 'is_government_directive',
            'is_death', 'is_missing', 'is_admission_cancelled',
            'is_unauthorized_absent'
        ]

        for f in flags:
            setattr(reg, f, False)

        # নির্বাচিত reason = True
        setattr(reg, reason, True)
        reg.is_active = False   # student inactive
        reg.save()

        resp['success'] = True
        resp['msg'] = "Restriction added successfully"

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


@login_required()
def getOptionalSubjectsManagerAPI(request):
    if request.method == 'GET':
        org_id = request.GET.get('org_id')
        class_id = request.GET.get('class_id')
        groups_id = request.GET.get('groups_id')
        is_english = request.GET.get('is_english')
        is_bangla = request.GET.get('is_bangla')

        # Initialize filter with active and optional subjects
        filters = Q(is_active=True, is_optional=True)

        # Add filters dynamically if parameters are provided and valid
        if org_id and org_id.isdigit():
            filters &= Q(org_id_id=int(org_id))
        if class_id and class_id.isdigit():
            filters &= Q(class_id_id=int(class_id))
        if groups_id and groups_id.isdigit():
            filters &= Q(groups_id_id=int(groups_id))
        if is_english == '1':
            filters &= Q(is_english=True)
        if is_bangla == '1':
            filters &= Q(is_bangla=True)

        # Query the subjects
        subjects_qs = in_subjects.objects.filter(filters).order_by('subjects_no')

        # Prepare the list of subject dicts
        subOptions = [
            {
                'subjects_id': str(sub.subjects_id),
                'subjects_name': sub.subjects_name or '',
            }
            for sub in subjects_qs
        ]

        return JsonResponse({'subOptions': subOptions})

    # For any non-GET request, return an error response
    return JsonResponse({'error': 'Invalid request method'}, status=405)