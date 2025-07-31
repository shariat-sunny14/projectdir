import sys
import json
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
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
def resultFinalizationListManagerAPI(request):
    
    return render(request, 'result_finalization/result_finalization_list.html')


@login_required()
def grossResultFinalizeManagerAPI(request):
    user = request.user

    examtypelist = in_exam_type.objects.filter(is_active=True).all()

    has_access = access_list.objects.filter(
        user_id=user,
        feature_id__feature_page_link='FINALIZERESULTSAPPACC',
        is_active=True
    ).exists()

    context = {
        'examtypelist': examtypelist,
        'has_access': has_access,
    }
    return render(request, 'result_finalization/add_result_finalization.html', context)


@login_required()
def editGrossResultFinalizeManagerAPI(request):
    user = request.user

    examtypelist = in_exam_type.objects.filter(is_active=True).all()

    has_access = access_list.objects.filter(
        user_id=user,
        feature_id__feature_page_link='FINALIZERESULTSAPPACC',
        is_active=True
    ).exists()

    context = {
        'examtypelist': examtypelist,
        'has_access': has_access,
    }
    return render(request, 'result_finalization/edit_result_finalization.html', context)


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
    branch_filter = request.GET.get('filter_branch')
    filter_option = request.GET.get('filter_option')
    filter_class = request.GET.get('filter_class')
    filter_groups = request.GET.get('filter_groups')
    filter_subjects = request.GET.get('filter_subjects')
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
    if filter_groups:
        filter_kwargs &= Q(groups_id=filter_groups)
    if filter_subjects:
        filter_kwargs &= Q(subject_id=filter_subjects)

    if is_start and is_end:
        filter_kwargs &= Q(created_date__range=[is_start, is_end])
    elif is_start:
        filter_kwargs &= Q(created_date__gte=is_start)
    elif is_end:
        filter_kwargs &= Q(created_date__lte=is_end)

    results_data = in_result_finalization.objects.filter(filter_kwargs)

    data = []
    for rf in results_data:
        data.append({
            'res_fin_id': rf.res_fin_id,
            'names_of_exam': rf.names_of_exam,
            'created_date': rf.created_date.strftime('%Y-%m-%d') if rf.created_date else None,
            'exam_date': rf.exam_date.strftime('%Y-%m-%d') if rf.exam_date else None,
            'approved_date': rf.approved_date,
            'is_approved': rf.is_approved,
            'approved_by': rf.is_approved_by.get_full_name() if rf.is_approved_by else '',
        })

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
        
        def str_to_bool(val):
            if val is None:
                return False
            return str(val).lower() in ['true', '1', 'on', 'yes']

        is_cq_check = str_to_bool(data.get("is_cq_check"))
        is_cq = int(data.get("is_cq") or 0)
        is_mcq_check = str_to_bool(data.get("is_mcq_check"))
        is_mcq = int(data.get("is_mcq") or 0)
        is_written_check = str_to_bool(data.get("is_written_check"))
        is_written = int(data.get("is_written") or 0)
        is_practical_check = str_to_bool(data.get("is_practical_check"))
        is_practical = int(data.get("is_practical") or 0)
        is_oral_check = str_to_bool(data.get("is_oral_check"))
        is_oral = int(data.get("is_oral") or 0)
        is_approved = data['is_approved']
        approved_date = data.get("approved_date")
        approved_user_id = data.get("is_approved_by_user_id")
        
        
        current_year = datetime.now().year

        filter_kwargs = Q()
        filter_kwargs &= Q(finalize_year=current_year)  # filter by current year

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
        if subject_id:
            filter_kwargs &= Q(subject_id=subject_id)
        if exam_type_id:
            filter_kwargs &= Q(exam_type_id=exam_type_id)

        finalized_data = in_result_finalization.objects.filter(filter_kwargs)
        
        if finalized_data.exists():
            # If data exists for the current year, return an error
            return JsonResponse({'success': False, 'errmsg': 'Finalized Data For This Year Already Exists. Please Choose Another Exam Type.'})


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
                is_half_yearly=exam_type.is_half_yearly,
                is_yearly=exam_type.is_yearly,
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
                    org_id=org,
                    branch_id=branch,
                    class_id=class_obj,
                    section_id=section,
                    shifts_id=shift,
                    groups_id=group,
                    subject_id=subject,
                    exam_type_id=exam_type,
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
                    is_half_yearly=exam_type.is_half_yearly,
                    is_yearly=exam_type.is_yearly,
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


@login_required()
def updateResultsFinalizationManagerAPI(request):
    resp = {'status': 'failed', 'errmsg': 'Failed ...'}
    data = request.POST

    try:
        org_id = data.get("org")
        branch_id = data.get("branchs")
        class_id = data.get("is_class")
        section_id = data.get("is_section")
        shifts_id = data.get("is_shifts")
        groups_id = data.get("is_groups")
        names_of_exam = data.get("names_of_exam")
        exam_date = data.get("exam_date")
        subject_id = data.get("is_subjects")
        exam_type_id = data.get("exam_type")
        def str_to_bool(val):
            if val is None:
                return False
            return str(val).lower() in ['true', '1', 'on', 'yes']

        is_cq_check = str_to_bool(data.get("is_cq_check"))
        is_cq = int(data.get("is_cq") or 0)
        is_mcq_check = str_to_bool(data.get("is_mcq_check"))
        is_mcq = int(data.get("is_mcq") or 0)
        is_written_check = str_to_bool(data.get("is_written_check"))
        is_written = int(data.get("is_written") or 0)
        is_practical_check = str_to_bool(data.get("is_practical_check"))
        is_practical = int(data.get("is_practical") or 0)
        is_oral_check = str_to_bool(data.get("is_oral_check"))
        is_oral = int(data.get("is_oral") or 0)
        is_approved = data['is_approved']
        approved_date = data.get("approved_date")
        approved_user_id = data.get("is_approved_by_user_id")
        res_fin_id = data.get("res_fin_id")
        
        current_year = datetime.now().year

        filter_kwargs = Q()
        filter_kwargs &= Q(finalize_year=current_year)  # filter by current year

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
        if subject_id:
            filter_kwargs &= Q(subject_id=subject_id)
        if exam_type_id:
            filter_kwargs &= Q(exam_type_id=exam_type_id)

        finalized_data = in_result_finalization.objects.filter(filter_kwargs, is_approved=True)
        
        if finalized_data.exists():
            # If data exists for the current year, return an error
            return JsonResponse({'success': False, 'errmsg': 'Finalized Data For This Year Already Exists. Please Choose Another Exam Type.'})


        user_instance = None
        if approved_user_id:
            user_instance = get_object_or_404(User, user_id=approved_user_id)

        exam_type = get_object_or_404(in_exam_type, exam_type_id=exam_type_id)
        subject = get_object_or_404(in_subjects, subjects_id=subject_id)

        with transaction.atomic():
            # UPDATE or CREATE in_result_finalization
            if res_fin_id:
                ResultsFinalization = in_result_finalization.objects.get(res_fin_id=res_fin_id)
                ResultsFinalization.names_of_exam = names_of_exam
                ResultsFinalization.exam_date = datetime.strptime(exam_date, "%d-%m-%Y").date() if exam_date else None
                ResultsFinalization.subject_id = subject
                ResultsFinalization.is_cq_check = is_cq_check
                ResultsFinalization.is_cq = is_cq
                ResultsFinalization.is_mcq_check = is_mcq_check
                ResultsFinalization.is_mcq = is_mcq
                ResultsFinalization.is_written_check = is_written_check
                ResultsFinalization.is_written = is_written
                ResultsFinalization.is_practical_check = is_practical_check
                ResultsFinalization.is_practical = is_practical
                ResultsFinalization.is_oral_check = is_oral_check
                ResultsFinalization.is_oral = is_oral
                ResultsFinalization.exam_type_id = exam_type
                ResultsFinalization.is_half_yearly = exam_type.is_half_yearly
                ResultsFinalization.is_yearly = exam_type.is_yearly
                ResultsFinalization.is_approved = is_approved
                ResultsFinalization.is_approved_by = user_instance
                ResultsFinalization.approved_date = approved_date
                ResultsFinalization.ss_modifier = request.user
                ResultsFinalization.save()

            # UPDATE or CREATE in_result_finalizationdtls
            zip_datas = zip(
                data.getlist('res_findtl_id[]'),
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

            for res_findtl_id, is_cq_marks, is_cq_apval, is_mcq_marks, is_mcq_apval, is_written_marks, is_written_apval, is_practical_marks, is_practical_apval, is_oral_marks, is_oral_apval, is_grand_total_marks in zip_datas:
                try:
                    # Update existing detail
                    resFin_dtl = in_result_finalizationdtls.objects.get(res_findtl_id=res_findtl_id)
                    resFin_dtl.is_cq_marks = int(is_cq_marks or 0)
                    resFin_dtl.is_cq_apval = '1' if is_cq_apval == '1' else 0
                    resFin_dtl.is_mcq_marks = int(is_mcq_marks or 0)
                    resFin_dtl.is_mcq_apval = '1' if is_mcq_apval == '1' else 0
                    resFin_dtl.is_written_marks = int(is_written_marks or 0)
                    resFin_dtl.is_written_apval = '1' if is_written_apval == '1' else 0
                    resFin_dtl.is_practical_marks = int(is_practical_marks or 0)
                    resFin_dtl.is_practical_apval = '1' if is_practical_apval == '1' else 0
                    resFin_dtl.is_oral_marks = int(is_oral_marks or 0)
                    resFin_dtl.is_oral_apval = '1' if is_oral_apval == '1' else 0
                    resFin_dtl.grand_total_marks = int(is_grand_total_marks or 0)
                    resFin_dtl.exam_type_id = exam_type
                    resFin_dtl.is_half_yearly = exam_type.is_half_yearly
                    resFin_dtl.is_yearly = exam_type.is_yearly
                    resFin_dtl.ss_modifier = request.user
                    resFin_dtl.save()
                except Exception as e:
                    resp['errmsg'] = str(e)
                
        return JsonResponse({'success': True, 'msg': 'Student attendance updated successfully.'})

    except Exception as e:
        print("Unhandled Error:", str(e))
        resp['errmsg'] = str(e)

    return JsonResponse(resp)


@login_required()
def get_result_finalization_detailsAPI(request):
    res_fin_id = request.GET.get('res_fin_id')

    if not res_fin_id:
        return JsonResponse({'error': 'Missing res_fin_id'}, status=400)

    try:
        finalization = in_result_finalization.objects.get(res_fin_id=res_fin_id)
        details = in_result_finalizationdtls.objects.filter(res_fin_id=finalization)

        detail_list = []
        for d in details:
            detail_list.append({
                'res_findtl_id': d.res_findtl_id,
                'reg_id': d.reg_id.reg_id if d.reg_id else None,
                'full_name': d.reg_id.full_name if d.reg_id else '',
                'roll_no': d.roll_no,
                'class_name': d.class_name,
                'section_name': d.section_name,
                'shift_name': d.shift_name,
                'groups_name': d.groups_name,
                'is_cq_marks': d.is_cq_marks,
                'is_cq_apval': 1 if d.is_cq_apval else 0,
                'is_mcq_marks': d.is_mcq_marks,
                'is_mcq_apval': 1 if d.is_mcq_apval else 0,
                'is_written_marks': d.is_written_marks,
                'is_written_apval': 1 if d.is_written_apval else 0,
                'is_practical_marks': d.is_practical_marks,
                'is_practical_apval': 1 if d.is_practical_apval else 0,
                'is_oral_marks': d.is_oral_marks,
                'is_oral_apval': 1 if d.is_oral_apval else 0,
                'grand_total_marks': d.grand_total_marks,
            })

        data = {
            'finalization': {
                'res_fin_id': finalization.res_fin_id,
                'names_of_exam': finalization.names_of_exam,
                'org_id': finalization.org_id.org_id if finalization.org_id else None,
                'org_name': finalization.org_id.org_name if finalization.org_id else None,
                'branch_id': finalization.branch_id.branch_id if finalization.branch_id else None,
                'branch_name': finalization.branch_id.branch_name if finalization.branch_id else None,
                'class_id': finalization.class_id.class_id if finalization.class_id else None,
                'class_name': finalization.class_id.class_name if finalization.class_id else None,
                'section_id': finalization.section_id.section_id if finalization.section_id else None,
                'section_name': finalization.section_id.section_name if finalization.section_id else None,
                'shifts_id': finalization.shifts_id.shift_id if finalization.shifts_id else None,
                'shifts_name': finalization.shifts_id.shift_name if finalization.shifts_id else None,
                'groups_id': finalization.groups_id.groups_id if finalization.groups_id else None,
                'groups_name': finalization.groups_id.groups_name if finalization.groups_id else None,
                'exam_type_id': finalization.exam_type_id.exam_type_id if finalization.exam_type_id else None,
                'exam_type_name': finalization.exam_type_id.exam_type_name if finalization.exam_type_id else None,
                'subject_id': finalization.subject_id.subjects_id if finalization.subject_id else None,
                'subject_name': finalization.subject_id.subjects_name if finalization.subject_id else None,
                'is_cq_check': finalization.is_cq_check,
                'is_cq': finalization.is_cq,
                'is_mcq_check': finalization.is_mcq_check,
                'is_mcq': finalization.is_mcq,
                'is_written_check': finalization.is_written_check,
                'is_written': finalization.is_written,
                'is_practical_check': finalization.is_practical_check,
                'is_practical': finalization.is_practical,
                'is_oral_check': finalization.is_oral_check,
                'is_oral': finalization.is_oral,
                'exam_date': finalization.exam_date.strftime('%Y-%m-%d') if finalization.exam_date else None,
                'is_approved': finalization.is_approved,
                'approved_date': finalization.approved_date,
                'is_approved_by_id': finalization.is_approved_by.user_id if finalization.is_approved_by else None,
                'is_approved_by_name': f"{finalization.is_approved_by.first_name} {finalization.is_approved_by.last_name}" if finalization.is_approved_by else '',
            },
            'details': detail_list
        }
        return JsonResponse({'success': True, 'data': data})

    except in_result_finalization.DoesNotExist:
        return JsonResponse({'error': 'Result finalization not found'}, status=404)
    
    
@login_required()
def getHalfAndAnnualFinalizeDataExistorNotAPI(request):
    org_filter = request.GET.get('filter_org')
    branch_filter = request.GET.get('filter_branch')
    filter_option = request.GET.get('filter_option')
    filter_class = request.GET.get('filter_class')
    filter_section = request.GET.get('filter_section')
    filter_shifts = request.GET.get('filter_shifts')
    filter_groups = request.GET.get('filter_groups')
    filter_subjects = request.GET.get('filter_subjects')
    filter_exam_type = request.GET.get('filter_exam_type')

    current_year = datetime.now().year

    filter_kwargs = Q()
    filter_kwargs &= Q(finalize_year=current_year)  # filter by current year

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
    if filter_subjects:
        filter_kwargs &= Q(subject_id=filter_subjects)
    if filter_exam_type:
        filter_kwargs &= Q(exam_type_id=filter_exam_type)

    finalize_data = in_result_finalization.objects.filter(filter_kwargs)

    data = list(finalize_data.values('is_half_yearly', 'is_yearly', 'is_approved'))

    return JsonResponse({'data': data})