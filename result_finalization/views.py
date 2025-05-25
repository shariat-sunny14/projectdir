import sys
import json
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from datetime import datetime
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.db.models import Q, F, Sum, ExpressionWrapper, fields, FloatField
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
from user_setup.models import access_list
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def grossResultFinalizeManagerAPI(request):
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

    classlist = in_class.objects.filter(is_active=True).all()
    sectionlist = in_section.objects.filter(is_active=True).all()
    shiftslist = in_shifts.objects.filter(is_active=True).all()
    groupslist = in_groups.objects.filter(is_active=True).all()
    examtypelist = in_exam_type.objects.filter(is_active=True).all()
    reslist = in_registrations.objects.filter(is_active=True).all()

    has_access = access_list.objects.filter(
        user_id=user,
        feature_id__feature_page_link='FINALIZERESULTSAPPACC',
        is_active=True
    ).exists()

    context = {
        'org_list': org_list,
        'classlist': classlist,
        'sectionlist': sectionlist,
        'shiftslist': shiftslist,
        'groupslist': groupslist,
        'examtypelist': examtypelist,
        'has_access': has_access,
    }
    return render(request, 'result_finalization/result_finalization.html', context)


@login_required()
def getSubjectsOptionsManagerAPI(request):
    if request.method == 'GET':
        org_id = request.GET.get('org_id')
        class_id = request.GET.get('class_id')
        groups_id = request.GET.get('groups_id')

        filters = {
            'is_active': True,
        }
        if org_id:
            filters['org_id'] = org_id
        if class_id:
            filters['class_id'] = class_id
        if groups_id:
            filters['groups_id'] = groups_id

        # Querying with filters
        subjects_qs = in_subjects.objects.filter(**filters)

        # Serialize subject data
        subOptions = [
            {
                'subjects_id': str(sub.subjects_id),
                'subjects_name': sub.subjects_name or ''
            }
            for sub in subjects_qs
        ]

        return JsonResponse({'subOptions': subOptions})

    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required()
def getDefaultsExamModesManagerAPI(request):
    org_id = request.GET.get('org_id')
    class_id = request.GET.get('class_id')

    modes = in_exam_modes.objects.filter(
        org_id=org_id,
        class_id=class_id,
        is_active=True
    ).values('is_exam_modes', 'is_default_marks')

    return JsonResponse(list(modes), safe=False)

@login_required()
def getRegListDetailsForFinalizedResultsAPI(request):
    org_filter = request.GET.get('filter_org')
    branch_filter = request.GET.get('filter_branch')
    filter_class = request.GET.get('filter_class')
    filter_section = request.GET.get('filter_section')
    filter_shift = request.GET.get('filter_shift')
    filter_groups = request.GET.get('filter_groups')

    filter_kwargs = Q()

    if org_filter:
        filter_kwargs &= Q(org_id=org_filter)

    if branch_filter:
        filter_kwargs &= Q(branch_id=branch_filter)

    if filter_class:
        filter_kwargs &= Q(class_id=filter_class)

    if filter_section:
        filter_kwargs &= Q(section_id=filter_section)

    if filter_shift:
        filter_kwargs &= Q(shift_id=filter_shift)

    if filter_groups:
        filter_kwargs &= Q(groups_id=filter_groups)

    reg_data = in_registrations.objects.filter(filter_kwargs)

    data = []
    for reglist in reg_data:
        data.append({
            'reg_id': reglist.reg_id,
            'students_no': reglist.students_no,
            'org_name': getattr(reglist.org_id, 'org_name', None),
            'branch_name': getattr(reglist.branch_id, 'branch_name', None),
            'class_name': getattr(reglist.class_id, 'class_name', None),
            'section_name': getattr(reglist.section_id, 'section_name', None),
            'shift_name': getattr(reglist.shift_id, 'shift_name', None),
            'groups_name': getattr(reglist.groups_id, 'groups_name', 'N/A'),
            'full_name': reglist.full_name,
            'roll_no': reglist.roll_no,
        })

    return JsonResponse({'data': data})


@login_required()
def getResultsFinalizationListManagerAPI(request):
    org_filter = request.GET.get('filter_org')
    filter_option = request.GET.get('filter_option')
    filter_class = request.GET.get('filter_class')
    filter_groups = request.GET.get('filter_groups')
    filter_subjects = request.GET.get('filter_subjects')

    filter_kwargs = Q()

    if org_filter:
        filter_kwargs &= Q(org_id=org_filter)

    if filter_option in ['true', 'false']:
        filter_kwargs &= Q(is_approved=(filter_option == 'true'))

    if filter_class:
        filter_kwargs &= Q(class_id=filter_class)

    if filter_groups:
        filter_kwargs &= Q(groups_id=filter_groups)

    if filter_subjects:
        filter_kwargs &= Q(subject_id=filter_subjects)  # Fix typo: 'subject_id' not 'subjects_id'

    resultsfinal_data = in_result_finalization.objects.filter(filter_kwargs)

    data = [{
        'res_fin_id': rfdata.res_fin_id,
        'names_of_exam': rfdata.names_of_exam,
    } for rfdata in resultsfinal_data]

    return JsonResponse({'data': data})


# is_approved = data['is_approved']

@login_required()
def saveResultsFinalizationManagerAPI(request):
    resp = {'status': 'failed', 'errmsg': 'Failed ...'}
    data = request.POST

    try:
        names_of_exam = data.get("names_of_exam")
        org_id = data.get("org")
        branch_id = data.get("branchs")
        exam_date = data.get("exam_date")
        class_id = data.get("is_class")
        section_id = data.get("is_section")
        shifts_id = data.get("is_shifts")
        groups_id = data.get("is_groups")
        subject_id = data.get("is_subjects")
        exam_type_id = data.get("exam_type")

        is_cq_check = data.get("is_cq_check") == 'true'
        is_cq = int(data.get("is_cq") or 0)
        is_mcq_check = data.get("is_mcq_check") == 'true'
        is_mcq = int(data.get("is_mcq") or 0)
        is_written_check = data.get("is_written_check") == 'true'
        is_written = int(data.get("is_written") or 0)
        is_practical_check = data.get("is_practical_check") == 'true'
        is_practical = int(data.get("is_practical") or 0)
        is_oral_check = data.get("is_oral_check") == 'true'
        is_oral = int(data.get("is_oral") or 0)
        is_approved = data['is_approved']
        approved_date = data.get("approved_date")
        approved_user_id = data.get("is_approved_by_user_id")

        # Handle exam_date parsing
        exam_date_obj = None
        if exam_date:
            try:
                exam_date_obj = datetime.strptime(exam_date, "%d-%m-%Y").date()
            except ValueError:
                resp['errmsg'] = f"Invalid exam date format: {exam_date}. Expected DD-MM-YYYY."
                return JsonResponse(resp)

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
            subject = in_subjects.objects.get(subjects_id=subject_id)
            exam_type = in_exam_type.objects.get(exam_type_id=exam_type_id)
            group = in_groups.objects.get(groups_id=groups_id) if groups_id else None

            result_finalization = in_result_finalization.objects.create(
                names_of_exam=names_of_exam,
                exam_date=exam_date_obj,
                org_id=org,
                branch_id=branch,
                class_id=class_obj,
                section_id=section,
                shifts_id=shift,
                groups_id=group,
                subject_id=subject,
                exam_type_id=exam_type,
                is_cq_check=is_cq_check,
                is_cq=is_cq,
                is_mcq_check=is_mcq_check,
                is_mcq=is_mcq,
                is_written_check=is_written_check,
                is_written=is_written,
                is_practical_check=is_practical_check,
                is_practical=is_practical,
                is_oral_check=is_oral_check,
                is_oral=is_oral,
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
                data.getlist('is_cq_marks[]'),
                data.getlist('is_cq_apval[]'),
                data.getlist('is_mcq_marks[]'),
                data.getlist('is_mcq_apval[]'),
                data.getlist('is_written_marks[]'),
                data.getlist('is_written_apval[]'),
                data.getlist('is_practical_marks[]'),
                data.getlist('is_practical_apval[]'),
                data.getlist('is_oral_marks[]'),
                data.getlist('is_oral_apval[]'),
                data.getlist('is_grand_total_marks[]'),
            )

            for fields in zip_datas:
                (
                    reg_id, roll_no, class_name, section_name, shift_name, groups_name,
                    cq_marks, cq_apval, mcq_marks, mcq_apval, written_marks, written_apval,
                    practical_marks, practical_apval, oral_marks, oral_apval, grand_total
                ) = fields

                reg_instance = in_registrations.objects.get(reg_id=reg_id)

                resultFinalizationDtl = in_result_finalizationdtls.objects.create(
                    res_fin_id=result_finalization,
                    reg_id=reg_instance,
                    roll_no=roll_no,
                    class_name=class_name,
                    section_name=section_name,
                    shift_name=shift_name,
                    groups_name=groups_name,
                    is_cq_marks=int(cq_marks or 0),
                    is_cq_apval=cq_apval == '1',
                    is_mcq_marks=int(mcq_marks or 0),
                    is_mcq_apval=mcq_apval == '1',
                    is_written_marks=int(written_marks or 0),
                    is_written_apval=written_apval == '1',
                    is_practical_marks=int(practical_marks or 0),
                    is_practical_apval=practical_apval == '1',
                    is_oral_marks=int(oral_marks or 0),
                    is_oral_apval=oral_apval == '1',
                    grand_total_marks=int(grand_total or 0),
                    ss_creator=request.user
                )

        return JsonResponse({'success': True, 'msg': 'Result finalization saved successfully.'})

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
    except in_subjects.DoesNotExist:
        resp['errmsg'] = 'Invalid subject ID.'
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
