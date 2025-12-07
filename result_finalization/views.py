import sys
import json
import base64, zlib, json
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
from defaults_exam_mode.models import defaults_exam_modes, in_exam_modes
from registrations.models import in_registrations
from result_finalization.models import in_result_finalization, in_result_finalizationdtls
from user_setup.models import access_list
from django.contrib.auth import get_user_model
User = get_user_model()

@login_required()
def resultFinalizationListManagerAPI(request):
    
    examtypelist = in_exam_type.objects.filter(is_active=True).all()
    
    context = {
        'examtypelist': examtypelist,
    }
    
    return render(request, 'result_finalization/result_finalization_list.html', context)


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
def approvedRollbackFinalizeManagerAPI(request):
    finalize_data = {}
    if request.method == 'GET':
        data = request.GET
        res_fin_id = ''
        if 'res_fin_id' in data:
            res_fin_id = data['res_fin_id']
        if res_fin_id.isnumeric() and int(res_fin_id) > 0:
            finalize_data = in_result_finalization.objects.filter(res_fin_id=res_fin_id).first()

    context = {
        'finalize_data': finalize_data,
    }
    return render(request, 'result_finalization/approved_rollback_finalization.html', context)


@login_required()
def approvedRollbackFinalizeSubmissionAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST
    res_fin_id = data.get('res_fin_id')

    try:
        with transaction.atomic():

            # ---- Fetch Parent Table ----
            fin_data = in_result_finalization.objects.get(res_fin_id=res_fin_id)

            # ---- Check current year match ----
            current_year = datetime.now().year
            if fin_data.finalize_year != current_year:
                resp['errmsg'] = f"Rollback failed! Finalization year ({fin_data.finalize_year}) does not match current year ({current_year})."
                return JsonResponse(resp)

            # ---- Update Parent Table ----
            fin_data.is_approved = False
            fin_data.is_approved_by = None
            fin_data.approved_date = None
            fin_data.ss_modifier = request.user
            fin_data.save()

            # ---- Update Child Table ----
            in_result_finalizationdtls.objects.filter(res_fin_id=fin_data).update(
                is_approved=False,
                is_approved_by=None,
                approved_date=None,
                ss_modifier=request.user
            )

            resp['success'] = True
            resp['msg'] = "Attendance rollback completed successfully"

    except in_result_finalization.DoesNotExist:
        resp['errmsg'] = "Attendance record not found"

    except Exception as e:
        resp['errmsg'] = str(e)

    return JsonResponse(resp)


@login_required()
def reportResultsFinalizationsAPI(request):
    
    return render(request, 'result_finalization/report/report_results_finalization.html')


@login_required()
def getResultsFinalizationDetailsReportAPI(request):
    
    res_fin_id = request.GET.get('res_fin_id')

    if not res_fin_id:
        return JsonResponse({"success": False, "message": "res_fin_id missing"}, status=400)

    try:
        final_obj = in_result_finalization.objects.select_related("org_id").get(res_fin_id=res_fin_id)
    except in_result_finalization.DoesNotExist:
        return JsonResponse({"success": False, "message": "Invalid res_fin_id"}, status=400)

    org = final_obj.org_id

    header_info = {
        "org_name": org.org_name,
        "address": org.address,
        "email": org.email,
        "website": org.website,
        "phone_hotline": org.hotline,
        "fax": org.fax,
        "branch_name": final_obj.branch_id.branch_name if hasattr(final_obj, "branch_id") else "",
        "exam_line": "Half-Yearly Results Finalization Report" if final_obj.is_half_yearly else "Annual Results Finalization Report",
        "changed_info": f"Changed By: {final_obj.ss_modifier} at {final_obj.ss_modified_on}",
    }

    dtls = in_result_finalizationdtls.objects.filter(
        res_fin_id=res_fin_id
    ).select_related(
        'reg_id', 'class_id', 'section_id', 'shifts_id',
        'groups_id', 'subject_id', 'exam_type_id'
    )

    data_dict = {}

    for d in dtls:
        key = f"{d.reg_id.reg_id}-{d.subject_id.subjects_id}"

        if key not in data_dict:
            data_dict[key] = {
                "full_name": d.reg_id.full_name,
                "roll_no": d.reg_id.roll_no,
                "class_name": d.class_id.class_name if d.class_id else "",
                "section_name": d.section_id.section_name if d.section_id else "",
                "shift_name": d.shifts_id.shift_name if d.shifts_id else "",
                "group_name": d.groups_id.groups_name if d.groups_id else "",
                "subject_name": d.subject_id.subjects_name if d.subject_id else "",
                "exam_type_name": d.exam_type_id.exam_type_name,
                "modes": []
            }

        data_dict[key]["modes"].append({
            "is_mode_name": d.is_mode_name,
            "is_actual_marks": d.is_actual_marks,
            "is_absent_present": True if d.is_absent_present else False
        })

    # ----------- SORTING HERE -----------
    final_data = list(data_dict.values())

    def roll_sort_key(item):
        roll = str(item["roll_no"])
        return (0, int(roll)) if roll.isdigit() else (1, roll)

    final_data_sorted = sorted(final_data, key=roll_sort_key)

    return JsonResponse({
        "success": True,
        "header": header_info,
        "data": final_data_sorted
    }, safe=False)


@login_required()
def getSubjectsOptionsManagerAPI(request):
    if request.method == 'GET':
        org_id = request.GET.get('org_id')
        class_id = request.GET.get('class_id')
        groups_id = request.GET.get('groups_id')
        is_english = request.GET.get('is_english')
        is_bangla = request.GET.get('is_bangla')
        is_version = request.GET.get('is_version')

        # Start with a Q object for dynamic filtering
        filters = Q(is_active=True)

        if org_id:
            filters &= Q(org_id_id=org_id)
        if class_id:
            filters &= Q(class_id_id=class_id)
        if groups_id:
            filters &= Q(groups_id_id=groups_id)
        if is_english == '1':
            filters &= Q(is_english=True)
        if is_bangla == '1':
            filters &= Q(is_bangla=True)
        if is_version == 'english':
            filters &= Q(is_english=True)
        if is_version == 'bangla':
            filters &= Q(is_bangla=True)

        # Fetch matching subjects
        subjects_qs = in_subjects.objects.filter(filters).order_by('subjects_no')

        # Serialize subject data
        subOptions = [
            {
                'subjects_id': str(sub.subjects_id),
                'subjects_name': sub.subjects_name or '',
                'is_defaults_marks': sub.is_marks or '',
                'is_pass_marks': sub.is_pass_marks or '',
                'is_optional': sub.is_optional,
            }
            for sub in subjects_qs
        ]

        return JsonResponse({'subOptions': subOptions})

    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required()
def getDefaultsExamModesManagerAPI(request):
    org_id = request.GET.get('org_id')
    class_id = request.GET.get('class_id')
    subjects_id = request.GET.get('subjects_id')
    exam_type_id = request.GET.get('exam_type_id')

    modes = in_exam_modes.objects.filter(
        org_id=org_id,
        class_id=class_id,
        subjects_id=subjects_id,
        exam_type_id=exam_type_id,
        is_active=True
    ).values('is_exam_modes', 'is_default_marks', 'is_pass_marks')

    return JsonResponse(list(modes), safe=False)

@login_required()
def getRegListDetailsForFinalizedResultsAPI(request):
    org_filter = request.GET.get('filter_org')
    branch_filter = request.GET.get('filter_branch')
    filter_class = request.GET.get('filter_class')
    filter_section = request.GET.get('filter_section')
    filter_shift = request.GET.get('filter_shift')
    filter_groups = request.GET.get('filter_groups')
    filter_version = request.GET.get('is_version')

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
    
    if filter_version == 'english':
        filter_kwargs &= Q(is_english=True)
    if filter_version == 'bangla':
        filter_kwargs &= Q(is_bangla=True)

    # reg_data = in_registrations.objects.filter(filter_kwargs).order_by('roll_no')
    reg_data = (
        in_registrations.objects
        .filter(filter_kwargs, is_active=True)
        .annotate(
            is_numeric=Case(
                When(roll_no__regex=r'^\d+$', then=Value(1)),  # শুধু digit হলে
                default=Value(0),
                output_field=IntegerField(),
            ),
            roll_as_int=Case(
                When(roll_no__regex=r'^\d+$', then=Cast('roll_no', IntegerField())),  
                default=Value(999999999),  # non-numeric হলে অনেক বড় সংখ্যা
                output_field=IntegerField(),
            )
        )
        .order_by('-is_numeric', 'roll_as_int', 'roll_no')  
    )

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
    
    user = request.user
    
    org_filter = request.GET.get('filter_org')
    branch_filter = request.GET.get('filter_branch')
    filter_option = request.GET.get('filter_option')
    filter_class = request.GET.get('filter_class')
    filter_section = request.GET.get('filter_section')
    filter_shifts = request.GET.get('filter_shifts')
    filter_groups = request.GET.get('filter_groups')
    filter_subjects = request.GET.get('filter_subjects')
    is_version = request.GET.get('filter_version')
    filter_exam_type = request.GET.get('filter_exam_type')
    is_start = request.GET.get('is_start')
    is_end = request.GET.get('is_end')
    
    has_access = access_list.objects.filter(
        user_id=user,
        feature_id__feature_page_link='FINALIZERESULTSAPPROLLBACKACC',
        is_active=True
    ).exists()

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
        
    if filter_exam_type:
        filter_kwargs &= Q(exam_type_id=filter_exam_type)

    if filter_groups:
        filter_kwargs &= Q(groups_id=filter_groups)
        
    if filter_subjects:
        filter_kwargs &= Q(subject_id=filter_subjects)
    
    if is_version == 'english':
        filter_kwargs &= Q(is_english=True)
    if is_version == 'bangla':
        filter_kwargs &= Q(is_bangla=True)

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
            'class_name': rf.class_id.class_name if rf.class_id else None,
            'subjects_name': rf.subject_id.subjects_name if rf.subject_id else None,
            'created_date': rf.created_date.strftime('%Y-%m-%d') if rf.created_date else None,
            'exam_date': rf.exam_date.strftime('%Y-%m-%d') if rf.exam_date else None,
            'approved_date': rf.approved_date,
            'is_approved': rf.is_approved,
            'approved_by': rf.is_approved_by.get_full_name() if rf.is_approved_by else '',
            'has_access': has_access,
        })

    return JsonResponse({'data': data})


# is_approved = data['is_approved']

@login_required()
def saveResultsFinalizationManagerAPI(request):
    resp = {'status': 'failed', 'errmsg': 'Failed ...'}
    try:
        # ---------------------------------
        # Step 1: Get compressed data
        # ---------------------------------
        body_unicode = request.body.decode('utf-8')
        body_data = json.loads(body_unicode)
        compressed_base64 = body_data.get("compressed_data")

        if not compressed_base64:
            return JsonResponse({'success': False, 'errmsg': 'No compressed data received.'})

        # ---------------------------------
        # Step 2: Decompress data
        # ---------------------------------
        compressed_bytes = base64.b64decode(compressed_base64)
        decompressed_json = zlib.decompress(compressed_bytes).decode('utf-8')
        data = json.loads(decompressed_json)

        # ---------------------------------
        # Extract fields
        # ---------------------------------
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
        is_version = data.get("is_version")
        is_approved = str(data.get("is_approved")).lower() in ['true', '1', 'on', 'yes']
        approved_date = data.get("approved_date")
        approved_user_id = data.get("is_approved_by_user_id")

        is_english = is_version == 'english'
        is_bangla = is_version == 'bangla'

        exam_date_obj = None
        if exam_date:
            exam_date_obj = datetime.strptime(exam_date, "%d-%m-%Y").date()

        # Get approver user instance
        user_instance = None
        if approved_user_id:
            try:
                user_instance = User.objects.get(user_id=approved_user_id)
            except User.DoesNotExist:
                return JsonResponse({'errmsg': 'Approver user not found.'}, status=400)

        from .models import (
            in_result_finalization, in_result_finalizationdtls, organizationlst, branchslist,
            in_class, in_section, in_shifts, in_groups, in_subjects, in_exam_type,
            in_registrations, defaults_exam_modes
        )

        current_year = datetime.now().year

        # Prevent duplicate finalization
        filter_kwargs = Q(finalize_year=current_year)
        if org_id: filter_kwargs &= Q(org_id=org_id)
        if branch_id: filter_kwargs &= Q(branch_id=branch_id)
        if class_id: filter_kwargs &= Q(class_id=class_id)
        if section_id: filter_kwargs &= Q(section_id=section_id)
        if shifts_id: filter_kwargs &= Q(shifts_id=shifts_id)
        if groups_id: filter_kwargs &= Q(groups_id=groups_id)
        if subject_id: filter_kwargs &= Q(subject_id=subject_id)
        if exam_type_id: filter_kwargs &= Q(exam_type_id=exam_type_id)

        if in_result_finalization.objects.filter(filter_kwargs).exists():
            return JsonResponse({'success': False, 'errmsg': 'Finalized Data For This Year Already Exists. Please Choose Another Exam Type.'})

        # Transaction block
        with transaction.atomic():
            org = organizationlst.objects.get(org_id=org_id)
            branch = branchslist.objects.get(branch_id=branch_id)
            class_obj = in_class.objects.get(class_id=class_id)
            section = in_section.objects.get(section_id=section_id)
            shift = in_shifts.objects.get(shift_id=shifts_id)
            group = in_groups.objects.get(groups_id=groups_id) if groups_id else None
            subject = in_subjects.objects.get(subjects_id=subject_id)
            exam_type = in_exam_type.objects.get(exam_type_id=exam_type_id)

            # Create main record
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
                is_approved=is_approved,
                is_approved_by=user_instance,
                approved_date=approved_date,
                is_half_yearly=exam_type.is_half_yearly,
                is_yearly=exam_type.is_yearly,
                is_english=is_english,
                is_bangla=is_bangla,
                ss_creator=request.user
            )

            # Arrays
            reg_ids = data.get('is_reg_id[]', [])
            roll_nos = data.get('is_roll_no[]', [])
            class_names = data.get('is_class_name[]', [])
            section_names = data.get('is_section_name[]', [])
            shift_names = data.get('is_shift_name[]', [])
            groups_names = data.get('is_groups_name[]', [])
            mode_ids = data.get('def_mode_id[]', [])
            mode_names = data.get('is_mode_name[]', [])
            pass_marks = data.get('is_pass_marks[]', [])
            default_marks = data.get('is_default_marks[]', [])
            marks_list = data.get('is_actual_marks[]', [])
            absent_present_list = data.get('is_absent_present[]', [])

            if not isinstance(reg_ids, list):
                reg_ids = [reg_ids]
                roll_nos = [roll_nos]
                class_names = [class_names]
                section_names = [section_names]
                shift_names = [shift_names]
                groups_names = [groups_names]
                mode_ids = [mode_ids]
                mode_names = [mode_names]
                pass_marks = [pass_marks]
                default_marks = [default_marks]
                marks_list = [marks_list]
                absent_present_list = [absent_present_list]

            # Group exam modes
            from collections import defaultdict
            student_modes = defaultdict(list)
            total_students = len(reg_ids)
            modes_per_student = len(mode_ids) // total_students if total_students else 0

            for i, reg_id in enumerate(reg_ids):
                start = i * modes_per_student
                end = start + modes_per_student
                student_modes[reg_id] = list(zip(
                    mode_ids[start:end],
                    mode_names[start:end],
                    pass_marks[start:end],
                    default_marks[start:end],
                    marks_list[start:end],
                    absent_present_list[start:end]
                ))

            # ============================
            # ✅ Optimization Part
            # ============================

            # Bulk fetch all registrations & exam_modes
            reg_instances = {r.reg_id: r for r in in_registrations.objects.filter(reg_id__in=reg_ids)}
            mode_instances = {m.def_mode_id: m for m in defaults_exam_modes.objects.filter(def_mode_id__in=mode_ids)}

            bulk_objects = []

            # Build all detail objects
            for i, reg_id in enumerate(reg_ids):
                reg_instance = reg_instances.get(int(reg_id))
                for mode_id, mode_name, pass_mark, default_mark, marks, is_present in student_modes[reg_id]:
                    mode_instance = mode_instances.get(int(mode_id))
                    bulk_objects.append(in_result_finalizationdtls(
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
                        roll_no=roll_nos[i],
                        class_name=class_names[i],
                        section_name=section_names[i],
                        shift_name=shift_names[i],
                        groups_name=groups_names[i],
                        def_mode_id=mode_instance,
                        is_mode_name=mode_name,
                        is_pass_marks=int(pass_mark or 0),
                        is_default_marks=int(default_mark or 0),
                        is_actual_marks=float(marks or 0),
                        is_absent_present=is_present in ['True', 'true', '1', 'on', 'yes'],
                        is_half_yearly=exam_type.is_half_yearly,
                        is_yearly=exam_type.is_yearly,
                        is_english=is_english,
                        is_bangla=is_bangla,
                        is_approved=is_approved,
                        is_approved_by=user_instance,
                        approved_date=approved_date,
                        ss_creator=request.user
                    ))

            # Bulk insert (faster)
            in_result_finalizationdtls.objects.bulk_create(bulk_objects, batch_size=500)

        return JsonResponse({'success': True, 'msg': 'Result finalization saved successfully.'})

    except Exception as e:
        print("Unhandled Error:", str(e))
        resp['errmsg'] = str(e)
        return HttpResponse(json.dumps(resp), content_type="application/json")
    
    
    # resp = {'status': 'failed', 'errmsg': 'Failed ...'}
    # try:
    #     # ---------------------------------
    #     # Step 1: Get compressed data
    #     # ---------------------------------
    #     body_unicode = request.body.decode('utf-8')
    #     body_data = json.loads(body_unicode)
    #     compressed_base64 = body_data.get("compressed_data")

    #     if not compressed_base64:
    #         return JsonResponse({'success': False, 'errmsg': 'No compressed data received.'})

    #     # ---------------------------------
    #     # Step 2: Decompress data
    #     # ---------------------------------
    #     compressed_bytes = base64.b64decode(compressed_base64)
    #     decompressed_json = zlib.decompress(compressed_bytes).decode('utf-8')
    #     data = json.loads(decompressed_json)

    #     # Now `data` contains same structure as normal request.POST
    #     # ---------------------------------
    #     # Extract fields (same as before)
    #     # ---------------------------------
    #     names_of_exam = data.get("names_of_exam")
    #     org_id = data.get("org")
    #     branch_id = data.get("branchs")
    #     exam_date = data.get("exam_date")
    #     class_id = data.get("is_class")
    #     section_id = data.get("is_section")
    #     shifts_id = data.get("is_shifts")
    #     groups_id = data.get("is_groups")
    #     subject_id = data.get("is_subjects")
    #     exam_type_id = data.get("exam_type")
    #     is_version = data.get("is_version")
    #     is_approved = str(data.get("is_approved")).lower() in ['true', '1', 'on', 'yes']
    #     approved_date = data.get("approved_date")
    #     approved_user_id = data.get("is_approved_by_user_id")

    #     is_english = is_version == 'english'
    #     is_bangla = is_version == 'bangla'

    #     exam_date_obj = None
    #     if exam_date:
    #         exam_date_obj = datetime.strptime(exam_date, "%d-%m-%Y").date()

    #     # Get approver user instance
    #     user_instance = None
    #     if approved_user_id:
    #         try:
    #             user_instance = User.objects.get(user_id=approved_user_id)
    #         except User.DoesNotExist:
    #             return JsonResponse({'errmsg': 'Approver user not found.'}, status=400)

    #     from .models import (
    #         in_result_finalization, in_result_finalizationdtls, organizationlst, branchslist,
    #         in_class, in_section, in_shifts, in_groups, in_subjects, in_exam_type,
    #         in_registrations, defaults_exam_modes
    #     )

    #     current_year = datetime.now().year

    #     # Prevent duplicate finalization
    #     from django.db.models import Q
    #     filter_kwargs = Q(finalize_year=current_year)
    #     if org_id: filter_kwargs &= Q(org_id=org_id)
    #     if branch_id: filter_kwargs &= Q(branch_id=branch_id)
    #     if class_id: filter_kwargs &= Q(class_id=class_id)
    #     if section_id: filter_kwargs &= Q(section_id=section_id)
    #     if shifts_id: filter_kwargs &= Q(shifts_id=shifts_id)
    #     if groups_id: filter_kwargs &= Q(groups_id=groups_id)
    #     if subject_id: filter_kwargs &= Q(subject_id=subject_id)
    #     if exam_type_id: filter_kwargs &= Q(exam_type_id=exam_type_id)

    #     if in_result_finalization.objects.filter(filter_kwargs).exists():
    #         return JsonResponse({'success': False, 'errmsg': 'Finalized Data For This Year Already Exists. Please Choose Another Exam Type.'})

    #     # Transaction block
    #     with transaction.atomic():
    #         org = organizationlst.objects.get(org_id=org_id)
    #         branch = branchslist.objects.get(branch_id=branch_id)
    #         class_obj = in_class.objects.get(class_id=class_id)
    #         section = in_section.objects.get(section_id=section_id)
    #         shift = in_shifts.objects.get(shift_id=shifts_id)
    #         group = in_groups.objects.get(groups_id=groups_id) if groups_id else None
    #         subject = in_subjects.objects.get(subjects_id=subject_id)
    #         exam_type = in_exam_type.objects.get(exam_type_id=exam_type_id)

    #         # Create main record
    #         result_finalization = in_result_finalization.objects.create(
    #             names_of_exam=names_of_exam,
    #             exam_date=exam_date_obj,
    #             org_id=org,
    #             branch_id=branch,
    #             class_id=class_obj,
    #             section_id=section,
    #             shifts_id=shift,
    #             groups_id=group,
    #             subject_id=subject,
    #             exam_type_id=exam_type,
    #             is_approved=is_approved,
    #             is_approved_by=user_instance,
    #             approved_date=approved_date,
    #             is_half_yearly=exam_type.is_half_yearly,
    #             is_yearly=exam_type.is_yearly,
    #             is_english=is_english,
    #             is_bangla=is_bangla,
    #             ss_creator=request.user
    #         )

    #         # Arrays
    #         reg_ids = data.get('is_reg_id[]', [])
    #         roll_nos = data.get('is_roll_no[]', [])
    #         class_names = data.get('is_class_name[]', [])
    #         section_names = data.get('is_section_name[]', [])
    #         shift_names = data.get('is_shift_name[]', [])
    #         groups_names = data.get('is_groups_name[]', [])
    #         mode_ids = data.get('def_mode_id[]', [])
    #         mode_names = data.get('is_mode_name[]', [])
    #         pass_marks = data.get('is_pass_marks[]', [])
    #         default_marks = data.get('is_default_marks[]', [])
    #         marks_list = data.get('is_actual_marks[]', [])
    #         absent_present_list = data.get('is_absent_present[]', [])

    #         if not isinstance(reg_ids, list):
    #             # Ensure arrays are list type
    #             reg_ids = [reg_ids]
    #             roll_nos = [roll_nos]
    #             class_names = [class_names]
    #             section_names = [section_names]
    #             shift_names = [shift_names]
    #             groups_names = [groups_names]
    #             mode_ids = [mode_ids]
    #             mode_names = [mode_names]
    #             pass_marks = [pass_marks]
    #             default_marks = [default_marks]
    #             marks_list = [marks_list]
    #             absent_present_list = [absent_present_list]

    #         # Group exam modes
    #         from collections import defaultdict
    #         student_modes = defaultdict(list)
    #         total_students = len(reg_ids)
    #         modes_per_student = len(mode_ids) // total_students if total_students else 0

    #         for i, reg_id in enumerate(reg_ids):
    #             start = i * modes_per_student
    #             end = start + modes_per_student
    #             student_modes[reg_id] = list(zip(
    #                 mode_ids[start:end],
    #                 mode_names[start:end],
    #                 pass_marks[start:end],
    #                 default_marks[start:end],
    #                 marks_list[start:end],
    #                 absent_present_list[start:end]
    #             ))

    #         # Save details
    #         for i, reg_id in enumerate(reg_ids):
    #             reg_instance = in_registrations.objects.get(reg_id=reg_id)
    #             for mode_id, mode_name, pass_mark, default_mark, marks, is_present in student_modes[reg_id]:
    #                 in_result_finalizationdtls.objects.create(
    #                     res_fin_id=result_finalization,
    #                     org_id=org,
    #                     branch_id=branch,
    #                     class_id=class_obj,
    #                     section_id=section,
    #                     shifts_id=shift,
    #                     groups_id=group,
    #                     subject_id=subject,
    #                     exam_type_id=exam_type,
    #                     reg_id=reg_instance,
    #                     roll_no=roll_nos[i],
    #                     class_name=class_names[i],
    #                     section_name=section_names[i],
    #                     shift_name=shift_names[i],
    #                     groups_name=groups_names[i],
    #                     def_mode_id=defaults_exam_modes.objects.get(def_mode_id=mode_id),
    #                     is_mode_name=mode_name,
    #                     is_pass_marks=int(pass_mark or 0),
    #                     is_default_marks=int(default_mark or 0),
    #                     is_actual_marks=float(marks or 0),
    #                     is_absent_present=is_present in ['True', 'true', '1', 'on', 'yes'],
    #                     is_half_yearly=exam_type.is_half_yearly,
    #                     is_yearly=exam_type.is_yearly,
    #                     is_english=is_english,
    #                     is_bangla=is_bangla,
    #                     is_approved=is_approved,
    #                     is_approved_by=user_instance,
    #                     approved_date=approved_date,
    #                     ss_creator=request.user
    #                 )

    #     return JsonResponse({'success': True, 'msg': 'Result finalization saved successfully.'})

    # except Exception as e:
    #     print("Unhandled Error:", str(e))
    #     resp['errmsg'] = str(e)
    #     return HttpResponse(json.dumps(resp), content_type="application/json")


@login_required()
def updateResultsFinalizationManagerAPI(request):
    resp = {'status': 'failed', 'errmsg': 'Failed ...'}

    try:
        if request.method != "POST":
            return JsonResponse({'success': False, 'errmsg': 'Invalid Request Method'})

        # ---------------------------------
        # Step 1: Parse compressed JSON
        # ---------------------------------
        try:
            body_data = json.loads(request.body.decode('utf-8'))
            compressed_b64 = body_data.get("compressed_data")
            if not compressed_b64:
                return JsonResponse({'success': False, 'errmsg': 'No compressed data received'})

            # Base64 decode
            compressed_bytes = base64.b64decode(compressed_b64)

            # ✅ Decompress raw-deflate (matches pako.deflateRaw)
            decompressed_bytes = zlib.decompress(compressed_bytes, -zlib.MAX_WBITS)
            data = json.loads(decompressed_bytes.decode("utf-8"))

        except Exception as e:
            return JsonResponse({'success': False, 'errmsg': f'Data decompression failed: {str(e)}'})

        # ---------------------------------
        # Step 2: Extract Master data
        # ---------------------------------
        res_fin_id = data.get("res_fin_id")
        names_of_exam = data.get("names_of_exam")
        exam_date = data.get("exam_date")
        is_approved = str(data.get("is_approved")).lower() in ['true', '1', 'on', 'yes']
        approved_date = data.get("approved_date")
        approved_user_id = data.get("is_approved_by_user_id")

        user_instance = None
        if approved_user_id:
            user_instance = get_object_or_404(User, pk=approved_user_id)

        with transaction.atomic():
            # ---------------------------------
            # Step 3: Update Master Table
            # ---------------------------------
            ResultsFinalization = get_object_or_404(in_result_finalization, res_fin_id=res_fin_id)
            ResultsFinalization.names_of_exam = names_of_exam
            ResultsFinalization.exam_date = (
                datetime.strptime(exam_date, "%d-%m-%Y").date() if exam_date else None
            )
            ResultsFinalization.is_approved = is_approved
            ResultsFinalization.is_approved_by = user_instance
            ResultsFinalization.approved_date = approved_date
            ResultsFinalization.ss_modifier = request.user
            ResultsFinalization.save()

            # ---------------------------------
            # Step 4: Details Update
            # ---------------------------------
            res_findtl_ids = data.get('res_findtl_id[]', [])
            mode_ids = data.get('def_mode_id[]', [])
            mode_names = data.get('is_mode_name[]', [])
            pass_marks = data.get('is_pass_marks[]', [])
            default_marks = data.get('is_default_marks[]', [])
            marks_list = data.get('is_actual_marks[]', [])
            absent_present_list = data.get('is_absent_present[]', [])

            total_records = len(res_findtl_ids)

            for i in range(total_records):
                res_findtl_id = res_findtl_ids[i]
                mode_id = mode_ids[i]
                mode_name = mode_names[i]
                pass_mark = pass_marks[i]
                default_mark = default_marks[i]
                marks = marks_list[i]
                is_absent = str(absent_present_list[i]).lower() in ['true', '1', 'on', 'yes']

                resDtl = get_object_or_404(in_result_finalizationdtls, res_findtl_id=res_findtl_id)

                # update fields
                resDtl.def_mode_id = get_object_or_404(defaults_exam_modes, pk=mode_id)
                resDtl.is_mode_name = mode_name
                resDtl.is_pass_marks = int(pass_mark or 0)
                resDtl.is_default_marks = int(default_mark or 0)
                resDtl.is_actual_marks = float(marks or 0)
                resDtl.is_absent_present = is_absent
                resDtl.is_approved = is_approved
                resDtl.is_approved_by = user_instance
                resDtl.approved_date = approved_date
                resDtl.ss_modifier = request.user
                resDtl.save()

        return JsonResponse({'success': True, 'msg': 'Results Finalization updated successfully.'})

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
        # details = in_result_finalizationdtls.objects.filter(res_fin_id=finalization).order_by('reg_id__roll_no')
        details = (
            in_result_finalizationdtls.objects
            .filter(res_fin_id=finalization)
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
                'res_findtl_id': d.res_findtl_id,
                'reg_id': d.reg_id.reg_id if d.reg_id else None,
                'full_name': d.reg_id.full_name if d.reg_id else '',
                'roll_no': d.roll_no,
                'class_name': d.class_name,
                'section_name': d.section_name,
                'shift_name': d.shift_name,
                'groups_name': d.groups_name,
                'def_mode_id': d.def_mode_id.def_mode_id if d.def_mode_id else None,
                'is_mode_name': d.is_mode_name,
                'is_default_marks': d.is_default_marks,
                'is_pass_marks': d.is_pass_marks,
                'is_actual_marks': d.is_actual_marks,
                'is_absent_present': d.is_absent_present,
            })

        data = {
            'finalization': {
                'res_fin_id': finalization.res_fin_id,
                'names_of_exam': finalization.names_of_exam,
                'is_english': finalization.is_english,
                'is_bangla': finalization.is_bangla,
                'exam_date': finalization.exam_date.strftime('%d-%m-%Y') if finalization.exam_date else None,
                'org_id': finalization.org_id.org_id if finalization.org_id else None,
                'branch_id': finalization.branch_id.branch_id if finalization.branch_id else None,
                'class_id': finalization.class_id.class_id if finalization.class_id else None,
                'section_id': finalization.section_id.section_id if finalization.section_id else None,
                'shifts_id': finalization.shifts_id.shift_id if finalization.shifts_id else None,
                'groups_id': finalization.groups_id.groups_id if finalization.groups_id else None,
                'subjects_id': finalization.subject_id.subjects_id if finalization.subject_id else None,
                'exam_type_id': finalization.exam_type_id.exam_type_id if finalization.exam_type_id else None,
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




# def getResultsFinalizationListManagerAPI(request):
# resp = {'status': 'failed', 'errmsg': 'Failed ...'}
    # data = request.POST

    # try:
    #     names_of_exam = data.get("names_of_exam")
    #     org_id = data.get("org")
    #     branch_id = data.get("branchs")
    #     exam_date = data.get("exam_date")
    #     class_id = data.get("is_class")
    #     section_id = data.get("is_section")
    #     shifts_id = data.get("is_shifts")
    #     groups_id = data.get("is_groups")
    #     subject_id = data.get("is_subjects")
    #     exam_type_id = data.get("exam_type")
        
    #     def str_to_bool(val):
    #         if val is None:
    #             return False
    #         return str(val).lower() in ['true', '1', 'on', 'yes']

    #     is_cq_check = str_to_bool(data.get("is_cq_check"))
    #     is_cq = int(data.get("is_cq") or 0)
    #     is_cq_pass_marks = int(data.get("is_cq_pass_mark") or 0)
    #     is_mcq_check = str_to_bool(data.get("is_mcq_check"))
    #     is_mcq = int(data.get("is_mcq") or 0)
    #     is_mcq_pass_marks = int(data.get("is_mcq_pass_mark") or 0)
    #     is_written_check = str_to_bool(data.get("is_written_check"))
    #     is_written = int(data.get("is_written") or 0)
    #     is_written_pass_marks = int(data.get("is_written_pass_mark") or 0)
    #     is_practical_check = str_to_bool(data.get("is_practical_check"))
    #     is_practical = int(data.get("is_practical") or 0)
    #     is_practical_pass_marks = int(data.get("is_practical_pass_mark") or 0)
    #     is_oral_check = str_to_bool(data.get("is_oral_check"))
    #     is_oral = int(data.get("is_oral") or 0)
    #     is_oral_pass_marks = int(data.get("is_oral_pass_mark") or 0)
    #     is_version = data.get("is_version")
    #     is_approved = data['is_approved']
    #     approved_date = data.get("approved_date")
    #     approved_user_id = data.get("is_approved_by_user_id")
        
        
    #     current_year = datetime.now().year

    #     filter_kwargs = Q()
    #     filter_kwargs &= Q(finalize_year=current_year)  # filter by current year

    #     if org_id:
    #         filter_kwargs &= Q(org_id=org_id)
    #     if branch_id:
    #         filter_kwargs &= Q(branch_id=branch_id)
    #     if class_id:
    #         filter_kwargs &= Q(class_id=class_id)
    #     if section_id:
    #         filter_kwargs &= Q(section_id=section_id)
    #     if shifts_id:
    #         filter_kwargs &= Q(shifts_id=shifts_id)
    #     if groups_id:
    #         filter_kwargs &= Q(groups_id=groups_id)
    #     if subject_id:
    #         filter_kwargs &= Q(subject_id=subject_id)
    #     if exam_type_id:
    #         filter_kwargs &= Q(exam_type_id=exam_type_id)
    #     if is_version == 'english':
    #         is_english = True
    #         is_bangla = False
    #     if is_version == 'bangla':
    #         is_english = False
    #         is_bangla = True

    #     finalized_data = in_result_finalization.objects.filter(filter_kwargs)
        
    #     if finalized_data.exists():
    #         # If data exists for the current year, return an error
    #         return JsonResponse({'success': False, 'errmsg': 'Finalized Data For This Year Already Exists. Please Choose Another Exam Type.'})


    #     # Handle exam_date parsing
    #     exam_date_obj = None
    #     if exam_date:
    #         try:
    #             exam_date_obj = datetime.strptime(exam_date, "%d-%m-%Y").date()
    #         except ValueError:
    #             resp['errmsg'] = f"Invalid exam date format: {exam_date}. Expected DD-MM-YYYY."
    #             return JsonResponse(resp)

    #     # Get approver user instance
    #     user_instance = None
    #     if approved_user_id:
    #         try:
    #             user_instance = User.objects.get(user_id=approved_user_id)
    #         except User.DoesNotExist:
    #             return JsonResponse({'errmsg': 'Approver user not found.'}, status=400)

    #     with transaction.atomic():
    #         org = organizationlst.objects.get(org_id=org_id)
    #         branch = branchslist.objects.get(branch_id=branch_id)
    #         class_obj = in_class.objects.get(class_id=class_id)
    #         section = in_section.objects.get(section_id=section_id)
    #         shift = in_shifts.objects.get(shift_id=shifts_id)
    #         subject = in_subjects.objects.get(subjects_id=subject_id)
    #         exam_type = in_exam_type.objects.get(exam_type_id=exam_type_id)
    #         group = in_groups.objects.get(groups_id=groups_id) if groups_id else None

    #         result_finalization = in_result_finalization.objects.create(
    #             names_of_exam=names_of_exam,
    #             exam_date=exam_date_obj,
    #             org_id=org,
    #             branch_id=branch,
    #             class_id=class_obj,
    #             section_id=section,
    #             shifts_id=shift,
    #             groups_id=group,
    #             subject_id=subject,
    #             exam_type_id=exam_type,
    #             is_cq_check=is_cq_check,
    #             is_cq=is_cq,
    #             is_cq_pass_marks=is_cq_pass_marks,
    #             is_mcq_check=is_mcq_check,
    #             is_mcq=is_mcq,
    #             is_mcq_pass_marks=is_mcq_pass_marks,
    #             is_written_check=is_written_check,
    #             is_written=is_written,
    #             is_written_pass_marks=is_written_pass_marks,
    #             is_practical_check=is_practical_check,
    #             is_practical=is_practical,
    #             is_practical_pass_marks=is_practical_pass_marks,
    #             is_oral_check=is_oral_check,
    #             is_oral=is_oral,
    #             is_oral_pass_marks=is_oral_pass_marks,
    #             is_approved=is_approved,
    #             is_approved_by=user_instance,
    #             approved_date=approved_date,
    #             is_half_yearly=exam_type.is_half_yearly,
    #             is_yearly=exam_type.is_yearly,
    #             is_english=is_english,
    #             is_bangla=is_bangla,
    #             ss_creator=request.user
    #         )

    #         zip_datas = zip(
    #             data.getlist('is_reg_id[]'),
    #             data.getlist('is_roll_no[]'),
    #             data.getlist('is_class_name[]'),
    #             data.getlist('is_section_name[]'),
    #             data.getlist('is_shift_name[]'),
    #             data.getlist('is_groups_name[]'),
    #             data.getlist('is_cq_marks[]'),
    #             data.getlist('is_cq_apval[]'),
    #             data.getlist('is_mcq_marks[]'),
    #             data.getlist('is_mcq_apval[]'),
    #             data.getlist('is_written_marks[]'),
    #             data.getlist('is_written_apval[]'),
    #             data.getlist('is_practical_marks[]'),
    #             data.getlist('is_practical_apval[]'),
    #             data.getlist('is_oral_marks[]'),
    #             data.getlist('is_oral_apval[]'),
    #             data.getlist('is_grand_total_marks[]'),
    #         )

    #         for fields in zip_datas:
    #             (
    #                 reg_id, roll_no, class_name, section_name, shift_name, groups_name,
    #                 cq_marks, cq_apval, mcq_marks, mcq_apval, written_marks, written_apval,
    #                 practical_marks, practical_apval, oral_marks, oral_apval, grand_total
    #             ) = fields

    #             reg_instance = in_registrations.objects.get(reg_id=reg_id)

    #             resultFinalizationDtl = in_result_finalizationdtls.objects.create(
    #                 res_fin_id=result_finalization,
    #                 org_id=org,
    #                 branch_id=branch,
    #                 class_id=class_obj,
    #                 section_id=section,
    #                 shifts_id=shift,
    #                 groups_id=group,
    #                 subject_id=subject,
    #                 exam_type_id=exam_type,
    #                 reg_id=reg_instance,
    #                 roll_no=roll_no,
    #                 class_name=class_name,
    #                 section_name=section_name,
    #                 shift_name=shift_name,
    #                 groups_name=groups_name,
    #                 is_cq_marks=int(cq_marks or 0),
    #                 is_cq_apval=cq_apval == '1',
    #                 is_cq_pass_marks=is_cq_pass_marks,
    #                 is_mcq_marks=int(mcq_marks or 0),
    #                 is_mcq_apval=mcq_apval == '1',
    #                 is_mcq_pass_marks=is_mcq_pass_marks,
    #                 is_written_marks=int(written_marks or 0),
    #                 is_written_apval=written_apval == '1',
    #                 is_written_pass_marks=is_written_pass_marks,
    #                 is_practical_marks=int(practical_marks or 0),
    #                 is_practical_apval=practical_apval == '1',
    #                 is_practical_pass_marks=is_practical_pass_marks,
    #                 is_oral_marks=int(oral_marks or 0),
    #                 is_oral_apval=oral_apval == '1',
    #                 is_oral_pass_marks=is_oral_pass_marks,
    #                 grand_total_marks=int(grand_total or 0),
    #                 is_half_yearly=exam_type.is_half_yearly,
    #                 is_yearly=exam_type.is_yearly,
    #                 is_english=is_english,
    #                 is_bangla=is_bangla,
    #                 is_approved=is_approved,
    #                 is_approved_by=user_instance,
    #                 approved_date=approved_date,
    #                 ss_creator=request.user
    #             )

    #     return JsonResponse({'success': True, 'msg': 'Result finalization saved successfully.'})

    # except organizationlst.DoesNotExist:
    #     resp['errmsg'] = 'Invalid organization ID.'
    # except branchslist.DoesNotExist:
    #     resp['errmsg'] = 'Invalid branch ID.'
    # except in_class.DoesNotExist:
    #     resp['errmsg'] = 'Invalid class ID.'
    # except in_section.DoesNotExist:
    #     resp['errmsg'] = 'Invalid section ID.'
    # except in_shifts.DoesNotExist:
    #     resp['errmsg'] = 'Invalid shift ID.'
    # except in_subjects.DoesNotExist:
    #     resp['errmsg'] = 'Invalid subject ID.'
    # except in_exam_type.DoesNotExist:
    #     resp['errmsg'] = 'Invalid exam type ID.'
    # except in_groups.DoesNotExist:
    #     resp['errmsg'] = 'Invalid group ID.'
    # except in_registrations.DoesNotExist:
    #     resp['errmsg'] = 'Invalid registration ID.'
    # except Exception as e:
    #     print("Unhandled Error:", str(e))
    #     resp['errmsg'] = str(e)

    # return HttpResponse(json.dumps(resp), content_type="application/json")