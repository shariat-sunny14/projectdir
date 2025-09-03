import sys
import json
from django.db.models.functions import Cast
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.db.models import Q, F, Sum, ExpressionWrapper, fields, FloatField, IntegerField, Value, Case, When
from django.db import transaction
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from organizations.models import branchslist, organizationlst
from class_setup.models import in_class
from groups_setup.models import in_groups
from section_setup.models import in_section
from shift_setup.models import in_shifts
from exam_type.models import in_exam_type
from subject_setup.models import in_subjects
from defaults_exam_mode.models import in_exam_modes
from registrations.models import in_registrations
from result_finalization.models import in_result_finalization, in_result_finalizationdtls
from attendant_manager.models import in_student_attendant, in_student_attendantdtls
from user_setup.models import access_list
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def studentAttendantListManagerAPI(request):
    
    return render(request, 'attendant_manager/attendant_manager_list.html')


@login_required()
def addNewStudentAttendantManagerAPI(request):
    user = request.user

    examtypelist = in_exam_type.objects.filter(is_active=True).filter(Q(is_half_yearly=True) | Q(is_yearly=True))

    has_access = access_list.objects.filter(
        user_id=user,
        feature_id__feature_page_link='ATTENDANTSAPPACCESS',
        is_active=True
    ).exists()

    context = {
        'examtypelist': examtypelist,
        'has_access': has_access,
    }
    return render(request, 'attendant_manager/add_new_attendants.html', context)


@login_required()
def editStudentAttendantManagerAPI(request):
    user = request.user

    examtypelist = in_exam_type.objects.filter(is_active=True).filter(Q(is_half_yearly=True) | Q(is_yearly=True))

    has_access = access_list.objects.filter(
        user_id=user,
        feature_id__feature_page_link='ATTENDANTSAPPACCESS',
        is_active=True
    ).exists()

    context = {
        'examtypelist': examtypelist,
        'has_access': has_access,
    }
    return render(request, 'attendant_manager/edit_new_attendants.html', context)


@login_required()
def get_attendant_details(request):
    attendant_id = request.GET.get('attendant_id')

    if not attendant_id:
        return JsonResponse({'error': 'Missing attendant_id'}, status=400)

    try:
        attendant = in_student_attendant.objects.get(attendant_id=attendant_id)
        # details = in_student_attendantdtls.objects.filter(attendant_id=attendant)
        details = (
            in_student_attendantdtls.objects
            .filter(attendant_id=attendant)
            .annotate(
                is_numeric=Case(
                    When(roll_no__regex=r'^\d+$', then=Value(1)),  # pure digits হলে 1
                    default=Value(0),  # নাহলে 0
                    output_field=IntegerField(),
                ),
                roll_as_int=Case(
                    When(roll_no__regex=r'^\d+$', then=Cast('roll_no', IntegerField())),
                    default=Value(999999999),  # non-numeric হলে একেবারে শেষে
                    output_field=IntegerField(),
                )
            )
            .order_by('-is_numeric', 'roll_as_int', 'roll_no')  
        )

        detail_list = []
        for d in details:
            detail_list.append({
                'attendantdtl_id': d.attendantdtl_id,
                'reg_id': d.reg_id.reg_id if d.reg_id else None,
                'roll_no': d.roll_no,
                'class_name': d.class_name,
                'section_name': d.section_name,
                'shift_name': d.shift_name,
                'groups_name': d.groups_name,
                'attendant_qty': d.attendant_qty,
                'full_name': d.reg_id.full_name if d.reg_id else '',
            })

        data = {
            'attendant': {
                'attendant_id': attendant.attendant_id,
                'org_id': attendant.org_id.org_id if attendant.org_id else None,
                'org_name': attendant.org_id.org_name if attendant.org_id else None,
                'branch_id': attendant.branch_id.branch_id if attendant.branch_id else None,
                'branch_name': attendant.branch_id.branch_name if attendant.branch_id else None,
                'class_id': attendant.class_id.class_id if attendant.class_id else None,
                'class_name': attendant.class_id.class_name if attendant.class_id else None,
                'section_id': attendant.section_id.section_id if attendant.section_id else None,
                'section_name': attendant.section_id.section_name if attendant.section_id else None,
                'shifts_id': attendant.shifts_id.shift_id if attendant.shifts_id else None,
                'shifts_name': attendant.shifts_id.shift_name if attendant.shifts_id else None,
                'groups_id': attendant.groups_id.groups_id if attendant.groups_id else None,
                'groups_name': attendant.groups_id.groups_name if attendant.groups_id else None,
                'exam_type_id': attendant.exam_type_id.exam_type_id if attendant.exam_type_id else None,
                'exam_type_name': attendant.exam_type_id.exam_type_name if attendant.exam_type_id else None,
                'trans_date': attendant.trans_date,
                'working_days': attendant.working_days,
                'is_english': attendant.is_english,
                'is_bangla': attendant.is_bangla,
                'is_approved': attendant.is_approved,
                'approved_date': attendant.approved_date,
                'is_approved_by_id': attendant.is_approved_by.user_id if attendant.is_approved_by else None,
                'is_approved_by_name': f"{attendant.is_approved_by.first_name} {attendant.is_approved_by.last_name}" if attendant.is_approved_by else '',
            },
            'details': detail_list
        }
        return JsonResponse({'success': True, 'data': data})

    except in_student_attendant.DoesNotExist:
        return JsonResponse({'error': 'Attendant not found'}, status=404)

@login_required()
def saveStudentAttendantManagerAPI(request):
    resp = {'status': 'failed', 'errmsg': 'Failed ...'}
    data = request.POST

    try:
        org_id = data.get("org")
        branch_id = data.get("branchs")
        class_id = data.get("is_class")
        section_id = data.get("is_section")
        shifts_id = data.get("is_shifts")
        groups_id = data.get("is_groups")
        exam_type_id = data.get("exam_type")
        working_days = data.get("working_days")
        is_version = data.get("is_version")
        is_approved = data['is_approved']
        approved_date = data.get("approved_date")
        approved_user_id = data.get("is_approved_by_user_id")
        
        current_year = datetime.now().year

        filter_kwargs = Q()
        filter_kwargs &= Q(attendant_year=current_year)  # filter by current year

        if org_id:
            filter_kwargs &= Q(org_id=org_id)
        if branch_id:
            filter_kwargs &= Q(branch_id=branch_id)
        if class_id:
            filter_kwargs &= Q(class_id=class_id)
        if section_id:
            filter_kwargs &= Q(section_id=section_id)
        if shifts_id:
            filter_kwargs &= Q(shifts_id=shifts_id)
        if groups_id:
            filter_kwargs &= Q(groups_id=groups_id)
        if exam_type_id:
            filter_kwargs &= Q(exam_type_id=exam_type_id)
        if is_version == 'english':
            is_english = True
            is_bangla = False
        if is_version == 'bangla':
            is_english = False
            is_bangla = True
            

        attendant_data = in_student_attendant.objects.filter(filter_kwargs)
        
        if attendant_data.exists():
            # If data exists for the current year, return an error
            return JsonResponse({'success': False, 'errmsg': 'Attendance Data For This Year Already Exists. Please Choose Another Exam Type.'})

        # Get approver user instance
        user_instance = None
        if approved_user_id:
            try:
                user_instance = User.objects.get(user_id=approved_user_id)
            except User.DoesNotExist:
                return JsonResponse({'errmsg': 'Approver user not found.'}, status=400)

        with transaction.atomic():
            org = organizationlst.objects.get(org_id=org_id)
            branch = branchslist.objects.get(branch_id=branch_id)
            class_obj = in_class.objects.get(class_id=class_id)
            section = in_section.objects.get(section_id=section_id)
            shift = in_shifts.objects.get(shift_id=shifts_id)
            exam_type = in_exam_type.objects.get(exam_type_id=exam_type_id)
            group = in_groups.objects.get(groups_id=groups_id) if groups_id else None

            studentAttendant = in_student_attendant.objects.create(
                org_id=org,
                branch_id=branch,
                class_id=class_obj,
                section_id=section,
                shifts_id=shift,
                groups_id=group,
                exam_type_id=exam_type,
                working_days=int(working_days or 0),
                is_half_yearly=exam_type.is_half_yearly,
                is_yearly=exam_type.is_yearly,
                is_english=is_english,
                is_bangla=is_bangla,
                is_approved=is_approved,
                is_approved_by=user_instance,
                approved_date=approved_date,
                ss_creator=request.user
            )

            zip_datas = zip(
                data.getlist('is_reg_id[]'),
                data.getlist('is_roll_no[]'),
                data.getlist('is_class_name[]'),
                data.getlist('is_section_name[]'),
                data.getlist('is_shift_name[]'),
                data.getlist('is_groups_name[]'),
                data.getlist('attendant_qty[]'),
            )

            for fields in zip_datas:
                (
                    reg_id, roll_no, class_name, section_name, shift_name, groups_name, attendant_qty
                ) = fields

                reg_instance = in_registrations.objects.get(reg_id=reg_id)

                studentAttendantDtl = in_student_attendantdtls.objects.create(
                    attendant_id=studentAttendant,
                    org_id=org,
                    branch_id=branch,
                    class_id=class_obj,
                    section_id=section,
                    shifts_id=shift,
                    groups_id=group,
                    exam_type_id=exam_type,
                    reg_id=reg_instance,
                    roll_no=roll_no,
                    class_name=class_name,
                    section_name=section_name,
                    shift_name=shift_name,
                    groups_name=groups_name,
                    attendant_qty=int(attendant_qty or 0),
                    is_half_yearly=exam_type.is_half_yearly,
                    is_yearly=exam_type.is_yearly,
                    is_english=is_english,
                    is_bangla=is_bangla,
                    is_approved=is_approved,
                    is_approved_by=user_instance,
                    approved_date=approved_date,
                    ss_creator=request.user
                )

        return JsonResponse({'success': True, 'msg': 'Student attendance saved successfully.'})

    except organizationlst.DoesNotExist:
        resp['errmsg'] = 'Invalid organization ID.'
    except branchslist.DoesNotExist:
        resp['errmsg'] = 'Invalid branch ID.'
    except in_class.DoesNotExist:
        resp['errmsg'] = 'Invalid class ID.'
    except in_section.DoesNotExist:
        resp['errmsg'] = 'Invalid section ID.'
    except in_shifts.DoesNotExist:
        resp['errmsg'] = 'Invalid shift ID.'
    except in_exam_type.DoesNotExist:
        resp['errmsg'] = 'Invalid exam type ID.'
    except in_groups.DoesNotExist:
        resp['errmsg'] = 'Invalid group ID.'
    except in_registrations.DoesNotExist:
        resp['errmsg'] = 'Invalid registration ID.'
    except Exception as e:
        print("Unhandled Error:", str(e))
        resp['errmsg'] = str(e)

    return HttpResponse(json.dumps(resp), content_type="application/json")


@login_required()
def updateStudentAttendantManagerAPI(request):
    resp = {'status': 'failed', 'errmsg': 'Failed ...'}
    data = request.POST

    try:
        org_id = data.get("id_org_id")
        branch_id = data.get("id_branch_id")
        class_id = data.get("id_class_id")
        section_id = data.get("id_section_id")
        shifts_id = data.get("id_shift_id")
        groups_id = data.get("id_group_id")
        exam_type_id = data.get("exam_type")
        working_days = data.get("working_days")
        is_approved = data['is_approved']
        approved_date = data.get("approved_date")
        approved_user_id = data.get("is_approved_by_user_id")
        attendant_id = data.get("attendant_id")
        is_version = data.get("is_version")
        
        current_year = datetime.now().year

        filter_kwargs = Q()
        filter_kwargs &= Q(attendant_year=current_year)  # filter by current year

        if org_id:
            filter_kwargs &= Q(org_id=org_id)
        if branch_id:
            filter_kwargs &= Q(branch_id=branch_id)
        if class_id:
            filter_kwargs &= Q(class_id=class_id)
        if section_id:
            filter_kwargs &= Q(section_id=section_id)
        if shifts_id:
            filter_kwargs &= Q(shifts_id=shifts_id)
        if groups_id:
            filter_kwargs &= Q(groups_id=groups_id)
        if exam_type_id:
            filter_kwargs &= Q(exam_type_id=exam_type_id)
        if is_version == 'english':
            is_english = True
            is_bangla = False
        if is_version == 'bangla':
            is_english = False
            is_bangla = True
        

        attendant_data = in_student_attendant.objects.filter(filter_kwargs, is_approved=True)
        
        if attendant_data.exists():
            # If data exists for the current year, return an error
            return JsonResponse({'success': False, 'errmsg': 'Attendance Data For This Year Already Exists. Please Choose Another Exam Type.'})


        user_instance = None
        if approved_user_id:
            user_instance = get_object_or_404(User, user_id=approved_user_id)

        exam_type = get_object_or_404(in_exam_type, exam_type_id=exam_type_id)

        with transaction.atomic():
            # UPDATE or CREATE in_student_attendant
            if attendant_id:
                studentAttendant = in_student_attendant.objects.get(attendant_id=attendant_id)
                studentAttendant.exam_type_id = exam_type
                studentAttendant.is_half_yearly = exam_type.is_half_yearly
                studentAttendant.is_yearly = exam_type.is_yearly
                studentAttendant.working_days = int(working_days or 0)
                studentAttendant.is_english=is_english
                studentAttendant.is_bangla=is_bangla
                studentAttendant.is_approved = is_approved
                studentAttendant.is_approved_by = user_instance
                studentAttendant.approved_date = approved_date
                studentAttendant.ss_modifier = request.user
                studentAttendant.save()

            # UPDATE or CREATE in_student_attendantdtls
            zip_datas = zip(
                data.getlist('attendantdtl_id[]'),
                data.getlist('attendant_qty[]'),
            )

            for attendantdtl_id, attendant_qty in zip_datas:
                try:
                    # Update existing detail
                    att_dtl = in_student_attendantdtls.objects.get(attendantdtl_id=attendantdtl_id)
                    att_dtl.attendant_qty = int(attendant_qty or 0)
                    att_dtl.exam_type_id = exam_type
                    att_dtl.is_half_yearly = exam_type.is_half_yearly
                    att_dtl.is_yearly = exam_type.is_yearly
                    att_dtl.is_english=is_english
                    att_dtl.is_bangla=is_bangla
                    att_dtl.is_approved = is_approved
                    att_dtl.is_approved_by = user_instance
                    att_dtl.approved_date = approved_date
                    att_dtl.ss_modifier = request.user
                    att_dtl.save()
                except Exception as e:
                    resp['errmsg'] = str(e)
                
        return JsonResponse({'success': True, 'msg': 'Student attendance updated successfully.'})

    except Exception as e:
        print("Unhandled Error:", str(e))
        resp['errmsg'] = str(e)

    return JsonResponse(resp)


@login_required()
def getStudentAttendantListManagerAPI(request):
    org_filter = request.GET.get('filter_org')
    branch_filter = request.GET.get('filter_branch')
    filter_option = request.GET.get('filter_option')
    filter_class = request.GET.get('filter_class')
    filter_section = request.GET.get('filter_section')
    filter_shifts = request.GET.get('filter_shifts')
    filter_groups = request.GET.get('filter_groups')
    is_version = request.GET.get('filter_version')
    filter_exam_type = request.GET.get('filter_exam_type')  # corrected key
    is_start = request.GET.get('is_start')
    is_end = request.GET.get('is_end')

    filter_kwargs = Q()

    if org_filter:
        filter_kwargs &= Q(org_id=org_filter)
    if branch_filter:
        filter_kwargs &= Q(branch_id=branch_filter)
    if filter_option in ['true', 'false']:
        filter_kwargs &= Q(is_approved=(filter_option == 'true'))
    if filter_class:
        filter_kwargs &= Q(class_id=filter_class)
    if filter_section:
        filter_kwargs &= Q(section_id=filter_section)
    if filter_shifts:
        filter_kwargs &= Q(shifts_id=filter_shifts)
    if filter_groups:
        filter_kwargs &= Q(groups_id=filter_groups)
    if filter_exam_type:
        filter_kwargs &= Q(exam_type_id=filter_exam_type)  # correct field in model

    if is_start and is_end:
        filter_kwargs &= Q(trans_date__range=[is_start, is_end])
    elif is_start:
        filter_kwargs &= Q(trans_date__gte=is_start)
    elif is_end:
        filter_kwargs &= Q(trans_date__lte=is_end)
    
    if is_version == 'english':
        filter_kwargs &= Q(is_english=True)
    if is_version == 'bangla':
        filter_kwargs &= Q(is_bangla=True)

    attendant_data = in_student_attendant.objects.filter(filter_kwargs)

    data = []
    for att in attendant_data:
        data.append({
            'attendant_id': att.attendant_id,
            'trans_date': att.trans_date,
            'attendant_year': att.attendant_year,
            'is_half_yearly': att.is_half_yearly,
            'is_yearly': att.is_yearly,
            'approved_date': att.approved_date,
            'is_approved': att.is_approved,
            'approved_by': att.is_approved_by.get_full_name() if att.is_approved_by else '',
        })

    return JsonResponse({'data': data})


@login_required()
def getHalfAndAnnualDataExistorNotManagerAPI(request):
    org_filter = request.GET.get('filter_org')
    branch_filter = request.GET.get('filter_branch')
    filter_option = request.GET.get('filter_option')
    filter_class = request.GET.get('filter_class')
    filter_section = request.GET.get('filter_section')
    filter_shifts = request.GET.get('filter_shifts')
    filter_groups = request.GET.get('filter_groups')
    filter_exam_type = request.GET.get('filter_exam_type')

    current_year = datetime.now().year

    filter_kwargs = Q()
    filter_kwargs &= Q(attendant_year=current_year)  # filter by current year

    if org_filter:
        filter_kwargs &= Q(org_id=org_filter)
    if branch_filter:
        filter_kwargs &= Q(branch_id=branch_filter)
    if filter_option in ['true', 'false']:
        filter_kwargs &= Q(is_approved=(filter_option == 'true'))
    if filter_class:
        filter_kwargs &= Q(class_id=filter_class)
    if filter_section:
        filter_kwargs &= Q(section_id=filter_section)
    if filter_shifts:
        filter_kwargs &= Q(shifts_id=filter_shifts)
    if filter_groups:
        filter_kwargs &= Q(groups_id=filter_groups)
    if filter_exam_type:
        filter_kwargs &= Q(exam_type_id=filter_exam_type)

    attendant_data = in_student_attendant.objects.filter(filter_kwargs)

    data = list(attendant_data.values('is_half_yearly', 'is_yearly', 'is_approved'))

    return JsonResponse({'data': data})