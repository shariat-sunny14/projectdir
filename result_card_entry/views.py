import os
import pdfkit
from io import BytesIO
from decimal import Decimal
import re, json, copy, math
from PyPDF2 import PdfReader, PdfWriter
from django.utils import timezone
from collections import defaultdict
from django.db.models.functions import Cast
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Sum, IntegerField, Value, Case, When
from audioop import reverse
from datetime import datetime
from django.utils.timezone import now
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, Http404
from django.contrib import messages
from django.db import transaction, IntegrityError
from defaults_exam_mode.models import defaults_exam_modes, in_letter_grade_mode, in_letter_gradeFiftyMap, in_letter_gradeHundredMap
from merit_app_card_print.models import in_merit_position_approval, in_merit_position_approvaldtls
from organizations.models import branchslist, organizationlst
from class_setup.models import in_class
from groups_setup.models import in_groups
from policy_setup.models import annual_exam_percentance_policy
from section_setup.models import in_section
from shift_setup.models import in_shifts
from registrations.models import in_registrations
from subject_setup.models import in_subjects
from result_finalization.models import in_result_finalizationdtls
from attendant_manager.models import in_student_attendant, in_student_attendantdtls
from user_setup.models import access_list
from . models import in_results_card_entry
from django.template.loader import render_to_string
from weasyprint import HTML, Document
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def resultCardEntryListManagerAPI(request):
    
    return render(request, 'result_card_entry/result_card_entry_list.html')


@login_required()
def resultCardEntryHistoryListManagerAPI(request):
    
    return render(request, 'result_card_history/result_card_history_list.html')


@login_required()
def getRegistrationListDetailsAPI(request):
    org_filter = request.GET.get('filter_org')
    branch_filter = request.GET.get('filter_branch')
    filter_class = request.GET.get('filter_class')
    filter_section = request.GET.get('filter_section')
    filter_shift = request.GET.get('filter_shift')
    filter_groups = request.GET.get('filter_groups')
    search_year = request.GET.get('search_year')

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
    # current_year = search_year

    for reglist in reg_data:
        # Check if related results_card_entry exists for this reg_id and current year
        half_year_exists_result = in_results_card_entry.objects.filter(
            reg_id=reglist.reg_id,
            create_date=search_year,
            is_half_year=True,
            is_annual=False
        ).exists()
        
        annual_exists_result = in_results_card_entry.objects.filter(
            reg_id=reglist.reg_id,
            create_date=search_year,
            is_half_year=False,
            is_annual=True
        ).exists()

        data.append({
            'reg_id': reglist.reg_id,
            'students_no': reglist.students_no,
            'org_name': getattr(reglist.org_id, 'org_name', None),
            'branch_name': getattr(reglist.branch_id, 'branch_name', None),
            'class_name': getattr(reglist.class_id, 'class_name', None),
            'section_name': getattr(reglist.section_id, 'section_name', None),
            'shift_name': getattr(reglist.shift_id, 'shift_name', None),
            'groups_name': getattr(reglist.groups_id, 'groups_name', None),
            'full_name': reglist.full_name,
            'roll_no': reglist.roll_no,
            'half_year_status': half_year_exists_result,  # True if result exists, else False
            'annual_status': annual_exists_result
        })

    return JsonResponse({'data': data})


@login_required()
def getResultCardHistoryDetailsListAPI(request):
    
    user = request.user
    
    org_filter = request.GET.get('filter_org')
    branch_filter = request.GET.get('filter_branch')
    filter_class = request.GET.get('filter_class')
    filter_section = request.GET.get('filter_section')
    filter_shift = request.GET.get('filter_shift')
    filter_groups = request.GET.get('filter_groups')
    filter_year = request.GET.get('filter_year')
    search_input = request.GET.get('searchInput')
    exams_types = request.GET.get('filter_exams_types')
    
    has_access = access_list.objects.filter(
        user_id=user,
        feature_id__feature_page_link='RESULTSCARDRBACCESSBTN',
        is_active=True
    ).exists()

    filter_kwargs = Q()

    # -------------------------
    # APPLY FILTERS
    # -------------------------
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

    if filter_year:
        filter_kwargs &= Q(create_date=filter_year)

    # Exam type filter
    if exams_types:
        if exams_types.lower() == "is_half_yearly":
            filter_kwargs &= Q(is_half_year=True)
        elif exams_types.lower() == "is_annual":
            filter_kwargs &= Q(is_annual=True)

    # Search filter
    if search_input:
        filter_kwargs &= (
            Q(roll_no__icontains=search_input) |
            Q(reg_id__full_name__icontains=search_input) |
            Q(reg_id__students_no__icontains=search_input)
        )

    # -------------------------
    # MAIN QUERY WITH roll_no SORTING
    # -------------------------
    result_cards = (
        in_results_card_entry.objects
        .filter(filter_kwargs)
        .annotate(
            # roll_no numeric হলে 1, না হলে 0
            is_numeric=Case(
                When(roll_no__regex=r'^\d+$', then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            ),
            # roll_no digit হলে integer cast, না হলে বড় সংখ্যা
            roll_as_int=Case(
                When(roll_no__regex=r'^\d+$', then=Cast('roll_no', IntegerField())),
                default=Value(999999999),
                output_field=IntegerField(),
            ),
        )
        .order_by('-is_numeric', 'roll_as_int', 'roll_no')
    )

    # -------------------------
    # BUILD RESPONSE
    # -------------------------
    data = []
    for rc in result_cards:
        data.append({
            'res_card_id': rc.res_card_id,
            'create_year': rc.create_date,
            'org_id': rc.org_id.org_id if rc.org_id else None,
            'branch_id': rc.branch_id.branch_id if rc.branch_id else None,
            'class_id': rc.class_id.class_id if rc.class_id else None,
            'section_id': rc.section_id.section_id if rc.section_id else None,
            'shift_id': rc.shift_id.shift_id if rc.shift_id else None,
            'groups_id': rc.groups_id.groups_id if rc.groups_id else None,
            'is_english': rc.is_english,
            'is_bangla': rc.is_bangla,
            'students_no': getattr(rc.reg_id, 'students_no', ''),
            'full_name': getattr(rc.reg_id, 'full_name', ''),
            'roll_no': rc.roll_no,
            'org_name': getattr(rc.org_id, 'org_name', None),
            'branch_name': getattr(rc.branch_id, 'branch_name', None),
            'class_name': getattr(rc.class_id, 'class_name', None),
            'section_name': getattr(rc.section_id, 'section_name', None),
            'shift_name': getattr(rc.shift_id, 'shift_name', None),
            'groups_name': getattr(rc.groups_id, 'groups_name', None),
            'is_half_year': rc.is_half_year,
            'is_annual': rc.is_annual,
            'is_approved': rc.is_approved,
            'approved_date': rc.approved_date,
            'is_approved_by': rc.is_approved_by.username if rc.is_approved_by else '',
            'has_access': has_access,
        })

    return JsonResponse({'data': data})

# half yearly result entry UI
@login_required()
def getResultsEntryUIManagerAPI(request):
    org_id = request.GET.get('org_id')
    branch_id = request.GET.get('branch_id')
    reg_id = request.GET.get('reg_id')
    is_year = request.GET.get('is_year')

    org_list = get_object_or_404(organizationlst, org_id=org_id)
    branch_list = get_object_or_404(branchslist, branch_id=branch_id)
    registration = get_object_or_404(in_registrations, reg_id=reg_id)

    def title_case(value):
        if value:
            return ' '.join(word.capitalize() for word in value.split())
        return ''

    registration_data = {
        'reg_id': registration.reg_id,
        'class_id': registration.class_id.class_id if registration.class_id else '',
        'section_id': registration.section_id.section_id if registration.section_id else '',
        'shift_id': registration.shift_id.shift_id if registration.shift_id else '',
        'groups_id': registration.groups_id.groups_id if registration.groups_id else '',
        'full_name': title_case(registration.full_name),
        'father_name': title_case(registration.father_name),
        'mother_name': title_case(registration.mother_name),
        'class_name': registration.class_id.class_name if registration.class_id else '',
        'section_name': registration.section_id.section_name if registration.section_id else '',
        'shift_name': registration.shift_id.shift_name if registration.shift_id else '',
        'roll_no': registration.roll_no or '',
        'is_english': registration.is_english,
        'is_bangla': registration.is_bangla,
    }

    context = {
        'org_list': org_list,
        'branch_list': branch_list,
        'registration': registration_data,
        'is_year': is_year,
    }

    return render(request, 'result_card_entry/result_card_half_yearly.html', context)


def safe_int(val):
    if val in (None, "", "null", "None"):
        return None
    try:
        return int(val)
    except ValueError:
        return None

@login_required()
def getStudentAttendance(request):
    if request.method == "GET":
        org_id = safe_int(request.GET.get('org_id'))
        branch_id = safe_int(request.GET.get('branch_id'))
        reg_id = safe_int(request.GET.get('reg_id'))
        class_id = safe_int(request.GET.get('class_id'))
        shift_id = safe_int(request.GET.get('shift_id'))
        groups_id = safe_int(request.GET.get('groups_id'))

        is_half_yearly = request.GET.get('is_half_yearly') == 'true'
        current_year = datetime.now().year

        # Build filter
        base_filter = {'attendant_year': current_year}
        if org_id: base_filter['org_id_id'] = org_id
        if branch_id: base_filter['branch_id_id'] = branch_id
        if class_id: base_filter['class_id_id'] = class_id
        if shift_id: base_filter['shifts_id_id'] = shift_id
        if groups_id: base_filter['groups_id_id'] = groups_id
        if is_half_yearly: base_filter['is_half_yearly'] = True

        try:
            att_master = in_student_attendant.objects.get(**base_filter)
            total_working_days = att_master.working_days or 0

            present_days = in_student_attendantdtls.objects.filter(
                attendant_id=att_master,
                reg_id_id=reg_id
            ).aggregate(total_present=Sum('attendant_qty'))['total_present'] or 0

        except in_student_attendant.DoesNotExist:
            total_working_days = 0
            present_days = 0

        return JsonResponse({
            'success': True,
            'total_working_days': total_working_days,
            'total_present_days': present_days
        })

    return JsonResponse({'success': False, 'message': 'Invalid request method'})
    

@login_required()
def getHalfYearlyResultAPI(request):
    if request.method == 'GET':
        org_id = request.GET.get("org_id")
        branch_id = request.GET.get("branch_id")
        reg_id = request.GET.get("reg_id")
        class_id = request.GET.get("class_id")
        section_id = request.GET.get("section_id")
        year = request.GET.get("is_year")
        version = request.GET.get("is_version")  # english/bangla

        registration = get_object_or_404(in_registrations, reg_id=reg_id)

        # Base subject filter
        base_filter = {
            "class_id": registration.class_id,
            "groups_id": registration.groups_id,
            "org_id": registration.org_id,
            "is_active": True
        }

        if version == "english":
            is_english = True
            base_filter["is_english"] = True
        elif version == "bangla":
            is_bangla = True
            base_filter["is_bangla"] = True

        # subjects_qs = in_subjects.objects.filter(**base_filter).order_by("subjects_no")
        subjects_qs = (
            in_subjects.objects
            .filter(**base_filter)
            .annotate(
                is_numeric=Case(
                    When(subjects_no__regex=r'^\d+$', then=Value(1)),  # pure digits হলে 1
                    default=Value(0),  # নাহলে 0
                    output_field=IntegerField(),
                ),
                subjects_as_int=Case(
                    When(subjects_no__regex=r'^\d+$', then=Cast('subjects_no', IntegerField())),
                    default=Value(999999999),  # non-numeric হলে একেবারে শেষে
                    output_field=IntegerField(),
                )
            )
            .order_by('-is_numeric', 'subjects_as_int', 'subjects_no')  
        )

        subjects_list = []
        for s in subjects_qs:
            subjects_list.append({
                "id": s.subjects_id,
                "name": s.subjects_name,
                "full_marks": s.is_marks,
                "pass_marks": s.is_pass_marks or 0,
                "is_applicable_pass_marks": s.is_applicable_pass_marks,   # <-- ADD THIS
                "modes": {},
                "is_optional": s.is_optional and s.subjects_id == registration.is_optional_sub_id,
                "is_not_countable": s.is_not_countable,
                "letter_grade": "",
                "gp": "-"
            })

        # Results
        result_qs = in_result_finalizationdtls.objects.filter(
            org_id_id=org_id,
            branch_id_id=branch_id,
            reg_id_id=reg_id,
            class_id_id=class_id,
            section_id_id=section_id,
            finalize_year=year,
            is_half_yearly=True,
            is_approved=True
        ).select_related("subject_id")

        results_map = {}
        mode_names_set = set()
        
        exam_type_name = None
        if result_qs.exists():
            exam_type_name = result_qs.first().exam_type_id.exam_type_name
        
        for r in result_qs:
            sid = r.subject_id.subjects_id
            if sid not in results_map:
                results_map[sid] = {}
            results_map[sid][r.is_mode_name] = {
                "def_mode_id": r.def_mode_id.def_mode_id,
                "actual": float(r.is_actual_marks) if r.is_actual_marks is not None else 0.0,
                "pass": float(r.is_pass_marks or 0.0),
                "default": float(r.is_default_marks or 0.0)
            }
            mode_names_set.add(r.is_mode_name)

        # Get mode names in order
        all_modes_qs = defaults_exam_modes.objects.filter(
            is_active=True,
            is_mode_name__in=mode_names_set
        ).order_by("order_by")
        mode_names_ordered = [m.is_mode_name for m in all_modes_qs]
        
        is_english = False
        is_bangla = False

        # Calculate subject-wise grade
        for sub in subjects_list:
            sub["modes"] = results_map.get(sub["id"], {})
            safe_total = sum([float(m["actual"]) for m in sub["modes"].values()]) if sub["modes"] else 0.0
            total = math.floor(safe_total)

            if sub["is_not_countable"]:
                sub["letter_grade"] = "-"
                sub["gp"] = "-"
                continue

            failed_flag = False

            # --- NEW FAIL CHECK LOGIC ---
            if sub["is_applicable_pass_marks"]:
                # Subject-level pass mark check
                if float(total) < float(sub["pass_marks"]):
                    failed_flag = True
            else:
                # Mode-level pass mark check
                failed_flag = any(float(m["actual"]) < float(m["pass"]) for m in sub["modes"].values())

            if failed_flag:
                sub["letter_grade"] = "F"
                sub["gp"] = 0.00
                continue
            
            filter_kwargs = {
                "org_id_id": org_id,
                "class_id_id": registration.class_id,
                "from_marks__lte": total,
                "to_marks__gte": total,
                "is_active": True
            }

            # apply only if needed
            if is_english:
                filter_kwargs["is_english"] = True
            if is_bangla:
                filter_kwargs["is_bangla"] = True

            # --- GRADING LOGIC ---
            if sub["full_marks"] == 100:
                grade_qs = in_letter_gradeHundredMap.objects.filter(
                    **filter_kwargs
                ).first()
            elif sub["full_marks"] == 50:
                grade_qs = in_letter_gradeFiftyMap.objects.filter(
                    **filter_kwargs
                ).first()
            else:
                grade_qs = None

            if grade_qs:
                sub["letter_grade"] = grade_qs.grade_id.is_grade_name
                sub["gp"] = float(grade_qs.grade_point)
            else:
                sub["letter_grade"] = "F"
                sub["gp"] = 0.00

        # --- Extra Calculation Part ---
        total_marks = 0
        count_subjects = 0
        total_gp = 0.0
        fail_flag = False
        optional_bonus = 0.0

        for sub in subjects_list:
            total_sub_marks = sum([float(m["actual"]) for m in sub["modes"].values()]) if sub["modes"] else 0.0

            # সব subject total_marks এ count হবে
            total_marks += total_sub_marks

            # GPA হিসাবের জন্য এখনো আগের logic রাখবো
            if not sub["is_not_countable"] and not sub["is_optional"]:
                count_subjects += 1
                if isinstance(sub["gp"], (int, float)):
                    total_gp += sub["gp"]
                if sub["gp"] == 0.00:
                    fail_flag = True
            elif sub["is_optional"]:
                if isinstance(sub["gp"], (int, float)):
                    bonus = sub["gp"] - 2.00
                    if bonus > 0:
                        optional_bonus += bonus   # শুধু positive অংশ নেবো
                
                # --- NEW LOGIC ---
                # যদি optional subject fail করে এবং is_optional_wise_grade_cal = False হয়
                subj_obj = next((s for s in subjects_qs if s.subjects_id == sub["id"]), None)
                if subj_obj and not subj_obj.is_optional_wise_grade_cal and sub["letter_grade"] == "F":
                    fail_flag = True   # পুরো result fail

        # Average GPA হিসাব
        if count_subjects > 0:
            # এখানে optional_bonus plus হবে না, বরং total_gp এর সাথে যোগ হবে
            adjusted_gp = total_gp + optional_bonus
            average_gpa = adjusted_gp / count_subjects
        else:
            average_gpa = 0.00

        # Fail হলে 0.00
        if fail_flag:
            average_gpa = 0.00

        # সর্বোচ্চ GPA সীমা
        if average_gpa > 5.00:
            average_gpa = 5.00

        # --- FIX: Average Letter Grade (Manual Mapping) ---
        if average_gpa == 0.00:
            average_letter_grade = "F"
        elif average_gpa >= 5.00:
            average_letter_grade = "A+"
        elif average_gpa >= 4.00:
            average_letter_grade = "A"
        elif average_gpa >= 3.50:
            average_letter_grade = "A-"
        elif average_gpa >= 3.00:
            average_letter_grade = "B"
        elif average_gpa >= 2.00:
            average_letter_grade = "C"
        elif average_gpa >= 1.00:
            average_letter_grade = "D"
        else:
            average_letter_grade = "F"
            
        # --- Remarks Mapping ---
        remarks_map = {
            "A+": "Outstanding Achievement!",
            "A": "Impressive Performance!",
            "A-": "Commendable Performance!",
            "B": "Encouraging Performance!",
            "C": "An Average Performance!",
            "D": "Needs Significant Improvement!",
            "F": "Unsatisfactory Performance!"
        }
        remarks_status = remarks_map.get(average_letter_grade, "")

        # Result Status
        result_status = "Failed" if average_gpa == 0.00 and average_letter_grade == "F" else "Passed"

        return JsonResponse({
            "success": True,
            "subjects": subjects_list,
            "mode_names": mode_names_ordered,
            "total_obtained_marks": total_marks,
            "average_gpa": round(average_gpa, 2),
            "average_letter_grade": average_letter_grade,
            "remarks_status": remarks_status,
            "result_status": result_status,
            'exam_type_name': exam_type_name,
        })

    return JsonResponse({"success": False, "message": "Invalid request"})


@login_required()
def saveResultsCardEntryManagerAPI(request):
    resp = {'status': 'failed', 'msg': ''}
    data = request.POST
    org_id = data.get('is_org_id')
    branch_id = data.get('is_branch_id')
    reg_id = data.get('is_reg_id')
    roll_no = data.get('roll_no') 
    class_id = data.get('is_class_id')
    section_id = data.get('is_section_id')
    shift_id = data.get('is_shifts_id')
    groups_id = data.get('is_groups_id')
    total_working_days = data.get('total_working_days')
    total_present_days = data.get('total_present_days')
    is_remarks = data.get('is_remarks')
    date_of_publication_raw = data.get('date_of_publication')
    is_average_gpa = data.get('is_average_gpa')
    average_letter_grade = data.get('average_letter_grade')
    result_status = data.get('result_status')
    total_obtained_marks = data.get('total_obtained_marks')
    is_year = data.get('is_year', 0)
    is_english = data.get('is_english_id', 0)
    is_bangla = data.get('is_bangla_id', 0)


    try:
        with transaction.atomic():
            org_instance = organizationlst.objects.get(org_id=org_id)
            branch_instance = branchslist.objects.get(branch_id=branch_id)
            class_instance = in_class.objects.get(class_id=class_id)
            section_instance = in_section.objects.get(section_id=section_id)
            shift_instance = in_shifts.objects.get(shift_id=shift_id)
            if groups_id:
                groups_instance = in_groups.objects.get(groups_id=groups_id)
            else:
                groups_instance = None

            if reg_id:
                reg_instance = in_registrations.objects.get(reg_id=reg_id)
            else:
                reg_instance = None


            # Filter for existing results card entries
            filter_kwargs = Q(create_date=is_year)
            if org_id: filter_kwargs &= Q(org_id=org_id)
            if branch_id: filter_kwargs &= Q(branch_id=branch_id)
            if class_id: filter_kwargs &= Q(class_id=class_id)
            if section_id: filter_kwargs &= Q(section_id=section_id)
            if shift_id: filter_kwargs &= Q(shift_id=shift_id)
            if groups_id: filter_kwargs &= Q(groups_id=groups_id)
            if reg_id: filter_kwargs &= Q(reg_id=reg_id)

            if in_results_card_entry.objects.filter(filter_kwargs, is_half_year=True, is_annual=False).exists():
                return JsonResponse({'success': False, 'msg': 'This Year Results Card Already Created. Please Try Another One.'})

            date_of_publication = None
            if date_of_publication_raw:
                try:
                    # Convert from 'DD-MM-YYYY' to 'YYYY-MM-DD'
                    date_of_publication = datetime.strptime(date_of_publication_raw, '%d-%m-%Y').date()
                except ValueError:
                    resp['msg'] = f"Invalid date format for date_of_publication: {date_of_publication_raw}"
                    return JsonResponse(resp)

            res_card_entry = in_results_card_entry.objects.create(
                date_of_publication=date_of_publication,
                create_date=is_year,
                org_id=org_instance,
                branch_id=branch_instance,
                reg_id=reg_instance,
                roll_no=roll_no,
                class_id=class_instance,
                section_id=section_instance,
                shift_id=shift_instance,
                groups_id=groups_instance,
                is_half_year=True,
                is_annual=False,
                is_average_gpa=is_average_gpa,
                average_letter_grade=average_letter_grade,
                result_status=result_status,
                total_obtained_marks=float(total_obtained_marks),
                total_working_days=total_working_days,
                total_present_days=total_present_days,
                is_remarks=is_remarks,
                is_english=is_english,
                is_bangla=is_bangla,
                is_approved=True,
                is_approved_by=request.user,
                approved_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                ss_creator=request.user,
                ss_modifier=request.user
            )

            res_card_id = res_card_entry.res_card_id

            resp['status'] = 'success'
            resp['res_card_id'] = res_card_id
    except Exception as e:
        resp['msg'] = str(e)

    return JsonResponse(resp)

@login_required()
def resultsCardEntryReportManagerAPI(request):
    res_card_id = request.GET.get('id')
    org_id = request.GET.get("org_id")
    class_id = request.GET.get("class_id")

    org_id = int(org_id) if org_id and org_id != "null" else None
    class_id = int(class_id) if class_id and class_id != "null" else None

    is_english = request.GET.get("is_english") == 'true'
    is_bangla = request.GET.get("is_bangla") == 'true'

    card_entry = get_object_or_404(in_results_card_entry, res_card_id=res_card_id)
    registration = card_entry.reg_id

    # ================================
    # Fifty Marks Map
    # ================================
    fifty_grades = in_letter_gradeFiftyMap.objects.filter(is_active=True)

    if is_english:
        fifty_grades = fifty_grades.filter(is_english=True)

    if is_bangla:
        fifty_grades = fifty_grades.filter(is_bangla=True)

    if org_id:
        fifty_grades = fifty_grades.filter(org_id=org_id)

    if class_id:
        fifty_grades = fifty_grades.filter(class_id=class_id)

    # ================================
    # Hundred Marks Map
    # ================================
    hundred_grades = in_letter_gradeHundredMap.objects.filter(is_active=True)

    if is_english:
        hundred_grades = hundred_grades.filter(is_english=True)

    if is_bangla:
        hundred_grades = hundred_grades.filter(is_bangla=True)

    if org_id:
        hundred_grades = hundred_grades.filter(org_id=org_id)

    if class_id:
        hundred_grades = hundred_grades.filter(class_id=class_id)

    # =================================
    # Collect grade_ids
    # =================================
    fifty_grade_ids = list(fifty_grades.values_list("grade_id", flat=True))
    hundred_grade_ids = list(hundred_grades.values_list("grade_id", flat=True))

    grade_ids = set(fifty_grade_ids + hundred_grade_ids)

    grades = in_letter_grade_mode.objects.filter(
        grade_id__in=grade_ids
    ).order_by("grade_id")

    # ===============================
    # Prepare Table Data
    # ===============================
    table_data = []
    for grade in grades:

        fifty_map = fifty_grades.filter(grade_id=grade).first()
        hundred_map = hundred_grades.filter(grade_id=grade).first()

        table_data.append({
            "grade_name": grade.is_grade_name,
            "fifty_interval": (
                f"{fifty_map.from_marks}-{fifty_map.to_marks}" if fifty_map else ""
            ),
            "hundred_interval": (
                f"{hundred_map.from_marks}-{hundred_map.to_marks}" if hundred_map else ""
            ),
            "grade_point": (
                fifty_map.grade_point if fifty_map else
                (hundred_map.grade_point if hundred_map else "")
            )
        })

    # ===============================
    # Transaction Data
    # ===============================
    def title_case(value):
        return ' '.join(word.capitalize() for word in value.split()) if value else ''

    transaction = {
        'create_date': card_entry.create_date or '',
        'reg_id': registration.reg_id if registration else '',
        'org_name': card_entry.org_id.org_name if card_entry.org_id else '',
        'full_name': title_case(registration.full_name) if registration else '',
        'roll_no': registration.roll_no if registration else '',
        'father_name': title_case(registration.father_name) if registration else '',
        'mother_name': title_case(registration.mother_name) if registration else '',
        'class_name': card_entry.class_id.class_name if card_entry.class_id else '',
        'section_name': card_entry.section_id.section_name if card_entry.section_id else '',
        'shift_name': card_entry.shift_id.shift_name if card_entry.shift_id else '',
        'total_working_days': card_entry.total_working_days or '',
        'total_present_days': card_entry.total_present_days or '',
        'is_remarks': card_entry.is_remarks or '',
        'date_of_publication': card_entry.date_of_publication or '',
        'is_average_gpa': card_entry.is_average_gpa or '',
        'average_letter_grade': card_entry.average_letter_grade or '',
        'total_obtained_marks': card_entry.total_obtained_marks or '',
        'result_status': card_entry.result_status or '',
    }

    context = {
        "transaction": transaction,
        "registration": registration,
        "table_data": table_data,
    }

    return render(request, 'result_card_entry/result_card_half_yearly_viewer.html', context)


@login_required()
def printResultsCardEntryReportManagerAPI(request):
    id = request.GET.get('id')

    card_entry = get_object_or_404(in_results_card_entry, res_card_id=id)

    def title_case(value):
        if value:
            return ' '.join(word.capitalize() for word in value.split())
        return ''

    transaction = {
        'res_card_id': card_entry.res_card_id,
        'create_date': card_entry.create_date or '',
        'reg_id': card_entry.reg_id.reg_id if card_entry.reg_id else '',
        'org_name': card_entry.org_id.org_name if card_entry.org_id else '',
        'full_name': title_case(card_entry.reg_id.full_name) if card_entry.reg_id else '',
        'roll_no': card_entry.reg_id.roll_no if card_entry.reg_id else '',
        'father_name': title_case(card_entry.reg_id.father_name) if card_entry.reg_id else '',
        'mother_name': title_case(card_entry.reg_id.mother_name) if card_entry.reg_id else '',
        'class_name': card_entry.class_id.class_name if card_entry.class_id else '',
        'section_name': card_entry.section_id.section_name if card_entry.section_id else '',
        'shift_name': card_entry.shift_id.shift_name if card_entry.shift_id else '',
        'merit_position': card_entry.merit_position or '',
        'total_working_days': card_entry.total_working_days or '',
        'total_present_days': card_entry.total_present_days or '',
        'is_remarks': card_entry.is_remarks or '',
        'date_of_publication': card_entry.date_of_publication or '',
        'is_average_gpa': card_entry.is_average_gpa or '',
        'average_letter_grade': card_entry.average_letter_grade or '',
        'result_status': card_entry.result_status or '',
        'total_obtained_marks': card_entry.total_obtained_marks or '',
    }

    context = {
        "transaction": transaction,
    }

    return render(request, 'result_card_entry/print_result_card_half_yearly_report.html', context)


def print_transcript(request):
    id = request.GET.get('id')
    card_entry = get_object_or_404(in_results_card_entry, res_card_id=id)

    # ----------------------------
    # Helper functions
    # ----------------------------
    def parse_int_param(value):
        return int(value) if value and value not in ['null', 'None'] else None

    def title_case(value):
        if value:
            return ' '.join(word.capitalize() for word in value.split())
        return ''

    # ----------------------------
    # Get filtering params
    # ----------------------------
    is_class = parse_int_param(request.GET.get('is_class', ''))
    is_section = parse_int_param(request.GET.get('is_section', ''))
    is_shift = parse_int_param(request.GET.get('is_shift', ''))
    is_groups = parse_int_param(request.GET.get('is_groups', ''))

    # ----------------------------
    # Ranking calculation
    # ----------------------------
    filter_q = Q(org_id=card_entry.org_id, branch_id=card_entry.branch_id)
    if is_class:
        filter_q &= Q(class_id=is_class)
    if is_section:
        filter_q &= Q(section_id=is_section)
    if is_shift:
        filter_q &= Q(shift_id=is_shift)
    if is_groups:
        filter_q &= Q(groups_id=is_groups)

    class_entries = in_results_card_entry.objects.filter(filter_q).select_related('reg_id')

    def sort_key(entry):
        gpa = float(entry.is_average_gpa or 0.0)
        total = int(entry.total_obtained_marks or 0)
        roll = int(entry.reg_id.roll_no) if entry.reg_id and entry.reg_id.roll_no and entry.reg_id.roll_no.isdigit() else 99999
        return (-gpa, -total, roll)

    sorted_entries = sorted(class_entries, key=sort_key)

    ranking_map = {}
    previous_key = None
    current_position = 1
    merit_counter = 1

    for entry in sorted_entries:
        key = sort_key(entry)
        if previous_key is not None and key == previous_key:
            pass
        else:
            merit_counter = current_position
        ranking_map[entry.res_card_id] = merit_counter
        previous_key = key
        current_position += 1

    calculated_merit_position = ranking_map.get(card_entry.res_card_id, '')

    # ----------------------------
    # Subjects & Results Logic
    # ----------------------------
    registration = get_object_or_404(in_registrations, reg_id=card_entry.reg_id.reg_id)

    version = request.GET.get('is_version', '')  # 'english' or 'bangla'
    base_filter = {
        "class_id": registration.class_id,
        "groups_id": registration.groups_id,
        "org_id": registration.org_id,
        "is_active": True
    }

    if version == "english":
        base_filter["is_english"] = True
    elif version == "bangla":
        base_filter["is_bangla"] = True

    # subjects_qs = in_subjects.objects.filter(**base_filter).order_by("subjects_no")
    subjects_qs = (
        in_subjects.objects
        .filter(**base_filter)
        .annotate(
            is_numeric=Case(
                When(subjects_no__regex=r'^\d+$', then=Value(1)),  # pure digits হলে 1
                default=Value(0),  # নাহলে 0
                output_field=IntegerField(),
            ),
            subjects_as_int=Case(
                When(subjects_no__regex=r'^\d+$', then=Cast('subjects_no', IntegerField())),
                default=Value(999999999),  # non-numeric হলে একেবারে শেষে
                output_field=IntegerField(),
            )
        )
        .order_by('-is_numeric', 'subjects_as_int', 'subjects_no')  
    )

    subjects_list = []
    for s in subjects_qs:
        subjects_list.append({
            "id": s.subjects_id,
            "name": s.subjects_name,
            "full_marks": s.is_marks,
            "pass_marks": s.is_pass_marks or 0,
            "is_applicable_pass_marks": s.is_applicable_pass_marks,   # <-- ADD THIS
            "modes": {},
            "is_optional": s.is_optional and s.subjects_id == registration.is_optional_sub_id,
            "is_not_countable": s.is_not_countable,
            "letter_grade": "",
            "gp": "-"
        })

    # Results
    result_qs = in_result_finalizationdtls.objects.filter(
        org_id_id=card_entry.org_id.org_id,
        branch_id_id=card_entry.branch_id.branch_id,
        reg_id_id=card_entry.reg_id.reg_id,
        class_id_id=card_entry.class_id.class_id,
        section_id_id=card_entry.section_id.section_id,
        finalize_year=card_entry.create_date,
        is_english=card_entry.is_english,
        is_bangla=card_entry.is_bangla,
        is_half_yearly=True,
        is_approved=True
    ).select_related("subject_id")

    results_map = {}
    mode_names_set = set()
    for r in result_qs:
        sid = r.subject_id.subjects_id
        if sid not in results_map:
            results_map[sid] = {}
        results_map[sid][r.is_mode_name] = {
            "def_mode_id": r.def_mode_id.def_mode_id,
            "actual": float(r.is_actual_marks) if r.is_actual_marks is not None else 0.0,
            "pass": float(r.is_pass_marks or 0),
            "default": float(r.is_default_marks or 0)
        }
        mode_names_set.add(r.is_mode_name)

    # Mode names ordered
    all_modes_qs = defaults_exam_modes.objects.filter(
        is_active=True,
        is_mode_name__in=mode_names_set
    ).order_by("order_by")
    mode_names_ordered = [m.is_mode_name for m in all_modes_qs]

    # Calculate subject-wise grade
    for sub in subjects_list:
        sub["modes"] = results_map.get(sub["id"], {})
        safe_total = sum([float(m["actual"]) for m in sub["modes"].values()]) if sub["modes"] else 0.0
        total = math.floor(safe_total)

        if sub["is_not_countable"]:
            sub["letter_grade"] = "-"
            sub["gp"] = "-"
            continue

        failed_flag = False

        # --- NEW FAIL CHECK LOGIC ---
        if sub["is_applicable_pass_marks"]:
            # Subject-level pass mark check
            if float(total) < float(sub["pass_marks"]):
                failed_flag = True
        else:
            # Mode-level pass mark check
            failed_flag = any(float(m["actual"]) < float(m["pass"]) for m in sub["modes"].values())

        if failed_flag:
            sub["letter_grade"] = "F"
            sub["gp"] = 0.00
            continue

        # --- GRADING LOGIC ---
        if sub["full_marks"] == 100:
            grade_qs = in_letter_gradeHundredMap.objects.filter(
                org_id_id=card_entry.org_id.org_id,
                class_id_id=registration.class_id,
                from_marks__lte=total,
                to_marks__gte=total,
                is_active=True
            ).first()
        elif sub["full_marks"] == 50:
            grade_qs = in_letter_gradeFiftyMap.objects.filter(
                org_id_id=card_entry.org_id.org_id,
                class_id_id=registration.class_id,
                from_marks__lte=total,
                to_marks__gte=total,
                is_active=True
            ).first()
        else:
            grade_qs = None

        if grade_qs:
            sub["letter_grade"] = grade_qs.grade_id.is_grade_name
            sub["gp"] = float(grade_qs.grade_point)
        else:
            sub["letter_grade"] = "F"
            sub["gp"] = 0.00

    # ----------------------------
    # Prepare transaction context
    # ----------------------------
    transaction = {
        'create_date': card_entry.create_date or '',
        'reg_id': card_entry.reg_id.reg_id if card_entry.reg_id else '',
        'org_name': card_entry.org_id.org_name if card_entry.org_id else '',
        'full_name': title_case(card_entry.reg_id.full_name) if card_entry.reg_id else '',
        'roll_no': card_entry.reg_id.roll_no if card_entry.reg_id else '',
        'father_name': title_case(card_entry.reg_id.father_name) if card_entry.reg_id else '',
        'mother_name': title_case(card_entry.reg_id.mother_name) if card_entry.reg_id else '',
        'class_name': card_entry.class_id.class_name if card_entry.class_id else '',
        'section_name': card_entry.section_id.section_name if card_entry.section_id else '',
        'shift_name': card_entry.shift_id.shift_name if card_entry.shift_id else '',
        'merit_position': calculated_merit_position,
        'total_working_days': card_entry.total_working_days or '',
        'total_present_days': card_entry.total_present_days or '',
        'is_remarks': card_entry.is_remarks or '',
        'date_of_publication': card_entry.date_of_publication or '',
        'is_average_gpa': card_entry.is_average_gpa or '',
        'average_letter_grade': card_entry.average_letter_grade or '',
        'result_status': card_entry.result_status or '',
        'total_obtained_marks': card_entry.total_obtained_marks or '',
        'subjects': subjects_list,
        'mode_names': mode_names_ordered,
    }

    context = {
        "transaction": transaction,
        "printed_on": datetime.now().strftime("%d/%m/%Y, %H:%M:%S"),
    }

    html_string = render_to_string("result_card_entry/print_result_card_half_yearly_report.html", context)
    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    pdf_file = html.write_pdf()

    response = HttpResponse(pdf_file, content_type="application/pdf")
    response['Content-Disposition'] = 'inline; filename="Students_Transcript_Report.pdf"'
    return response


    # id = request.GET.get('id')
    # card_entry = get_object_or_404(in_results_card_entry, res_card_id=id)

    # def parse_int_param(value):
    #     return int(value) if value and value not in ['null', 'None'] else None

    # is_class = parse_int_param(request.GET.get('is_class', ''))
    # is_section = parse_int_param(request.GET.get('is_section', ''))
    # is_shift = parse_int_param(request.GET.get('is_shift', ''))
    # is_groups = parse_int_param(request.GET.get('is_groups', ''))

    # filter_q = Q(org_id=card_entry.org_id, branch_id=card_entry.branch_id)
    # if is_class:
    #     filter_q &= Q(class_id=is_class)
    # if is_section:
    #     filter_q &= Q(section_id=is_section)
    # if is_shift:
    #     filter_q &= Q(shift_id=is_shift)
    # if is_groups:
    #     filter_q &= Q(groups_id=is_groups)

    # class_entries = in_results_card_entry.objects.filter(filter_q).select_related('reg_id')

    # def sort_key(entry):
    #     gpa = float(entry.is_average_gpa or 0.0)
    #     total = int(entry.total_obtained_marks or 0)
    #     roll = int(entry.reg_id.roll_no) if entry.reg_id and entry.reg_id.roll_no and entry.reg_id.roll_no.isdigit() else 99999
    #     return (-gpa, -total, roll)

    # sorted_entries = sorted(class_entries, key=sort_key)

    # ranking_map = {}
    # previous_key = None
    # current_position = 1
    # merit_counter = 1

    # for entry in sorted_entries:
    #     key = sort_key(entry)
    #     if previous_key is not None and key == previous_key:
    #         pass
    #     else:
    #         merit_counter = current_position
    #     ranking_map[entry.res_card_id] = merit_counter
    #     previous_key = key
    #     current_position += 1

    # calculated_merit_position = ranking_map.get(card_entry.res_card_id, '')
    
    # def title_case(value):
    #     if value:
    #         return ' '.join(word.capitalize() for word in value.split())
    #     return ''

    # transaction = {
    #     'create_date': card_entry.create_date or '',
    #     'reg_id': card_entry.reg_id.reg_id if card_entry.reg_id else '',
    #     'org_name': card_entry.org_id.org_name if card_entry.org_id else '',
    #     'full_name': title_case(card_entry.reg_id.full_name) if card_entry.reg_id else '',
    #     'roll_no': card_entry.reg_id.roll_no if card_entry.reg_id else '',
    #     'father_name': title_case(card_entry.reg_id.father_name) if card_entry.reg_id else '',
    #     'mother_name': title_case(card_entry.reg_id.mother_name) if card_entry.reg_id else '',
    #     'class_name': card_entry.class_id.class_name if card_entry.class_id else '',
    #     'section_name': card_entry.section_id.section_name if card_entry.section_id else '',
    #     'shift_name': card_entry.shift_id.shift_name if card_entry.shift_id else '',
    #     'merit_position': calculated_merit_position,
    #     'total_working_days': card_entry.total_working_days or '',
    #     'total_present_days': card_entry.total_present_days or '',
    #     'is_remarks': card_entry.is_remarks or '',
    #     'date_of_publication': card_entry.date_of_publication or '',
    #     'is_average_gpa': card_entry.is_average_gpa or '',
    #     'average_letter_grade': card_entry.average_letter_grade or '',
    #     'result_status': card_entry.result_status or '',
    #     'total_obtained_marks': card_entry.total_obtained_marks or '',
    # }

    # context = {
    #     "transaction": transaction,
    #     "printed_on": datetime.now().strftime("%d/%m/%Y, %H:%M:%S"),
    # }

    # html_string = render_to_string("result_card_entry/print_result_card_half_yearly_report.html", context)

    # html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    # pdf_file = html.write_pdf()

    # response = HttpResponse(pdf_file, content_type="application/pdf")
    # response['Content-Disposition'] = 'inline; filename="Students_Transcript_Report.pdf"'
    # return response



# ১. is_class, is_section, is_shift, is_groups থেকে যেসব মান আসবে তা দিয়ে in_results_card_entry.objects.filter() হবে:
# অর্থাৎ, ইউজার যদি ক্লাস, সেকশন, শিফট, গ্রুপ সিলেক্ট করে তাহলে ঐ মানগুলোর উপর ভিত্তি করে filter() হবে।
# কিন্তু যদি কোন ফিল্ড null, 'null', 'None', অথবা খালি ('') হয়, তাহলে সেই ফিল্ড বাদ দিয়ে সব ক্লাস/সেকশন/শিফট/গ্রুপ এর রেজাল্ট দেখা যাবে।
# অর্থাৎ, ঐ ফিল্ডটি ফিল্টার করার দরকার নেই।

# ২. is_grand_total_marks এর বদলে merit sort হবে is_average_gpa অনুযায়ী:
# আগে যেভাবে is_grand_total_marks দিয়ে সবার র‍্যাংকিং করা হতো, এখন সেটা হবে is_average_gpa দিয়ে।
# অর্থাৎ, যার GPA বেশি, তার পজিশন আগে হবে।

# ৩. যদি কারো is_average_gpa সমান হয়, তাহলে is_grand_total_marks দেখা হবে:
# GPA সমান হলেও যার টোটাল মার্কস বেশি, তার merit position হবে আগে।

# ৪. যদি is_average_gpa এবং is_grand_total_marks দুইটাই সমান হয়, তাহলে:
# তখন reg_id.roll_no দেখা হবে।
# যার রোল নাম্বার সবচেয়ে ছোট (মানে, রোল ১ → রোল ২ → রোল ৩...), সে আগের merit position পাবে।


# ========================================================================================
# ---------------- Helper Functions ----------------
# -----------------------
# Utility helpers
# -----------------------
def parse_int_param(value):
    if value in [None, '', 'null', 'None', 'undefined']:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

def parse_int_list(value):
    if not value or value in ['null', 'None', 'undefined', '']:
        return []
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except Exception:
            return []
    if isinstance(value, list):
        out = []
        for v in value:
            iv = parse_int_param(v)
            if iv is not None:
                out.append(iv)
        return out
    return []

def safe_value(val, placeholder=""):
    return val if val not in [None, 'null', 'None'] else placeholder

def title_case(value):
    return ' '.join(word.capitalize() for word in value.split()) if value else ''

# -----------------------
# Grade map cache
# -----------------------
_grade_map_cache = {}

def _load_grade_maps(org_id, class_id, version_key):
    """
    Load and cache grade maps (50 / 100) for given org, class, and version.
    """
    key = (org_id, class_id, version_key or '')
    if key in _grade_map_cache:
        return _grade_map_cache[key]

    is_eng = version_key == "english"
    is_ban = version_key == "bangla"

    # --- Fifty marks ---
    fifty_qs = in_letter_gradeFiftyMap.objects.filter(
        org_id=org_id, class_id=class_id, is_active=True
    )
    if is_eng:
        fifty_qs = fifty_qs.filter(Q(is_english=True) | Q(is_bangla=False))
    elif is_ban:
        fifty_qs = fifty_qs.filter(Q(is_bangla=True) | Q(is_english=False))

    # --- Hundred marks ---
    hundred_qs = in_letter_gradeHundredMap.objects.filter(
        org_id=org_id, class_id=class_id, is_active=True
    )
    if is_eng:
        hundred_qs = hundred_qs.filter(Q(is_english=True) | Q(is_bangla=False))
    elif is_ban:
        hundred_qs = hundred_qs.filter(Q(is_bangla=True) | Q(is_english=False))

    def norm(qs):
        out = []
        for g in qs:
            lo = float(g.from_marks or 0)
            hi = float(g.to_marks or 0)
            gp = float(g.grade_point or 0)
            name = g.grade_id.is_grade_name if g.grade_id else ""
            out.append((lo, hi, gp, name))
        return sorted(out, key=lambda x: (x[0], x[1]))

    data = {
        '50': norm(fifty_qs),
        '100': norm(hundred_qs),
    }
    _grade_map_cache[key] = data
    return data


def find_grade(org_id, class_id, full_marks, total, version_key):
    bucket = '100' if full_marks == 100 else ('50' if full_marks == 50 else None)
    if not bucket:
        print(f"Error: Invalid full_marks={full_marks} for org_id={org_id}, class_id={class_id}")
        return "F", 0.0
    gm = _load_grade_maps(org_id, class_id, version_key)
    for lo, hi, gp, name in gm.get(bucket, []):
        if lo <= total <= hi:
            return name or "F", float(gp)
    print(f"Error: No grade found for full_marks={full_marks}, total={total}, org_id={org_id}, class_id={class_id}, version={version_key}")
    return "F", 0.0

# -----------------------
# Subjects cache
# -----------------------
_subjects_cache = {}

def subjects_for(class_id, groups_id, org_id, version_key):
    key = (class_id, groups_id, org_id, version_key or '')
    if key in _subjects_cache:
        return _subjects_cache[key]

    is_eng = version_key == "english"
    is_ban = version_key == "bangla"

    base_filter = {
        "class_id_id": class_id,
        "groups_id_id": groups_id,
        "org_id_id": org_id,
        "is_active": True
    }

    if is_eng:
        base_filter["is_english"] = True
    elif is_ban:
        base_filter["is_bangla"] = True

    qs = (
        in_subjects.objects.filter(**base_filter)
        .annotate(
            is_numeric=Case(When(subjects_no__regex=r'^\d+$', then=Value(1)), default=Value(0), output_field=IntegerField()),
            subjects_no_int=Case(When(subjects_no__regex=r'^\d+$', then=Cast('subjects_no', IntegerField())), default=Value(999999999), output_field=IntegerField())
        )
        .only("subjects_id", "subjects_name", "is_marks", "is_pass_marks", "is_applicable_pass_marks", "is_optional", "is_not_countable")
        .order_by('-is_numeric', 'subjects_no_int', 'subjects_no')
    )

    templ = []
    for s in qs:
        templ.append({
            "id": s.subjects_id,
            "name": s.subjects_name or "Subject",
            "full_marks": s.is_marks,
            "pass_marks": s.is_pass_marks or 0,
            "is_applicable_pass_marks": bool(s.is_applicable_pass_marks),
            "modes": {},
            "is_optional": False,
            "is_not_countable": bool(s.is_not_countable),
            "letter_grade": "",
            "gp": "-",
        })
    _subjects_cache[key] = templ
    return templ

# -----------------------
# Mode ordering cache
# -----------------------
_active_modes = {}

def ensure_modes_loaded(mode_names):
    needs = [n for n in mode_names if n and n not in _active_modes]
    if needs:
        for m in defaults_exam_modes.objects.filter(is_active=True, is_mode_name__in=needs).only(
            "is_mode_name", "order_by", "def_mode_id"
        ):
            _active_modes[m.is_mode_name] = (m.order_by, m.is_mode_name, m.def_mode_id)

# -----------------------
# Main View
# -----------------------
@login_required()
def print_multiple_transcripts(request):
    if request.method != "POST":
        return HttpResponse("Invalid request method", status=400)

    try:
        print_blocks = json.loads(request.POST.get("print_blocks", "[]"))
    except Exception:
        return HttpResponse("Invalid print_blocks data", status=400)

    writer = PdfWriter()
    now_str = timezone.now().strftime("%d/%m/%Y, %H:%M:%S")

    printed_keys = set()  # Global deduplication: (reg_id, section_id, version_key)

    for block in print_blocks:
        org_id = parse_int_param(block.get("org_id"))
        branch_id = parse_int_param(block.get("branch_id"))
        class_id = parse_int_param(block.get("class_id"))
        shift_id = parse_int_param(block.get("shift_id"))
        groups_id = parse_int_param(block.get("groups_id"))
        is_version = block.get("is_version")
        reg_ids = parse_int_list(block.get("reg_ids", []))
        section_ids = parse_int_list(block.get("section_ids", []))
        merit_id = parse_int_param(block.get("merit_id"))
        is_year = block.get("is_year")

        version_key = "english" if is_version == "english" else ("bangla" if is_version == "bangla" else None)
        is_eng = (version_key == "english")
        is_ban = (version_key == "bangla")

        # ---------------------------
        # Grade table
        # ---------------------------
        fifty_ids = in_letter_gradeFiftyMap.objects.filter(
            org_id_id=org_id, class_id_id=class_id, is_active=True,
            is_english=is_eng, is_bangla=is_ban
        ).values_list("grade_id", flat=True)
        
        hundred_ids = in_letter_gradeHundredMap.objects.filter(
            org_id_id=org_id, class_id_id=class_id, is_active=True,
            is_english=is_eng, is_bangla=is_ban
        ).values_list("grade_id", flat=True)
        grade_ids = set(list(fifty_ids) + list(hundred_ids))
        
        table_data = []
        
        if grade_ids:
            for grade in in_letter_grade_mode.objects.filter(grade_id__in=grade_ids).order_by("grade_id"):
                fifty_map = in_letter_gradeFiftyMap.objects.filter(
                    org_id_id=org_id, class_id_id=class_id, grade_id=grade,
                    is_active=True, is_english=is_eng, is_bangla=is_ban
                ).first()
                
                hundred_map = in_letter_gradeHundredMap.objects.filter(
                    org_id_id=org_id, class_id_id=class_id, grade_id=grade,
                    is_active=True, is_english=is_eng, is_bangla=is_ban
                ).first()
                
                fifty_interval = f"{int(fifty_map.from_marks)}-{int(fifty_map.to_marks)}" if fifty_map else ""
                hundred_interval = f"{int(hundred_map.from_marks)}-{int(hundred_map.to_marks)}" if hundred_map else ""
                
                grade_point = (
                    round(fifty_map.grade_point, 2) if fifty_map
                    else (round(hundred_map.grade_point, 2) if hundred_map else "")
                )
                table_data.append({
                    "grade_name": grade.is_grade_name,
                    "fifty_interval": fifty_interval,
                    "hundred_interval": hundred_interval,
                    "grade_point": grade_point,
                })

        # ---------------------------
        # Fetch card entries
        # ---------------------------
        filter_q = Q(org_id_id=org_id, branch_id_id=branch_id)
        if class_id:
            filter_q &= Q(class_id_id=class_id)
        if shift_id:
            filter_q &= Q(shift_id_id=shift_id)
        if groups_id:
            filter_q &= Q(groups_id_id=groups_id)
        if section_ids:
            filter_q &= Q(section_id_id__in=section_ids)
        if reg_ids:
            filter_q &= Q(reg_id_id__in=reg_ids)

        card_entries_qs = in_results_card_entry.objects.filter(filter_q).select_related(
            "class_id", "section_id", "shift_id", "groups_id",
            "org_id", "branch_id", "reg_id", "is_approved_by"
        ).order_by("res_card_id")

        card_entries = list(card_entries_qs)
        if not card_entries:
            continue

        # ---------------------------
        # Fetch merit positions
        # ---------------------------
        reg_id_set = {ce.reg_id_id for ce in card_entries if ce.reg_id_id}
        merit_pos_by_reg = {}
        if merit_id and reg_id_set:
            for md in in_merit_position_approvaldtls.objects.filter(
                merit_id_id=merit_id, reg_id_id__in=reg_id_set
            ).only("reg_id_id", "merit_position"):
                rid = md.reg_id_id
                mp = md.merit_position
                if rid not in merit_pos_by_reg or (mp is not None and mp < merit_pos_by_reg[rid]):
                    merit_pos_by_reg[rid] = mp

        # ---------------------------
        # Deduplicate globally by (reg_id, section_id, version)
        # ---------------------------
        unique_card_map = {}
        for ce in card_entries:
            key = (ce.reg_id_id, ce.section_id_id, version_key)
            if not ce.reg_id_id or key in printed_keys:
                continue
            current_merit = merit_pos_by_reg.get(ce.reg_id_id)
            if key not in unique_card_map:
                unique_card_map[key] = ce
            else:
                existing_merit = merit_pos_by_reg.get(ce.reg_id_id)
                if current_merit is not None and (existing_merit is None or current_merit < existing_merit):
                    unique_card_map[key] = ce

        for key in unique_card_map.keys():
            printed_keys.add(key)

        card_entries = list(unique_card_map.values())
        if not card_entries:
            continue

        # ---------------------------
        # Group results by section/version
        # ---------------------------
        groups = defaultdict(list)
        for ce in card_entries:
            groups[(ce.section_id_id, ce.is_english, ce.is_bangla)].append(ce)

        results_by_reg = {}
        exam_type_name_by_reg = {}
        mode_names_seen = set()

        for (sec_id, ce_is_eng, ce_is_ban), ces in groups.items():
            group_reg_ids = [c.reg_id_id for c in ces if c.reg_id_id]
            if not group_reg_ids:
                continue

            rqs = (
                in_result_finalizationdtls.objects
                .filter(
                    org_id_id=org_id,
                    branch_id_id=branch_id,
                    class_id_id=class_id if class_id else None,
                    section_id_id=sec_id if sec_id else None,
                    finalize_year=is_year,
                    is_english=ce_is_eng,
                    is_bangla=ce_is_ban,
                    is_half_yearly=True,
                    is_approved=True,
                    reg_id_id__in=group_reg_ids,
                )
                .select_related("subject_id", "exam_type_id", "def_mode_id")
                .only(
                    "reg_id_id",
                    "subject_id__subjects_id",
                    "def_mode_id__def_mode_id",
                    "is_mode_name",
                    "is_actual_marks",
                    "is_pass_marks",
                    "is_default_marks",
                    "exam_type_id__exam_type_name",
                )
            )

            for r in rqs:
                rid = r.reg_id_id
                sid = r.subject_id.subjects_id if r.subject_id else None
                if not sid:
                    continue
                results_by_reg.setdefault(rid, {}).setdefault(sid, {})[r.is_mode_name] = {
                    "def_mode_id": r.def_mode_id.def_mode_id if r.def_mode_id else None,
                    "actual": float(r.is_actual_marks or 0),
                    "pass": float(r.is_pass_marks or 0),
                    "default": float(r.is_default_marks or 0),
                }
                mode_names_seen.add(r.is_mode_name)
                if rid not in exam_type_name_by_reg and r.exam_type_id:
                    exam_type_name_by_reg[rid] = r.exam_type_id.exam_type_name

        # ---------------------------
        # Load modes ordering
        # ---------------------------
        ensure_modes_loaded(mode_names_seen)
        mode_names_ordered = [t[1] for t in sorted(_active_modes.values(), key=lambda x: (x[0], x[1]))] if _active_modes else []

        # ---------------------------
        # Build transactions
        # ---------------------------
        transactions = []
        for ce in card_entries:
            registration = ce.reg_id
            reg_results = results_by_reg.get(ce.reg_id_id, {})

            subj_template = subjects_for(
                registration.class_id_id if registration and getattr(registration, "class_id_id", None) else class_id,
                registration.groups_id_id if registration and getattr(registration, "groups_id_id", None) else groups_id,
                org_id,
                version_key
            )
            subjects_list = copy.deepcopy(subj_template)
            optional_id = getattr(registration, "is_optional_sub_id", None)
            for sub in subjects_list:
                sub["is_optional"] = (optional_id is not None and sub["id"] == optional_id)
                sub["modes"] = copy.deepcopy(reg_results.get(sub["id"], {}))
                
                # ---------------------------
                # Total calculation without floor
                # ---------------------------
                safe_total = sum(float(m["actual"]) for m in sub["modes"].values()) if sub["modes"] else 0.0
                total = round(safe_total, 2)

                if sub["is_not_countable"]:
                    sub["letter_grade"] = "-"
                    sub["gp"] = "-"
                else:
                    failed_flag = False

                    if sub["is_applicable_pass_marks"]:
                        # Only total compared with pass_marks
                        failed_flag = total < float(sub["pass_marks"])
                    else:
                        # Each mode compared individually with pass marks for that mode
                        for m in sub["modes"].values():
                            if float(m["actual"]) < float(m["pass"]):
                                failed_flag = True
                                break  # fail if any mode < mode.pass

                    if failed_flag:
                        sub["letter_grade"] = "F"
                        sub["gp"] = 0.0
                    else:
                        # Use full_marks and total to find grade
                        letter, gp = find_grade(org_id, class_id, sub["full_marks"], total, version_key)
                        sub["letter_grade"] = letter
                        sub["gp"] = gp

            merit_position = merit_pos_by_reg.get(ce.reg_id_id)
            exam_type_name = exam_type_name_by_reg.get(ce.reg_id_id, "N/A")

            transactions.append({
                'create_date': safe_value(getattr(ce, "create_date", None)),
                'reg_id': safe_value(ce.reg_id.reg_id if ce.reg_id else ''),
                'org_name': safe_value(ce.org_id.org_name if ce.org_id else ''),
                'full_name': safe_value(title_case(ce.reg_id.full_name) if ce.reg_id else ''),
                'roll_no': safe_value(ce.reg_id.roll_no if ce.reg_id else ''),
                'father_name': safe_value(title_case(getattr(ce.reg_id, "father_name", None)) if ce.reg_id else ''),
                'mother_name': safe_value(title_case(getattr(ce.reg_id, "mother_name", None)) if ce.reg_id else ''),
                'class_name': safe_value(ce.class_id.class_name if ce.class_id else ''),
                'section_name': safe_value(ce.section_id.section_name if ce.section_id else ''),
                'shift_name': safe_value(ce.shift_id.shift_name if ce.shift_id else ''),
                'merit_position': merit_position,
                'version': version_key,
                'exam_type_name': safe_value(exam_type_name, "N/A"),
                'total_working_days': safe_value(getattr(ce, "total_working_days", None)),
                'total_present_days': safe_value(getattr(ce, "total_present_days", None)),
                'is_remarks': safe_value(getattr(ce, "is_remarks", None)),
                'date_of_publication': safe_value(getattr(ce, "date_of_publication", None)),
                'is_average_gpa': safe_value(getattr(ce, "is_average_gpa", None)),
                'average_letter_grade': safe_value(getattr(ce, "average_letter_grade", None)),
                'result_status': safe_value(getattr(ce, "result_status", None)),
                'total_obtained_marks': safe_value(getattr(ce, "total_obtained_marks", None)),
                'subjects': subjects_list,
                'mode_names': mode_names_ordered,
            })

            transactions = sorted(transactions, key=lambda x: (x.get("merit_position") is None, x.get("merit_position") or 0))

        # ---------------------------
        # Render PDFs
        # ---------------------------
        combined_html = ""
        for transaction in transactions:
            context = {"transaction": transaction, "printed_on": now_str, "table_data": table_data}
            html_string = render_to_string(
                "result_card_entry/print_result_card_half_yearly_report.html",
                context
            )
            combined_html += f'<div style="page-break-after: always;">{html_string}</div>'

        # Remove the last page break
        combined_html = re.sub(r'<div style="page-break-after: always;">\s*$', '', combined_html)

        pdf = HTML(string=combined_html, base_url=request.build_absolute_uri('/')).write_pdf()

        response = HttpResponse(pdf, content_type="application/pdf")
        response['Content-Disposition'] = 'inline; filename="Academic_Transcript_Report.pdf"'
        return response



# # --- helpers stay the same (safe, tiny improvements) ---
# def parse_int_param(value):
#     """
#     Safe int parser:
#     - যদি value None, '', 'null', 'None', 'undefined' হয় → None ফেরত দেবে
#     - যদি সংখ্যা হয় → int ফেরত দেবে
#     """
#     if value in [None, '', 'null', 'None', 'undefined']:
#         return None
#     try:
#         return int(value)
#     except (TypeError, ValueError):
#         return None

# def parse_int_list(value):
#     """Safe list of ints parser"""
#     if not value or value in ['null', 'None', 'undefined', '']:
#         return []
#     if isinstance(value, str):
#         try:
#             value = json.loads(value)  # JSON string হলে list বানাবে
#         except Exception:
#             return []
#     if isinstance(value, list):
#         out = []
#         for v in value:
#             iv = parse_int_param(v)
#             if iv is not None:
#                 out.append(iv)
#         return out
#     return []

# def safe_value(val, placeholder="Missing"):
#     return val if val not in [None, '', 'null', 'None'] else f"[{placeholder}]"

# def title_case(value):
#     return ' '.join(word.capitalize() for word in value.split()) if value else ''


# def print_multiple_transcripts(request):
#     if request.method != "POST":
#         return HttpResponse("Invalid request method", status=400)

#     try:
#         print_blocks = json.loads(request.POST.get("print_blocks", "[]"))
#     except Exception:
#         return HttpResponse("Invalid print_blocks data", status=400)

#     # ------------- CACHES / BATCH HELPERS -------------
#     # subjects cache key: (class_id, groups_id, org_id, versionStr)
#     subjects_cache = {}
#     # grade map cache key: (org_id, class_id) -> {'50': [(from,to,grade_point,grade_name)], '100': [...]}
#     grade_map_cache = {}
#     # defaults_exam_modes: cache of active modes ordered; but we still order per set we actually see
#     active_modes_by_name = {}  # name -> (order_by, name, id)
#     # A tiny memo for mode order queries
#     modes_loaded = False

#     def load_grade_maps(org_id, class_id, version_key):
#         """
#         Load and cache both 50 and 100 marks grade maps for an (org, class).
#         Structure for faster lookup by total: list of tuples.
#         """
#         key = (org_id, class_id, version_key)
#         if key in grade_map_cache:
#             return grade_map_cache[key]
        
#         is_eng = version_key == "english"
#         is_ban = version_key == "bangla"

#         fifty_qs = list(
#             in_letter_gradeFiftyMap.objects.filter(
#                 org_id_id=org_id, class_id_id=class_id, is_english=is_eng, is_bangla=is_ban, is_active=True
#             ).select_related("grade_id")
#         )
#         hundred_qs = list(
#             in_letter_gradeHundredMap.objects.filter(
#                 org_id_id=org_id, class_id_id=class_id, is_english=is_eng, is_bangla=is_ban, is_active=True
#             ).select_related("grade_id")
#         )
#         def to_tuples(qs):
#             # Keep original boundaries as-is to preserve behavior
#             out = []
#             for g in qs:
#                 out.append((
#                     float(g.from_marks or 0),
#                     float(g.to_marks or 0),
#                     float(g.grade_point or 0),
#                     g.grade_id.is_grade_name if g.grade_id else ""
#                 ))
#             # sort for predictable scanning (optional)
#             out.sort(key=lambda x: (x[0], x[1]))
#             return out

#         data = {
#             '50': to_tuples(fifty_qs),
#             '100': to_tuples(hundred_qs),
#         }
#         grade_map_cache[key] = data
#         return data

#     def find_grade(org_id, class_id, full_marks, total, version_key):
#         """
#         Match total in [from, to] range from cached grade map.
#         """
#         gm = load_grade_maps(org_id, class_id, version_key)
#         bucket = '100' if full_marks == 100 else ('50' if full_marks == 50 else None)
#         if bucket is None:
#             return None
#         for lo, hi, gp, name in gm[bucket]:
#             # inclusive bounds as in original query (from_marks__lte & to_marks__gte)
#             if lo <= total <= hi:
#                 return name, gp
#         return None



#     def subjects_for(class_id, groups_id, org_id, version_key):
#         """
#         Load subjects once per (class, groups, org, versionFlag).
#         Returns a list of dict *templates*; caller must deepcopy before using.
        
#         """
#         key = (class_id, groups_id, org_id, version_key or '')
#         if key in subjects_cache:
#             return subjects_cache[key]

#         is_eng = version_key == "english"
#         is_ban = version_key == "bangla"

#         base_filter = {"class_id_id": class_id, "groups_id_id": groups_id, "org_id_id": org_id, "is_active": True}
#         if is_eng:
#             base_filter["is_english"] = True
#         elif is_ban:
#             base_filter["is_bangla"] = True

#         qs = (
#             in_subjects.objects.filter(**base_filter)
#             .annotate(
#                 is_numeric=Case(
#                     When(subjects_no__regex=r'^\d+$', then=Value(1)),
#                     default=Value(0),
#                     output_field=IntegerField(),
#                 ),
#                 subjects_no_int=Case(
#                     When(subjects_no__regex=r'^\d+$', then=Cast('subjects_no', IntegerField())),
#                     default=Value(999999999),
#                     output_field=IntegerField(),
#                 )
#             )
#             .only(
#                 "subjects_id",
#                 "subjects_name",
#                 "is_marks",
#                 "is_pass_marks",
#                 "is_applicable_pass_marks",
#                 "is_optional",
#                 "is_not_countable",
#             )
#             .order_by('-is_numeric', 'subjects_no_int', 'subjects_no')
#         )

#         templ = []
#         for s in qs:
#             templ.append({
#                 "id": s.subjects_id,
#                 "name": safe_value(s.subjects_name, "Subject"),
#                 "full_marks": s.is_marks,
#                 "pass_marks": s.is_pass_marks or 0,
#                 "is_applicable_pass_marks": s.is_applicable_pass_marks,
#                 "modes": {},  # will be filled per student
#                 "is_optional": False,  # will be set per student comparing registration.is_optional_sub_id
#                 "is_not_countable": s.is_not_countable,
#                 "letter_grade": "",
#                 "gp": "-"
#             })
#         subjects_cache[key] = templ
#         return templ

#     def ensure_modes_loaded(names):
#         """
#         Fill active_modes_by_name for given mode names once, keeping their order_by.
#         """
#         nonlocal modes_loaded
#         needs = [n for n in names if n not in active_modes_by_name]
#         if needs:
#             # load ONLY requested names to reduce query load
#             for m in defaults_exam_modes.objects.filter(is_active=True, is_mode_name__in=needs).only("is_mode_name", "order_by", "def_mode_id"):
#                 active_modes_by_name[m.is_mode_name] = (m.order_by, m.is_mode_name, m.def_mode_id)
#         modes_loaded = True

#     # ---------------------------------------------
#     # MAIN LOOP (block by block)
#     # ---------------------------------------------
#     combined_html = ""
#     pdf_buffers = []
#     now_str = timezone.now().strftime("%d/%m/%Y, %H:%M:%S")

#     for block in print_blocks:
#         org_id = parse_int_param(block.get("org_id"))
#         branch_id = parse_int_param(block.get("branch_id"))
#         class_id = parse_int_param(block.get("class_id"))
#         shift_id = parse_int_param(block.get("shift_id"))
#         groups_id = parse_int_param(block.get("groups_id"))
#         is_version = block.get("is_version")
#         reg_ids = parse_int_list(block.get("reg_ids", []))
#         section_ids = parse_int_list(block.get("section_ids", []))
#         merit_id = parse_int_param(block.get("merit_id"))
#         is_year = block.get("is_year")
        
#         version_key = "english" if is_version == "english" else ("bangla" if is_version == "bangla" else None)
#         is_eng = version_key == "english"
#         is_ban = version_key == "bangla"

#         # ---------------------------
#         # Grade mapping table (load ONCE per block)
#         # ---------------------------
#         # collect active grade_ids from both maps (exact as original, but single fetch)
#         fifty_grades = in_letter_gradeFiftyMap.objects.filter(
#             org_id=org_id, class_id=class_id, is_active=True,
#             is_english=is_eng, is_bangla=is_ban
#         ).values_list("grade_id", flat=True)

#         hundred_grades = in_letter_gradeHundredMap.objects.filter(
#             org_id=org_id, class_id=class_id, is_active=True,
#             is_english=is_eng, is_bangla=is_ban
#         ).values_list("grade_id", flat=True)

#         grade_ids = set(list(fifty_grades) + list(hundred_grades))

#         grades = in_letter_grade_mode.objects.filter(
#             grade_id__in=grade_ids
#         ).order_by("grade_id")

#         table_data = []
#         for grade in grades:
#             fifty_map = in_letter_gradeFiftyMap.objects.filter(
#                 org_id=org_id, class_id=class_id, grade_id=grade,
#                 is_active=True, is_english=is_eng, is_bangla=is_ban
#             ).first()
#             hundred_map = in_letter_gradeHundredMap.objects.filter(
#                 org_id=org_id, class_id=class_id, grade_id=grade,
#                 is_active=True, is_english=is_eng, is_bangla=is_ban
#             ).first()

#             fifty_interval = f"{int(fifty_map.from_marks)}-{int(fifty_map.to_marks)}" if fifty_map else ""
#             hundred_interval = f"{int(hundred_map.from_marks)}-{int(hundred_map.to_marks)}" if hundred_map else ""

#             grade_point = round(fifty_map.grade_point, 2) if fifty_map else (round(hundred_map.grade_point, 2) if hundred_map else "")

#             table_data.append({
#                 "grade_name": grade.is_grade_name,
#                 "fifty_interval": fifty_interval,
#                 "hundred_interval": hundred_interval,
#                 "grade_point": grade_point,
#             })

#         # ---------------------------
#         # Card entries for this block (single query)
#         # ---------------------------
#         filter_q = Q(org_id_id=org_id, branch_id_id=branch_id)
#         if class_id: filter_q &= Q(class_id_id=class_id)
#         if shift_id: filter_q &= Q(shift_id_id=shift_id)
#         if groups_id: filter_q &= Q(groups_id_id=groups_id)
#         if section_ids: filter_q &= Q(section_id_id__in=section_ids)
#         if reg_ids: filter_q &= Q(reg_id_id__in=reg_ids)

#         card_entries = list(
#             in_results_card_entry.objects.filter(filter_q)
#             .select_related(
#                 "class_id", "section_id", "shift_id", "groups_id",
#                 "org_id", "branch_id", "reg_id",
#                 "is_approved_by"
#             )
#             .order_by("reg_id__reg_id2merit_positiondtls__merit_position")
#         )

#         if not card_entries:
#             # nothing to print in this block; continue
#             continue

#         # ---------------------------
#         # Merit positions (batch)
#         # ---------------------------
#         reg_id_set = {ce.reg_id_id for ce in card_entries if ce.reg_id_id}
#         merit_pos_by_reg = {}
#         if merit_id and reg_id_set:
#             for md in in_merit_position_approvaldtls.objects.filter(
#                 merit_id_id=merit_id, reg_id_id__in=reg_id_set
#             ).only("reg_id_id", "merit_position"):
#                 merit_pos_by_reg[md.reg_id_id] = md.merit_position

#         # ---------------------------
#         # Subjects cache key per version
#         # ---------------------------
#         version_key = "english" if is_version == "english" else ("bangla" if is_version == "bangla" else None)

#         # ---------------------------
#         # Result details (batch by grouping common filters)
#         # Group by: (section_id, is_english, is_bangla) because other filters are common in this block.
#         # ---------------------------
#         groups = defaultdict(list)
#         for ce in card_entries:
#             groups[(ce.section_id_id, ce.is_english, ce.is_bangla)].append(ce)

#         # reg -> subject_id -> mode_name -> detail dict
#         results_by_reg = {}
#         # reg -> exam_type_name (first seen)
#         exam_type_name_by_reg = {}

#         for (sec_id, ce_is_eng, ce_is_ban), ces in groups.items():
#             reg_ids_group = [c.reg_id_id for c in ces if c.reg_id_id]
#             if not reg_ids_group:
#                 continue

#             rqs = (in_result_finalizationdtls.objects
#                    .filter(
#                        org_id_id=org_id,
#                        branch_id_id=branch_id,
#                        class_id_id=class_id if class_id else None,
#                        section_id_id=sec_id if sec_id else None,
#                        finalize_year=is_year,
#                        is_english=ce_is_eng,
#                        is_bangla=ce_is_ban,
#                        is_half_yearly=True,
#                        is_approved=True,
#                        reg_id_id__in=reg_ids_group
#                    )
#                    .select_related("subject_id", "exam_type_id", "def_mode_id")
#                    .only("reg_id_id", "subject_id__subjects_id", "def_mode_id__def_mode_id",
#                          "is_mode_name", "is_actual_marks", "is_pass_marks", "is_default_marks",
#                          "exam_type_id__exam_type_name"))

#             # Collect mode names for ordering once
#             mode_names = set()

#             for r in rqs:
#                 rid = r.reg_id_id
#                 sid = r.subject_id.subjects_id if r.subject_id else None
#                 if not sid:
#                     continue
#                 if rid not in results_by_reg:
#                     results_by_reg[rid] = {}
#                 if sid not in results_by_reg[rid]:
#                     results_by_reg[rid][sid] = {}
#                 results_by_reg[rid][sid][r.is_mode_name] = {
#                     "def_mode_id": r.def_mode_id.def_mode_id if r.def_mode_id else None,
#                     "actual": float(r.is_actual_marks or 0),
#                     "pass": float(r.is_pass_marks or 0),
#                     "default": float(r.is_default_marks or 0)
#                 }
#                 mode_names.add(r.is_mode_name)
#                 # store first exam_type_name for this reg
#                 if rid not in exam_type_name_by_reg and r.exam_type_id:
#                     exam_type_name_by_reg[rid] = r.exam_type_id.exam_type_name

#             # Load ordering for these modes
#             if mode_names:
#                 ensure_modes_loaded(mode_names)

#         # Build a single ordered mode list present in this block (keeps previous behavior of dynamic modes)
#         # We respect order_by across all modes we saw, then sort by that.
#         if active_modes_by_name:
#             mode_names_ordered = [t[1] for t in sorted(active_modes_by_name.values(), key=lambda x: (x[0], x[1]))]
#         else:
#             mode_names_ordered = []

#         # ---------------------------
#         # Render each card (no DB in loop except grade lookup cache hit)
#         # ---------------------------
#         for ce in card_entries:
#             registration = ce.reg_id  # already selected via select_related
#             # subjects template (deepcopy because we mutate per student)
#             subj_template = subjects_for(
#                 registration.class_id_id if registration and registration.class_id_id else class_id,
#                 registration.groups_id_id if registration else groups_id,
#                 org_id,
#                 version_key
#             )
#             subjects_list = copy.deepcopy(subj_template)

#             # mark optional per student
#             optional_id = registration.is_optional_sub_id if registration else None
#             for sub in subjects_list:
#                 sub["is_optional"] = (sub["id"] == optional_id) and (optional_id is not None) and any([
#                     True  # retains original logic: s.is_optional AND id match
#                 ])

#             # results for this student
#             reg_results = results_by_reg.get(ce.reg_id_id, {})
#             # fill modes and compute grade/gp
#             for sub in subjects_list:
#                 sub["modes"] = reg_results.get(sub["id"], {})
#                 safe_total = sum(float(m["actual"]) for m in sub["modes"].values()) if sub["modes"] else 0.0
#                 total = math.floor(safe_total)

#                 if sub["is_not_countable"]:
#                     sub["letter_grade"] = "-"
#                     sub["gp"] = "-"
#                     continue

#                 # pass / fail logic identical to original
#                 if not sub["is_applicable_pass_marks"]:
#                     failed_flag = any(float(m["actual"]) < float(m["pass"]) for m in sub["modes"].values())
#                 else:
#                     failed_flag = total < sub["pass_marks"]

#                 if failed_flag:
#                     sub["letter_grade"] = "F"
#                     sub["gp"] = 0.00
#                     continue

#                 # map to grade range (cached lookups)
#                 full_marks = sub["full_marks"]
#                 if full_marks in (50, 100):
#                     gfound = find_grade(org_id, registration.class_id_id if registration else class_id, full_marks, total, version_key)
#                     if gfound:
#                         sub["letter_grade"], sub["gp"] = gfound[0], float(gfound[1])
#                     else:
#                         sub["letter_grade"] = "F"
#                         sub["gp"] = 0.00
#                 else:
#                     # original code only graded 50/100; keep same fallback
#                     sub["letter_grade"] = "F"
#                     sub["gp"] = 0.00

#             # Merit
#             merit_position = merit_pos_by_reg.get(ce.reg_id_id, 0)

#             # Exam type name (first seen for this reg in batch)
#             exam_type_name = exam_type_name_by_reg.get(ce.reg_id_id)

#             # ---------------------------
#             # Transaction context
#             # ---------------------------
#             transaction = {
#                 'create_date': safe_value(ce.create_date),
#                 'reg_id': safe_value(ce.reg_id.reg_id if ce.reg_id else ''),
#                 'org_name': safe_value(ce.org_id.org_name if ce.org_id else ''),
#                 'full_name': safe_value(title_case(ce.reg_id.full_name) if ce.reg_id else ''),
#                 'roll_no': safe_value(ce.reg_id.roll_no if ce.reg_id else ''),
#                 'father_name': safe_value(title_case(ce.reg_id.father_name) if ce.reg_id else ''),
#                 'mother_name': safe_value(title_case(ce.reg_id.mother_name) if ce.reg_id else ''),
#                 'class_name': safe_value(ce.class_id.class_name if ce.class_id else ''),
#                 'section_name': safe_value(ce.section_id.section_name if ce.section_id else ''),
#                 'shift_name': safe_value(ce.shift_id.shift_name if ce.shift_id else ''),
#                 'merit_position': safe_value(merit_position, "N/A"),
#                 'version': version_key,
#                 'exam_type_name': safe_value(exam_type_name, "N/A"),
#                 'total_working_days': safe_value(ce.total_working_days),
#                 'total_present_days': safe_value(ce.total_present_days),
#                 'is_remarks': safe_value(ce.is_remarks),
#                 'date_of_publication': safe_value(ce.date_of_publication),
#                 'is_average_gpa': safe_value(ce.is_average_gpa),
#                 'average_letter_grade': safe_value(ce.average_letter_grade),
#                 'result_status': safe_value(ce.result_status),
#                 'total_obtained_marks': safe_value(ce.total_obtained_marks),
#                 'subjects': subjects_list,
#                 'mode_names': mode_names_ordered,
#             }

#             context = {
#                 "transaction": transaction,
#                 "printed_on": now_str,
#                 "table_data": table_data,
#             }

#             html_string = render_to_string("result_card_entry/print_result_card_half_yearly_report.html", context)
#             pdf_buffers.append(HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf())

#     # ---------------- Merge PDFs ----------------
#     writer = PdfWriter()
#     from io import BytesIO
#     for pdf_bytes in pdf_buffers:
#         reader = PdfReader(BytesIO(pdf_bytes))
#         for page in reader.pages:
#             writer.add_page(page)

#     merged_io = BytesIO()
#     writer.write(merged_io)
#     merged_io.seek(0)

#     response = HttpResponse(merged_io.read(), content_type='application/pdf')
#     response['Content-Disposition'] = 'inline; filename="Academic_Transcript_Merged.pdf"'
#     return response
    


    # # *************** for PDFKit ***************
    #         # প্রতিটি student এর জন্য html add করো
    #         html_string = render_to_string("result_card_entry/print_result_card_half_yearly_report_pdfkit.html", context)
            
    #         combined_html += f'<div style="page-break-after: always;">{html_string}</div>'

    #         # শেষ page-break মুছে ফেলো
    #         combined_html = re.sub(r'<div style="page-break-after: always;">\s*$', '', combined_html)

    #         # wkhtmltopdf config
    #         if os.name == "nt":
    #             config = pdfkit.configuration(wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")
    #         else:
    #             config = pdfkit.configuration(wkhtmltopdf="/usr/bin/wkhtmltopdf")
    #         options = {
    #             'page-size': 'A4',
    #             'encoding': "UTF-8",
    #             'enable-local-file-access': True,
    #             'margin-top': '0.4in',
    #             'margin-right': '0.3in',
    #             'margin-bottom': '0.4in',
    #             'margin-left': '0.3in',
    #         }

    #     # Generate PDF
    #     pdf = pdfkit.from_string(combined_html, False, configuration=config, options=options)

    #     # Response
    #     response = HttpResponse(pdf, content_type='application/pdf')
    #     response['Content-Disposition'] = 'inline; filename="Academic_Transcript_Report.pdf"'
    #     return response


    # # *************** for weasyprint ***************
    #         html_string = render_to_string("result_card_entry/print_result_card_half_yearly_report.html", context)
    #         combined_html += f'<div style="page-break-after: always;">{html_string}</div>'

    # # Remove last page breaks
    # combined_html = re.sub(r'<div style="page-break-after: always;">\s*$', '', combined_html)

    # pdf = HTML(string=combined_html, base_url=request.build_absolute_uri('/')).write_pdf()
    # response = HttpResponse(pdf, content_type='application/pdf')
    # response['Content-Disposition'] = 'inline; filename="Academic_Transcript_Report.pdf"'
    # return response

    # # *************** for weasyprint ***************


    # ids = request.GET.get('ids', '')
    # id_list = [res_id for res_id in ids.split(',') if res_id.isdigit()]

    # # ----------------------------
    # # Helper functions
    # # ----------------------------
    # def parse_int_param(value):
    #     return int(value) if value and value not in ['null', 'None'] else None

    # def safe_value(val, placeholder="Missing"):
    #     """Return safe value with placeholder if missing"""
    #     return val if val not in [None, '', 'null', 'None'] else f"[{placeholder}]"

    # def title_case(value):
    #     if value:
    #         return ' '.join(word.capitalize() for word in value.split())
    #     return ''

    # is_class = parse_int_param(request.GET.get('is_class', ''))
    # is_section = parse_int_param(request.GET.get('is_section', ''))
    # is_shift = parse_int_param(request.GET.get('is_shift', ''))
    # is_groups = parse_int_param(request.GET.get('is_groups', ''))

    # combined_html = ""

    # for res_id in id_list:
    #     try:
    #         card_entry = in_results_card_entry.objects.select_related(
    #             'class_id', 'section_id', 'shift_id', 'groups_id',
    #             'org_id', 'branch_id', 'reg_id'
    #         ).get(res_card_id=int(res_id))
    #     except in_results_card_entry.DoesNotExist:
    #         continue

    #     # ----------------------------
    #     # Class filter
    #     # ----------------------------
    #     filter_q = Q(org_id=card_entry.org_id, branch_id=card_entry.branch_id)

    #     if is_class:
    #         filter_q &= Q(class_id=is_class)
    #     if is_section:
    #         filter_q &= Q(section_id=is_section)
    #     if is_shift:
    #         filter_q &= Q(shift_id=is_shift)
    #     if is_groups:
    #         filter_q &= Q(groups_id=is_groups)

    #     class_entries = in_results_card_entry.objects.filter(filter_q).select_related('reg_id')

    #     # ----------------------------
    #     # Sort by GPA, marks, roll
    #     # ----------------------------
    #     def sort_key(entry):
    #         gpa = float(entry.is_average_gpa or 0.0)
    #         total = int(entry.total_obtained_marks or 0)
    #         roll = int(entry.reg_id.roll_no) if (entry.reg_id and entry.reg_id.roll_no and entry.reg_id.roll_no.isdigit()) else 99999
    #         return (-gpa, -total, roll)

    #     sorted_entries = sorted(class_entries, key=sort_key)

    #     # Merit positions
    #     ranking_map = {}
    #     previous_key = None
    #     current_position = 1
    #     merit_counter = 1

    #     for entry in sorted_entries:
    #         key = sort_key(entry)
    #         if previous_key is not None and key == previous_key:
    #             pass
    #         else:
    #             merit_counter = current_position
    #         ranking_map[entry.res_card_id] = merit_counter
    #         previous_key = key
    #         current_position += 1

    #     calculated_merit_position = ranking_map.get(card_entry.res_card_id, '')

    #     # ----------------------------
    #     # Subjects
    #     # ----------------------------
    #     registration = get_object_or_404(in_registrations, reg_id=card_entry.reg_id.reg_id)

    #     version = request.GET.get('is_version', '')  # 'english' or 'bangla'
    #     base_filter = {
    #         "class_id": registration.class_id,
    #         "groups_id": registration.groups_id,
    #         "org_id": registration.org_id,
    #         "is_active": True
    #     }

    #     if version == "english":
    #         base_filter["is_english"] = True
    #     elif version == "bangla":
    #         base_filter["is_bangla"] = True

    #     # subjects_qs = in_subjects.objects.filter(**base_filter).order_by("subjects_no")
    #     subjects_qs = (
    #         in_subjects.objects
    #         .filter(**base_filter)
    #         .annotate(
    #             is_numeric=Case(
    #                 When(subjects_no__regex=r'^\d+$', then=Value(1)),  # pure digits হলে 1
    #                 default=Value(0),  # নাহলে 0
    #                 output_field=IntegerField(),
    #             ),
    #             subjects_as_int=Case(
    #                 When(subjects_no__regex=r'^\d+$', then=Cast('subjects_no', IntegerField())),
    #                 default=Value(999999999),  # non-numeric হলে একেবারে শেষে
    #                 output_field=IntegerField(),
    #             )
    #         )
    #         .order_by('-is_numeric', 'subjects_as_int', 'subjects_no')  
    #     )

    #     subjects_list = []
    #     for s in subjects_qs:
    #         subjects_list.append({
    #             "id": s.subjects_id,
    #             "name": safe_value(s.subjects_name, "Subject"),
    #             "full_marks": s.is_marks,
    #             "pass_marks": s.is_pass_marks or 0,
    #             "is_applicable_pass_marks": s.is_applicable_pass_marks,   # <-- ADD THIS
    #             "modes": {},
    #             "is_optional": s.is_optional and s.subjects_id == registration.is_optional_sub_id,
    #             "is_not_countable": s.is_not_countable,
    #             "letter_grade": "",
    #             "gp": "-"
    #         })

    #     # ----------------------------
    #     # Results
    #     # ----------------------------
    #     result_qs = in_result_finalizationdtls.objects.filter(
    #         org_id_id=card_entry.org_id.org_id,
    #         branch_id_id=card_entry.branch_id.branch_id,
    #         reg_id_id=card_entry.reg_id.reg_id,
    #         class_id_id=card_entry.class_id.class_id,
    #         section_id_id=card_entry.section_id.section_id,
    #         finalize_year=card_entry.create_date,   # fixed year extraction
    #         is_english=card_entry.is_english,
    #         is_bangla=card_entry.is_bangla,
    #         is_half_yearly=True,
    #         is_approved=True
    #     ).select_related("subject_id")

    #     results_map = {}
    #     mode_names_set = set()
    #     for r in result_qs:
    #         sid = r.subject_id.subjects_id
    #         if sid not in results_map:
    #             results_map[sid] = {}
    #         results_map[sid][r.is_mode_name] = {
    #             "def_mode_id": r.def_mode_id.def_mode_id,
    #             "actual": float(r.is_actual_marks) if r.is_actual_marks is not None else 0.0,
    #             "pass": float(r.is_pass_marks or 0),
    #             "default": float(r.is_default_marks or 0)
    #         }
    #         mode_names_set.add(r.is_mode_name)

    #     all_modes_qs = defaults_exam_modes.objects.filter(
    #         is_active=True,
    #         is_mode_name__in=mode_names_set
    #     ).order_by("order_by")
    #     mode_names_ordered = [m.is_mode_name for m in all_modes_qs]

    #     # Calculate subject-wise grade
    #     for sub in subjects_list:
    #         sub["modes"] = results_map.get(sub["id"], {})
    #         safe_total = sum([float(m["actual"]) for m in sub["modes"].values()]) if sub["modes"] else 0.0
    #         total = math.floor(safe_total)

    #         if sub["is_not_countable"]:
    #             sub["letter_grade"] = "-"
    #             sub["gp"] = "-"
    #             continue

    #         failed_flag = False

    #         # --- NEW FAIL CHECK LOGIC ---
    #         if sub["is_applicable_pass_marks"]:
    #             # Subject-level pass mark check
    #             if float(total) < float(sub["pass_marks"]):
    #                 failed_flag = True
    #         else:
    #             # Mode-level pass mark check
    #             failed_flag = any(float(m["actual"]) < float(m["pass"]) for m in sub["modes"].values())

    #         if failed_flag:
    #             sub["letter_grade"] = "F"
    #             sub["gp"] = 0.00
    #             continue

    #         # --- GRADING LOGIC ---
    #         if sub["full_marks"] == 100:
    #             grade_qs = in_letter_gradeHundredMap.objects.filter(
    #                 org_id_id=card_entry.org_id.org_id,
    #                 class_id_id=registration.class_id,
    #                 from_marks__lte=total,
    #                 to_marks__gte=total,
    #                 is_active=True
    #             ).first()
    #         elif sub["full_marks"] == 50:
    #             grade_qs = in_letter_gradeFiftyMap.objects.filter(
    #                 org_id_id=card_entry.org_id.org_id,
    #                 class_id_id=registration.class_id,
    #                 from_marks__lte=total,
    #                 to_marks__gte=total,
    #                 is_active=True
    #             ).first()
    #         else:
    #             grade_qs = None

    #         if grade_qs:
    #             sub["letter_grade"] = grade_qs.grade_id.is_grade_name
    #             sub["gp"] = float(grade_qs.grade_point)
    #         else:
    #             sub["letter_grade"] = "F"
    #             sub["gp"] = 0.00

    #     # ----------------------------
    #     # Transaction data
    #     # ----------------------------
    #     transaction = {
    #         'create_date': safe_value(card_entry.create_date),
    #         'reg_id': safe_value(card_entry.reg_id.reg_id if card_entry.reg_id else ''),
    #         'org_name': safe_value(card_entry.org_id.org_name if card_entry.org_id else ''),
    #         'full_name': safe_value(title_case(card_entry.reg_id.full_name) if card_entry.reg_id else ''),
    #         'roll_no': safe_value(card_entry.reg_id.roll_no if card_entry.reg_id else ''),
    #         'father_name': safe_value(title_case(card_entry.reg_id.father_name) if card_entry.reg_id else ''),
    #         'mother_name': safe_value(title_case(card_entry.reg_id.mother_name) if card_entry.reg_id else ''),
    #         'class_name': safe_value(card_entry.class_id.class_name if card_entry.class_id else ''),
    #         'section_name': safe_value(card_entry.section_id.section_name if card_entry.section_id else ''),
    #         'shift_name': safe_value(card_entry.shift_id.shift_name if card_entry.shift_id else ''),
    #         'merit_position': safe_value(calculated_merit_position),
    #         'total_working_days': safe_value(card_entry.total_working_days),
    #         'total_present_days': safe_value(card_entry.total_present_days),
    #         'is_remarks': safe_value(card_entry.is_remarks),
    #         'date_of_publication': safe_value(card_entry.date_of_publication),
    #         'is_average_gpa': safe_value(card_entry.is_average_gpa),
    #         'average_letter_grade': safe_value(card_entry.average_letter_grade),
    #         'result_status': safe_value(card_entry.result_status),
    #         'total_obtained_marks': safe_value(card_entry.total_obtained_marks),
    #         'subjects': subjects_list,
    #         'mode_names': mode_names_ordered,
    #     }

    #     context = {
    #         "transaction": transaction,
    #         "printed_on": datetime.now().strftime("%d/%m/%Y, %H:%M:%S"),
    #     }

    #     html_string = render_to_string("result_card_entry/print_result_card_half_yearly_report.html", context)
    #     combined_html += f'<div style="page-break-after: always;">{html_string}</div>'

    # # ----------------------------
    # # Remove last page break safely
    # # ----------------------------
    # combined_html = re.sub(r'<div style="page-break-after: always;">\s*$','', combined_html)

    # pdf = HTML(string=combined_html, base_url=request.build_absolute_uri('/')).write_pdf()

    # response = HttpResponse(pdf, content_type='application/pdf')
    # response['Content-Disposition'] = 'inline; filename="Academic_Transcript_Report.pdf"'
    # return response
    
# ============================================================================
# annual report view starts here
# ============================================================================
# annual result entry UI
@login_required()
def getannualResultsEntryUIManagerAPI(request):
    org_id = request.GET.get('org_id')
    branch_id = request.GET.get('branch_id')
    reg_id = request.GET.get('reg_id')
    is_year = request.GET.get('is_year')

    org_list = get_object_or_404(organizationlst, org_id=org_id)
    branch_list = get_object_or_404(branchslist, branch_id=branch_id)
    registration = get_object_or_404(in_registrations, reg_id=reg_id)

    def title_case(value):
        if value:
            return ' '.join(word.capitalize() for word in value.split())
        return ''

    registration_data = {
        'reg_id': registration.reg_id,
        'class_id': registration.class_id.class_id if registration.class_id else '',
        'section_id': registration.section_id.section_id if registration.section_id else '',
        'shift_id': registration.shift_id.shift_id if registration.shift_id else '',
        'groups_id': registration.groups_id.groups_id if registration.groups_id else '',
        'full_name': title_case(registration.full_name),
        'father_name': title_case(registration.father_name),
        'mother_name': title_case(registration.mother_name),
        'class_name': registration.class_id.class_name if registration.class_id else '',
        'section_name': registration.section_id.section_name if registration.section_id else '',
        'shift_name': registration.shift_id.shift_name if registration.shift_id else '',
        'roll_no': registration.roll_no or '',
        'is_english': registration.is_english,
        'is_bangla': registration.is_bangla,
    }

    context = {
        'org_list': org_list,
        'branch_list': branch_list,
        'registration': registration_data,
        'is_year': is_year,
    }

    return render(request, 'result_card_entry/annual_result_card/result_card_is_annual.html', context)


@login_required()
def getisAnnualDetailsResultAPI(request):
    if request.method != 'GET':
        return JsonResponse({"success": False, "message": "Invalid request"})
    # -------------------------
    # GET params
    # -------------------------
    org_id = request.GET.get("org_id")
    branch_id = request.GET.get("branch_id")
    reg_id = request.GET.get("reg_id")
    class_id = request.GET.get("class_id")
    shifts_id = request.GET.get("shift_id")
    groups_id = request.GET.get("groups_id")
    groups_id = int(groups_id) if groups_id and groups_id != "null" else None
    year = request.GET.get("is_year")
    version = request.GET.get("is_version") # "english" / "bangla"
    # registration object (used earlier)
    registration = get_object_or_404(in_registrations, reg_id=reg_id)
    # version flags
    is_english = False
    is_bangla = False
    if version == "english":
        is_english = True
    elif version == "bangla":
        is_bangla = True
    # -------------------------
    # Subjects (same ordering logic you had)
    # -------------------------
    base_filter = {
        "class_id": registration.class_id,
        "groups_id": registration.groups_id,
        "org_id": registration.org_id,
        "is_active": True
    }
    if is_english:
        base_filter["is_english"] = True
    if is_bangla:
        base_filter["is_bangla"] = True
    subjects_qs = (
        in_subjects.objects
        .filter(**base_filter)
        .annotate(
            is_numeric=Case(
                When(subjects_no__regex=r'^\d+$', then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            ),
            subjects_as_int=Case(
                When(subjects_no__regex=r'^\d+$', then=Cast('subjects_no', IntegerField())),
                default=Value(999999999),
                output_field=IntegerField(),
            )
        )
        .order_by('-is_numeric', 'subjects_as_int', 'subjects_no')
    )
    # build subjects_list skeleton (keeps compatibility with your frontend)
    subjects_list = []
    for s in subjects_qs:
        subjects_list.append({
            "id": s.subjects_id,
            "name": s.subjects_name,
            "full_marks": s.is_marks,
            "pass_marks": s.is_pass_marks or 0,
            "is_applicable_pass_marks": s.is_applicable_pass_marks,
            "modes_half": {}, # per-mode data for half exam
            "modes_annual": {}, # per-mode data for annual exam
            "is_optional": s.is_optional and s.subjects_id == registration.is_optional_sub_id,
            "is_not_countable": s.is_not_countable,
            "letter_grade": "",
            "gp": "-"
        })
    # -------------------------
    # load percentage policy
    # -------------------------
    policy = annual_exam_percentance_policy.objects.filter(
        org_id_id=org_id,
        class_id_id=class_id
    ).first()
    half_percent = int(policy.half_yearly_per) if policy and policy.half_yearly_per else 0
    annual_percent = int(policy.annual_per) if policy and policy.annual_per else 0
    # -------------------------
    # load half and annual result rows separately
    # -------------------------
    half_qs = in_result_finalizationdtls.objects.filter(
        org_id_id=org_id,
        branch_id_id=branch_id,
        reg_id_id=reg_id,
        class_id_id=class_id,
        shifts_id_id=shifts_id,
        groups_id_id=groups_id,
        finalize_year=year,
        is_half_yearly=True,
        is_approved=True
    ).select_related("subject_id", "def_mode_id")
    annual_qs = in_result_finalizationdtls.objects.filter(
        org_id_id=org_id,
        branch_id_id=branch_id,
        reg_id_id=reg_id,
        class_id_id=class_id,
        shifts_id_id=shifts_id,
        groups_id_id=groups_id,
        finalize_year=year,
        is_yearly=True,
        is_approved=True
    ).select_related("subject_id", "def_mode_id")
    # -------------------------
    # build mode maps: subject_id -> mode_name -> dict(actual, pass, default, def_mode_id)
    # -------------------------
    half_map = {}
    annual_map = {}
    mode_names_set = set()
   
    exam_type_name = None
    if annual_qs.exists():
        exam_type_name = annual_qs.first().exam_type_id.exam_type_name
    for r in half_qs:
        sid = r.subject_id.subjects_id
        mode = r.is_mode_name or ""
        mode_names_set.add(mode)
        half_map.setdefault(sid, {})
        half_map[sid].setdefault(mode, {"actual": 0.0, "pass": 0.0, "default": 0.0, "def_mode_id": None})
        half_map[sid][mode]["actual"] += float(r.is_actual_marks or 0.0)
        half_map[sid][mode]["pass"] = float(r.is_pass_marks or 0.0)
        half_map[sid][mode]["default"] = float(r.is_default_marks or 0.0)
        half_map[sid][mode]["def_mode_id"] = getattr(r.def_mode_id, "def_mode_id", None)
    for r in annual_qs:
        sid = r.subject_id.subjects_id
        mode = r.is_mode_name or ""
        mode_names_set.add(mode)
        annual_map.setdefault(sid, {})
        annual_map[sid].setdefault(mode, {"actual": 0.0, "pass": 0.0, "default": 0.0, "def_mode_id": None})
        annual_map[sid][mode]["actual"] += float(r.is_actual_marks or 0.0)
        annual_map[sid][mode]["pass"] = float(r.is_pass_marks or 0.0)
        annual_map[sid][mode]["default"] = float(r.is_default_marks or 0.0)
        annual_map[sid][mode]["def_mode_id"] = getattr(r.def_mode_id, "def_mode_id", None)
    # order mode names by the existing defaults_exam_modes order if possible
    ordered_modes_qs = defaults_exam_modes.objects.filter(is_active=True, is_mode_name__in=list(mode_names_set)).order_by("order_by")
    mode_names_ordered = [m.is_mode_name for m in ordered_modes_qs] if ordered_modes_qs.exists() else sorted(list(mode_names_set))
    # -------------------------
    # Calculation per-subject
    # For each subject:
    # - For each mode: compute weighted_half_mode, weighted_annual_mode
    # - mode_total = weighted_half_mode + weighted_annual_mode
    # - total_subject = sum(mode_total for all modes)
    # - determine letter & gp by full_marks (100/50) using in_letter_gradeHundredMap / FiftyMap
    # - keep old fail/optional logic (adapted)
    # -------------------------
    final_subjects = []
    total_obtained_all_subjects = 0.0
    for sub in subjects_list:
        sid = sub["id"]
        full_marks = float(sub["full_marks"] or 0)
        pass_marks = float(sub["pass_marks"] or 0)
        is_optional = sub["is_optional"]
        is_not_countable = sub["is_not_countable"]
        is_applicable_pass_marks = sub["is_applicable_pass_marks"]
        # per mode results
        per_mode_entries = {}
        subject_half_total = 0.0
        subject_annual_total = 0.0
        # set of all mode names for this subject (union of half and annual modes)
        subject_modes = set()
        subject_modes.update(half_map.get(sid, {}).keys())
        subject_modes.update(annual_map.get(sid, {}).keys())
        # keep mode order
        subject_modes_ordered = [m for m in mode_names_ordered if m in subject_modes] + [m for m in subject_modes if m not in mode_names_ordered]
        # Build per-mode weighted marks
        total_subject_weighted = Decimal('0.00')
        for mode in subject_modes_ordered:
            half_mode = half_map.get(sid, {}).get(mode, {"actual": 0.0, "pass": 0.0, "default": 0.0, "def_mode_id": None})
            annual_mode = annual_map.get(sid, {}).get(mode, {"actual": 0.0, "pass": 0.0, "default": 0.0, "def_mode_id": None})
            half_actual = float(half_mode["actual"] or 0.0)
            annual_actual = float(annual_mode["actual"] or 0.0)
            subject_half_total += half_actual
            subject_annual_total += annual_actual
            # weighted contributions
            weighted_half = (Decimal(str(half_actual)) * Decimal(str(half_percent))) / Decimal(100) if half_percent else Decimal('0.00')
            weighted_annual = (Decimal(str(annual_actual)) * Decimal(str(annual_percent))) / Decimal(100) if annual_percent else Decimal('0.00')
            mode_total_weighted = (weighted_half + weighted_annual).quantize(Decimal('0.01'))
            per_mode_entries[mode] = {
                "def_mode_id": half_mode.get("def_mode_id") or annual_mode.get("def_mode_id"),
                "half_actual": round(half_actual, 2),
                "annual_actual": round(annual_actual, 2),
                f"{half_percent}% of Half Yearly Exam": float(weighted_half),
                f"{annual_percent}% of Annual Exam": float(weighted_annual),
                "Total mode_names Marks": float(mode_total_weighted)
            }
            total_subject_weighted += mode_total_weighted
        # total subject weighted marks as float
        total_subject_marks = float(total_subject_weighted.quantize(Decimal('0.01')))
        # If subject marked not countable, keep '-' for gp / grade
        if is_not_countable:
            letter_grade = "-"
            gp_display = 0.0 # <- must be numeric
        else:
            # Floor the marks for grade lookup to handle float mismatches with integer-ish ranges
            lookup_marks = total_subject_weighted // Decimal('1')
            # Determine grade using hundred/fifty mapping based on full_marks
            filter_kwargs = {
                "org_id_id": org_id,
                "class_id_id": registration.class_id,
                "from_marks__lte": float(lookup_marks),
                "to_marks__gte": float(lookup_marks),
                "is_active": True
            }
            if is_english:
                filter_kwargs["is_english"] = True
            if is_bangla:
                filter_kwargs["is_bangla"] = True
            grade_obj = None
            if full_marks == 100:
                grade_obj = in_letter_gradeHundredMap.objects.filter(**filter_kwargs).first()
            elif full_marks == 50:
                grade_obj = in_letter_gradeFiftyMap.objects.filter(**filter_kwargs).first()
            else:
                # fallback: prefer hundred_map if exists
                grade_obj = in_letter_gradeHundredMap.objects.filter(**filter_kwargs).first() or in_letter_gradeFiftyMap.objects.filter(**filter_kwargs).first()
            if grade_obj:
                # your grade models use related field grade_id -> letter/gp in earlier code
                # adapt to actual model fields:
                # in your earlier code you used grade_qs.grade_id.is_grade_name and grade_qs.grade_point
                # Here attempt both attributes (safe)
                try:
                    letter_grade = grade_obj.grade_id.is_grade_name
                except Exception:
                    # fallback attribute names
                    letter_grade = getattr(grade_obj, "letter_grade", "F")
                # gp might be stored as grade_point or gp_display etc.
                gp_display = float(getattr(grade_obj, "grade_point", getattr(grade_obj, "gp", 0.0) or 0.0))
            else:
                # if no grade found, assume fail (but with floor fix, should rarely happen)
                letter_grade = "F"
                gp_display = 0.0
        # build final subject entry
        subject_entry = {
            "id": sid,
            "name": sub["name"],
            "full_marks": full_marks,
            "pass_marks": pass_marks,
            "is_optional": is_optional,
            "is_not_countable": is_not_countable,
            "modes_ordered": subject_modes_ordered,
            "modes": per_mode_entries,
            "Total mode_names Marks": total_subject_marks,
            "letter_grade": letter_grade,
            "gp": float(gp_display)
        }
        final_subjects.append(subject_entry)
        # only sum subjects which are countable (your earlier logic sums all subject totals into total_marks regardless; keep same)
        total_obtained_all_subjects += total_subject_marks
    # -------------------------
    # Extra Calculation Part: GPA, average letter mapping, remarks
    # Keep your original logic: optional handling and fail_flag across all subjects
    # -------------------------
    total_marks = total_obtained_all_subjects
    count_subjects = 0
    total_gp = 0.0
    overall_fail_flag = False
    optional_bonus = 0.0
    for s in final_subjects:
        if s["is_not_countable"]:
            continue
        if not s["is_optional"]:
            count_subjects += 1
            if isinstance(s["gp"], (int, float)):
                total_gp += s["gp"]
            if s["gp"] == 0.00:
                overall_fail_flag = True
        else:
            # optional subject handling: bonus = gp - 2.00 positive part
            if isinstance(s["gp"], (int, float)):
                bonus = s["gp"] - 2.00
                if bonus > 0:
                    optional_bonus += bonus
            # check subject optional fail mapping from subjects_qs (is_optional_wise_grade_cal)
            subj_obj = next((x for x in subjects_qs if x.subjects_id == s["id"]), None)
            if subj_obj and not subj_obj.is_optional_wise_grade_cal and s["letter_grade"] == "F":
                overall_fail_flag = True
    if count_subjects > 0:
        adjusted_gp = total_gp + optional_bonus
        average_gpa = adjusted_gp / count_subjects
    else:
        average_gpa = 0.00
    if overall_fail_flag:
        average_gpa = 0.00
    if average_gpa > 5.00:
        average_gpa = 5.00
    # Average letter grade mapping (same thresholds you used)
    if average_gpa == 0.00:
        average_letter_grade = "F"
    elif average_gpa >= 5.00:
        average_letter_grade = "A+"
    elif average_gpa >= 4.00:
        average_letter_grade = "A"
    elif average_gpa >= 3.50:
        average_letter_grade = "A-"
    elif average_gpa >= 3.00:
        average_letter_grade = "B"
    elif average_gpa >= 2.00:
        average_letter_grade = "C"
    elif average_gpa >= 1.00:
        average_letter_grade = "D"
    else:
        average_letter_grade = "F"
    remarks_map = {
        "A+": "Outstanding Achievement!",
        "A": "Impressive Performance!",
        "A-": "Commendable Performance!",
        "B": "Encouraging Performance!",
        "C": "An Average Performance!",
        "D": "Needs Significant Improvement!",
        "F": "Unsatisfactory Performance!"
    }
    remarks_status = remarks_map.get(average_letter_grade, "")
    result_status = "Failed" if average_gpa == 0.00 and average_letter_grade == "F" else "Passed"
    # -------------------------
    # Prepare response
    # -------------------------
    response = {
        "success": True,
        "half_percent": half_percent,
        "annual_percent": annual_percent,
        "mode_names": mode_names_ordered,
        "half_yearly_exam": [
            {
                "subject_id": sid,
                "modes": half_map.get(sid, {}),
                "subject_total_half": sum([v["actual"] for v in half_map.get(sid, {}).values()]) if half_map.get(sid) else 0.0
            } for sid in sorted(list(half_map.keys()))
        ],
        "annual_exam": [
            {
                "subject_id": sid,
                "modes": annual_map.get(sid, {}),
                "subject_total_annual": sum([v["actual"] for v in annual_map.get(sid, {}).values()]) if annual_map.get(sid) else 0.0
            } for sid in sorted(list(annual_map.keys()))
        ],
        "final_subjects": final_subjects,
        "total_obtained_marks": round(total_marks, 2),
        "average_gpa": round(average_gpa, 2),
        "average_letter_grade": average_letter_grade,
        "remarks_status": remarks_status,
        "result_status": result_status,
        "exam_type_name": exam_type_name,
    }
    return JsonResponse(response)

@login_required()
def getStudentAttendanceAnnualExaminationAPI(request):
    if request.method == "GET":
        # -----------------------
        # Get params safely
        # -----------------------
        org_id = safe_int(request.GET.get('org_id'))
        branch_id = safe_int(request.GET.get('branch_id'))
        reg_id = safe_int(request.GET.get('reg_id'))
        class_id = safe_int(request.GET.get('class_id'))
        shift_id = safe_int(request.GET.get('shift_id'))
        groups_id = safe_int(request.GET.get('groups_id'))
        year = request.GET.get("is_year")
        version = request.GET.get("is_version")  # "english" / "bangla"
        is_yearly = request.GET.get('is_yearly') == 'true'

        # -----------------------
        # Version flags
        # -----------------------
        is_english = version == "english"
        is_bangla = version == "bangla"

        # -----------------------
        # Base filter
        # -----------------------
        current_year = int(year)
        base_filter = {'attendant_year': current_year}

        if org_id:
            base_filter['org_id_id'] = org_id
        if branch_id:
            base_filter['branch_id_id'] = branch_id
        if class_id:
            base_filter['class_id_id'] = class_id
        if shift_id:
            base_filter['shifts_id_id'] = shift_id
        if groups_id:
            base_filter['groups_id_id'] = groups_id
        if is_yearly:
            base_filter['is_yearly'] = True
        if is_english:
            base_filter['is_english'] = True
        if is_bangla:
            base_filter['is_bangla'] = True

        # -----------------------
        # Fetch attendance master
        # -----------------------
        try:
            att_master = in_student_attendant.objects.get(**base_filter)
            total_working_days = att_master.working_days or 0

            # Fetch present days
            present_days = in_student_attendantdtls.objects.filter(
                attendant_id=att_master,
                reg_id_id=reg_id,
                # Also apply language filter
                **({'is_english': True} if is_english else {}),
                **({'is_bangla': True} if is_bangla else {})
            ).aggregate(total_present=Sum('attendant_qty'))['total_present'] or 0

        except in_student_attendant.DoesNotExist:
            total_working_days = 0
            present_days = 0

        # -----------------------
        # Return response
        # -----------------------
        return JsonResponse({
            'success': True,
            'total_working_days': total_working_days,
            'total_present_days': present_days
        })

    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required()
def saveAnnualResultsCardEntryManagerAPI(request):
    resp = {'status': 'failed', 'msg': ''}
    data = request.POST
    org_id = data.get('is_org_id')
    branch_id = data.get('is_branch_id')
    reg_id = data.get('is_reg_id')
    roll_no = data.get('roll_no') 
    class_id = data.get('is_class_id')
    section_id = data.get('is_section_id')
    shift_id = data.get('is_shifts_id')
    groups_id = data.get('is_groups_id')
    total_working_days = data.get('total_working_days')
    total_present_days = data.get('total_present_days')
    is_remarks = data.get('is_remarks')
    date_of_publication_raw = data.get('date_of_publication')
    is_average_gpa = data.get('is_average_gpa')
    average_letter_grade = data.get('average_letter_grade')
    result_status = data.get('result_status')
    total_obtained_marks = data.get('total_obtained_marks')
    is_year = data.get('is_year', 0)
    is_english = data.get('is_english_id', 0)
    is_bangla = data.get('is_bangla_id', 0)


    try:
        with transaction.atomic():
            org_instance = organizationlst.objects.get(org_id=org_id)
            branch_instance = branchslist.objects.get(branch_id=branch_id)
            class_instance = in_class.objects.get(class_id=class_id)
            section_instance = in_section.objects.get(section_id=section_id)
            shift_instance = in_shifts.objects.get(shift_id=shift_id)
            if groups_id:
                groups_instance = in_groups.objects.get(groups_id=groups_id)
            else:
                groups_instance = None

            if reg_id:
                reg_instance = in_registrations.objects.get(reg_id=reg_id)
            else:
                reg_instance = None


            # Filter for existing results card entries
            filter_kwargs = Q(create_date=is_year)
            if org_id: filter_kwargs &= Q(org_id=org_id)
            if branch_id: filter_kwargs &= Q(branch_id=branch_id)
            if class_id: filter_kwargs &= Q(class_id=class_id)
            if section_id: filter_kwargs &= Q(section_id=section_id)
            if shift_id: filter_kwargs &= Q(shift_id=shift_id)
            if groups_id: filter_kwargs &= Q(groups_id=groups_id)
            if reg_id: filter_kwargs &= Q(reg_id=reg_id)

            if in_results_card_entry.objects.filter(filter_kwargs, is_half_year=False, is_annual=True).exists():
                return JsonResponse({'success': False, 'msg': 'This Year Results Card Already Created. Please Try Another One.'})

            date_of_publication = None
            if date_of_publication_raw:
                try:
                    # Convert from 'DD-MM-YYYY' to 'YYYY-MM-DD'
                    date_of_publication = datetime.strptime(date_of_publication_raw, '%d-%m-%Y').date()
                except ValueError:
                    resp['msg'] = f"Invalid date format for date_of_publication: {date_of_publication_raw}"
                    return JsonResponse(resp)

            res_card_entry = in_results_card_entry.objects.create(
                date_of_publication=date_of_publication,
                create_date=is_year,
                org_id=org_instance,
                branch_id=branch_instance,
                reg_id=reg_instance,
                roll_no=roll_no,
                class_id=class_instance,
                section_id=section_instance,
                shift_id=shift_instance,
                groups_id=groups_instance,
                is_half_year=False,
                is_annual=True,
                is_average_gpa=is_average_gpa,
                average_letter_grade=average_letter_grade,
                result_status=result_status,
                total_obtained_marks=float(total_obtained_marks),
                total_working_days=total_working_days,
                total_present_days=total_present_days,
                is_remarks=is_remarks,
                is_english=is_english,
                is_bangla=is_bangla,
                is_approved=True,
                is_approved_by=request.user,
                approved_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                ss_creator=request.user,
                ss_modifier=request.user
            )

            res_card_id = res_card_entry.res_card_id

            resp['status'] = 'success'
            resp['res_card_id'] = res_card_id
    except Exception as e:
        resp['msg'] = str(e)

    return JsonResponse(resp)


@login_required()
def annualResultsCardEntryViewerManagerAPI(request):
    res_card_id = request.GET.get('id')
    org_id = request.GET.get("org_id")
    class_id = request.GET.get("class_id")

    org_id = int(org_id) if org_id and org_id != "null" else None
    class_id = int(class_id) if class_id and class_id != "null" else None

    is_english = request.GET.get("is_english") == 'true'
    is_bangla = request.GET.get("is_bangla") == 'true'

    card_entry = get_object_or_404(in_results_card_entry, res_card_id=res_card_id)
    registration = card_entry.reg_id

    # ================================
    # Fifty Marks Map
    # ================================
    fifty_grades = in_letter_gradeFiftyMap.objects.filter(is_active=True)

    if is_english:
        fifty_grades = fifty_grades.filter(is_english=True)

    if is_bangla:
        fifty_grades = fifty_grades.filter(is_bangla=True)

    if org_id:
        fifty_grades = fifty_grades.filter(org_id=org_id)

    if class_id:
        fifty_grades = fifty_grades.filter(class_id=class_id)

    # ================================
    # Hundred Marks Map
    # ================================
    hundred_grades = in_letter_gradeHundredMap.objects.filter(is_active=True)

    if is_english:
        hundred_grades = hundred_grades.filter(is_english=True)

    if is_bangla:
        hundred_grades = hundred_grades.filter(is_bangla=True)

    if org_id:
        hundred_grades = hundred_grades.filter(org_id=org_id)

    if class_id:
        hundred_grades = hundred_grades.filter(class_id=class_id)

    # =================================
    # Collect grade_ids
    # =================================
    fifty_grade_ids = list(fifty_grades.values_list("grade_id", flat=True))
    hundred_grade_ids = list(hundred_grades.values_list("grade_id", flat=True))

    grade_ids = set(fifty_grade_ids + hundred_grade_ids)

    grades = in_letter_grade_mode.objects.filter(
        grade_id__in=grade_ids
    ).order_by("grade_id")

    # ===============================
    # Prepare Table Data
    # ===============================
    table_data = []
    for grade in grades:

        fifty_map = fifty_grades.filter(grade_id=grade).first()
        hundred_map = hundred_grades.filter(grade_id=grade).first()

        table_data.append({
            "grade_name": grade.is_grade_name,
            "fifty_interval": (
                f"{fifty_map.from_marks}-{fifty_map.to_marks}" if fifty_map else ""
            ),
            "hundred_interval": (
                f"{hundred_map.from_marks}-{hundred_map.to_marks}" if hundred_map else ""
            ),
            "grade_point": (
                fifty_map.grade_point if fifty_map else
                (hundred_map.grade_point if hundred_map else "")
            )
        })

    # ===============================
    # Transaction Data
    # ===============================
    def title_case(value):
        return ' '.join(word.capitalize() for word in value.split()) if value else ''

    transaction = {
        'create_date': card_entry.create_date or '',
        'reg_id': registration.reg_id if registration else '',
        'org_name': card_entry.org_id.org_name if card_entry.org_id else '',
        'full_name': title_case(registration.full_name) if registration else '',
        'roll_no': registration.roll_no if registration else '',
        'father_name': title_case(registration.father_name) if registration else '',
        'mother_name': title_case(registration.mother_name) if registration else '',
        'class_name': card_entry.class_id.class_name if card_entry.class_id else '',
        'section_name': card_entry.section_id.section_name if card_entry.section_id else '',
        'shift_name': card_entry.shift_id.shift_name if card_entry.shift_id else '',
        'total_working_days': card_entry.total_working_days or '',
        'total_present_days': card_entry.total_present_days or '',
        'is_remarks': card_entry.is_remarks or '',
        'date_of_publication': card_entry.date_of_publication or '',
        'is_average_gpa': card_entry.is_average_gpa or '',
        'average_letter_grade': card_entry.average_letter_grade or '',
        'total_obtained_marks': card_entry.total_obtained_marks or '',
        'result_status': card_entry.result_status or '',
    }

    context = {
        "transaction": transaction,
        "registration": registration,
        "table_data": table_data,
    }

    return render(request, 'result_card_entry/annual_result_card/result_card_annual_viewer.html', context)


@login_required()
def individualReportAnnualResultsCardAPI(request):
    res_card_id = request.GET.get('id')
    org_id = request.GET.get("org_id")
    branch_id = request.GET.get("branch_id")
    class_id = request.GET.get("is_class")
    groups_id = request.GET.get("is_groups")
    section_id = request.GET.get("is_section")
    shift_id = request.GET.get("is_shift")
    create_year = request.GET.get("create_year")
    
    org_id = int(org_id) if org_id and org_id != "null" else None
    branch_id = int(branch_id) if branch_id and branch_id != "null" else None
    class_id = int(class_id) if class_id and class_id != "null" else None
    groups_id = int(groups_id) if groups_id and groups_id != "null" else None
    section_id = int(section_id) if section_id and section_id != "null" else None
    shift_id = int(shift_id) if shift_id and shift_id != "null" else None
    create_year = int(create_year) if create_year and create_year != "null" else None

    is_english = request.GET.get("is_english") == 'true'
    is_bangla = request.GET.get("is_bangla") == 'true'

    card_entry = get_object_or_404(in_results_card_entry, res_card_id=res_card_id)
    registration = card_entry.reg_id


    # ======================================
    # 🔍 GET MERIT POSITION
    # ======================================

    merit_position = ""

    try:
        # Base query
        merit_approval = in_merit_position_approval.objects.filter(
            org_id=org_id,
            branch_id=branch_id,
            class_id=class_id,
            shifts_id=shift_id,
            is_yearly=True,
            is_half_yearly=False,
            merit_year=create_year
        )

        if section_id:
            merit_approval = merit_approval.filter(section_id=section_id)

        if groups_id:
            merit_approval = merit_approval.filter(groups_id=groups_id)

        merit_approval = merit_approval.first()

        merit_position = ""
        if merit_approval:
            merit_dtls = in_merit_position_approvaldtls.objects.filter(
                merit_id=merit_approval,
                reg_id=registration
            ).first()
            if merit_dtls:
                merit_position = merit_dtls.merit_position

    except Exception as e:
        print("Merit Error:", e)
        merit_position = ""

    # ================================
    # Fifty Marks Map
    # ================================
    fifty_grades = in_letter_gradeFiftyMap.objects.filter(is_active=True)

    if is_english:
        fifty_grades = fifty_grades.filter(is_english=True)

    if is_bangla:
        fifty_grades = fifty_grades.filter(is_bangla=True)

    if org_id:
        fifty_grades = fifty_grades.filter(org_id=org_id)

    if class_id:
        fifty_grades = fifty_grades.filter(class_id=class_id)

    # ================================
    # Hundred Marks Map
    # ================================
    hundred_grades = in_letter_gradeHundredMap.objects.filter(is_active=True)

    if is_english:
        hundred_grades = hundred_grades.filter(is_english=True)

    if is_bangla:
        hundred_grades = hundred_grades.filter(is_bangla=True)

    if org_id:
        hundred_grades = hundred_grades.filter(org_id=org_id)

    if class_id:
        hundred_grades = hundred_grades.filter(class_id=class_id)

    # =================================
    # Collect grade_ids
    # =================================
    fifty_grade_ids = list(fifty_grades.values_list("grade_id", flat=True))
    hundred_grade_ids = list(hundred_grades.values_list("grade_id", flat=True))

    grade_ids = set(fifty_grade_ids + hundred_grade_ids)

    grades = in_letter_grade_mode.objects.filter(
        grade_id__in=grade_ids
    ).order_by("grade_id")

    # ===============================
    # Prepare Table Data
    # ===============================
    table_data = []
    for grade in grades:

        fifty_map = fifty_grades.filter(grade_id=grade).first()
        hundred_map = hundred_grades.filter(grade_id=grade).first()

        table_data.append({
            "grade_name": grade.is_grade_name,
            "fifty_interval": (
                f"{fifty_map.from_marks}-{fifty_map.to_marks}" if fifty_map else ""
            ),
            "hundred_interval": (
                f"{hundred_map.from_marks}-{hundred_map.to_marks}" if hundred_map else ""
            ),
            "grade_point": (
                fifty_map.grade_point if fifty_map else
                (hundred_map.grade_point if hundred_map else "")
            )
        })

    # ===============================
    # Transaction Data
    # ===============================
    def title_case(value):
        return ' '.join(word.capitalize() for word in value.split()) if value else ''

    transaction = {
        'create_date': card_entry.create_date or '',
        'reg_id': registration.reg_id if registration else '',
        'org_name': card_entry.org_id.org_name if card_entry.org_id else '',
        'full_name': title_case(registration.full_name) if registration else '',
        'roll_no': registration.roll_no if registration else '',
        'father_name': title_case(registration.father_name) if registration else '',
        'mother_name': title_case(registration.mother_name) if registration else '',
        'class_name': card_entry.class_id.class_name if card_entry.class_id else '',
        'section_name': card_entry.section_id.section_name if card_entry.section_id else '',
        'shift_name': card_entry.shift_id.shift_name if card_entry.shift_id else '',
        'groups_name': card_entry.groups_id.groups_name if card_entry.groups_id else '',
        'total_working_days': card_entry.total_working_days or '',
        'total_present_days': card_entry.total_present_days or '',
        'is_remarks': card_entry.is_remarks or '',
        'date_of_publication': card_entry.date_of_publication or '',
        'is_average_gpa': card_entry.is_average_gpa or '',
        'average_letter_grade': card_entry.average_letter_grade or '',
        'total_obtained_marks': card_entry.total_obtained_marks or '',
        'result_status': card_entry.result_status or '',
        'merit_position': merit_position,
        'exam_type_name': 'Annual',
    }

    context = {
        "transaction": transaction,
        "registration": registration,
        "table_data": table_data,
    }

    return render(request, 'result_card_entry/annual_result_card/individual_report/individual_annual_report.html', context)


@login_required()
def rollbackResultsCardManagerAPI(request):
    card_data = {}
    if request.method == 'GET':
        data = request.GET
        res_card_id = ''
        if 'res_card_id' in data:
            res_card_id = data['res_card_id']
        if res_card_id.isnumeric() and int(res_card_id) > 0:
            card_data = in_results_card_entry.objects.filter(res_card_id=res_card_id).first()

    context = {
        'card_data': card_data,
    }
    return render(request, 'result_card_history/rollback_results_card.html', context)


@login_required()
def rollbackResultsCardSubmissionAPI(request):
    resp = {"success": False, "errmsg": "Failed"}

    if request.method != "POST":
        resp["errmsg"] = "Invalid request method"
        return JsonResponse(resp)

    res_card_id = request.POST.get("res_card_id")

    if not res_card_id:
        resp["errmsg"] = "Result card ID is missing"
        return JsonResponse(resp)

    try:
        with transaction.atomic():

            # ---- Fetch card safely ----
            try:
                card_data = in_results_card_entry.objects.get(res_card_id=res_card_id)
            except in_results_card_entry.DoesNotExist:
                resp["errmsg"] = "Result card record not found"
                return JsonResponse(resp)

            # ---- Check Year ----
            current_year = datetime.now().year
            if card_data.create_date != current_year:
                resp["errmsg"] = (
                    f"Rollback failed! Result card creation year ({card_data.create_date}) "
                    f"does not match current year ({current_year})."
                )
                return JsonResponse(resp)

            # ---- Delete ----
            card_data.delete()

            resp["success"] = True
            resp["msg"] = "Result card rollback completed successfully"

    except Exception as e:
        resp["errmsg"] = f"Unexpected error: {str(e)}"

    return JsonResponse(resp)

# @csrf_exempt
# @login_required()
# def annualResultsCardReportsManagerAPI(request):
#     if request.method != 'POST':
#         return HttpResponse("Invalid request")

#     import json
#     from django.template.loader import render_to_string

#     print_blocks = request.POST.get("print_blocks")

#     try:
#         blocks = json.loads(print_blocks)
#     except:
#         return HttpResponse("Invalid JSON")

#     rendered_pages = []

#     for block in blocks:

#         org_id      = block.get("org_id")
#         branch_id   = block.get("branch_id")
#         class_id    = block.get("class_id")
#         shift_id    = block.get("shift_id")
#         groups_id   = block.get("groups_id")
#         is_year     = block.get("is_year")
#         is_version  = block.get("is_version")
#         merit_id    = block.get("merit_id")
#         reg_ids     = block.get("reg_ids", [])
#         section_ids = block.get("section_ids", [])

#         # version detect
#         is_english = True if is_version == "english" else False
#         is_bangla  = True if is_version == "bangla" else False

#         # ================================
#         # Fetch all merit positions for given merit_id at once
#         # ================================
#         merit_qs = in_merit_position_approvaldtls.objects.filter(
#             merit_id=merit_id,
#             reg_id__in=reg_ids
#         ).values("reg_id", "merit_position")

#         merit_dict = {item["reg_id"]: item["merit_position"] for item in merit_qs}

#         # Sort reg_ids by merit_position ascending
#         reg_ids_sorted = sorted(
#             reg_ids, key=lambda rid: merit_dict.get(rid, float('inf'))
#         )

#         for reg_id in reg_ids_sorted:

#             merit_position = merit_dict.get(reg_id, 0)

#             # ================================
#             # FILTER RESULT CARD ENTRY
#             # ================================
#             card_entry = in_results_card_entry.objects.filter(
#                 reg_id=reg_id,
#                 org_id=org_id,
#                 branch_id=branch_id,
#                 class_id=class_id,
#                 shift_id=shift_id,
#                 groups_id=groups_id,
#                 is_annual=True if is_year else False,
#             ).first()

#             if not card_entry:
#                 return HttpResponse(
#                     f"No result card found for RegID={reg_id}",
#                 )

#             registration = card_entry.reg_id

#             # =================================
#             # Collect Grade Maps
#             # =================================
#             fifty_grades = in_letter_gradeFiftyMap.objects.filter(is_active=True, org_id=org_id, class_id=class_id)
#             hundred_grades = in_letter_gradeHundredMap.objects.filter(is_active=True, org_id=org_id, class_id=class_id)

#             if is_english:
#                 fifty_grades = fifty_grades.filter(is_english=True)
#                 hundred_grades = hundred_grades.filter(is_english=True)
#             if is_bangla:
#                 fifty_grades = fifty_grades.filter(is_bangla=True)
#                 hundred_grades = hundred_grades.filter(is_bangla=True)

#             fifty_grade_ids = list(fifty_grades.values_list("grade_id", flat=True))
#             hundred_grade_ids = list(hundred_grades.values_list("grade_id", flat=True))
#             grade_ids = set(fifty_grade_ids + hundred_grade_ids)

#             grades = in_letter_grade_mode.objects.filter(
#                 grade_id__in=grade_ids
#             ).order_by("grade_id")

#             # ===============================
#             # Table Data Prepare
#             # ===============================
#             table_data = []
#             for grade in grades:
#                 fifty_map = fifty_grades.filter(grade_id=grade).first()
#                 hundred_map = hundred_grades.filter(grade_id=grade).first()
#                 table_data.append({
#                     "grade_name": grade.is_grade_name,
#                     "fifty_interval": f"{fifty_map.from_marks}-{fifty_map.to_marks}" if fifty_map else "",
#                     "hundred_interval": f"{hundred_map.from_marks}-{hundred_map.to_marks}" if hundred_map else "",
#                     "grade_point": fifty_map.grade_point if fifty_map else (hundred_map.grade_point if hundred_map else "")
#                 })

#             # ===============================
#             # Transaction Data
#             # ===============================
#             def title_case(value):
#                 return ' '.join(word.capitalize() for word in value.split()) if value else ''

#             transaction = {
#                 'create_date': card_entry.create_date or '',
#                 'reg_id': registration.reg_id if registration else '',
#                 'org_name': card_entry.org_id.org_name if card_entry.org_id else '',
#                 'full_name': title_case(registration.full_name),
#                 'roll_no': registration.roll_no or '',
#                 'father_name': title_case(registration.father_name),
#                 'mother_name': title_case(registration.mother_name),
#                 'class_name': card_entry.class_id.class_name if card_entry.class_id else '',
#                 'section_name': card_entry.section_id.section_name if card_entry.section_id else '',
#                 'shift_name': card_entry.shift_id.shift_name if card_entry.shift_id else '',
#                 'total_working_days': card_entry.total_working_days or '',
#                 'total_present_days': card_entry.total_present_days or '',
#                 'is_remarks': card_entry.is_remarks or '',
#                 'date_of_publication': card_entry.date_of_publication or '',
#                 'is_average_gpa': card_entry.is_average_gpa or '',
#                 'average_letter_grade': card_entry.average_letter_grade or '',
#                 'total_obtained_marks': card_entry.total_obtained_marks or '',
#                 'result_status': card_entry.result_status or '',
#                 'merit_position': merit_position,
#                 'is_year': is_year,
#                 'merit_id': merit_id,
#             }

#             html = render_to_string(
#                 'result_card_entry/annual_result_card/annual_card_report/annual_report_card_report.html',
#                 {
#                     "transaction": transaction,
#                     "registration": registration,
#                     "table_data": table_data,
#                 }
#             )

#             rendered_pages.append(html)

#     return HttpResponse("".join(rendered_pages))

@csrf_exempt
@login_required()
def annualResultsCardReportsManagerAPI(request):
    if request.method != 'POST':
        return HttpResponse("Invalid request")

    import json
    from django.template.loader import render_to_string
    from django.db.models import Case, When, Value, IntegerField
    from django.db.models.functions import Cast

    print_blocks = request.POST.get("print_blocks")

    try:
        blocks = json.loads(print_blocks)
    except:
        return HttpResponse("Invalid JSON")

    rendered_pages = []

    for block in blocks:

        org_id      = block.get("org_id")
        branch_id   = block.get("branch_id")
        class_id    = block.get("class_id")
        shift_id    = block.get("shift_id")
        groups_id   = block.get("groups_id")
        is_year     = block.get("is_year")
        is_version  = block.get("is_version")
        merit_id    = block.get("merit_id")
        reg_ids     = block.get("reg_ids", [])
        section_ids = block.get("section_ids", [])

        # version detect
        is_english = True if is_version == "english" else False
        is_bangla  = True if is_version == "bangla" else False
        
        final_response = {}

        # ================================
        # Fetch all merit positions for given merit_id at once
        # ================================
        merit_qs = in_merit_position_approvaldtls.objects.filter(
            merit_id=merit_id,
            reg_id__in=reg_ids
        ).values("reg_id", "merit_position")

        merit_dict = {item["reg_id"]: item["merit_position"] or 0 for item in merit_qs}

        # Sort reg_ids by merit_position ascending
        reg_ids_sorted = sorted(
            reg_ids, key=lambda rid: merit_dict.get(rid, float('inf'))
        )

        for reg_id in reg_ids_sorted:

            merit_position = merit_dict.get(reg_id, 0)

            # ================================
            # FILTER RESULT CARD ENTRY
            # ================================
            card_entry = in_results_card_entry.objects.filter(
                reg_id=reg_id,
                org_id=org_id,
                branch_id=branch_id,
                class_id=class_id,
                shift_id=shift_id,
                groups_id=groups_id,
                is_annual=True,
            ).first()

            if not card_entry:
                continue  # skip if no card

            registration = card_entry.reg_id

            # =================================
            # Collect Grade Maps (একবারই লোড)
            # =================================
            fifty_grades = in_letter_gradeFiftyMap.objects.filter(is_active=True, org_id=org_id, class_id=class_id)
            hundred_grades = in_letter_gradeHundredMap.objects.filter(is_active=True, org_id=org_id, class_id=class_id)

            if is_english:
                fifty_grades = fifty_grades.filter(is_english=True)
                hundred_grades = hundred_grades.filter(is_english=True)
            if is_bangla:
                fifty_grades = fifty_grades.filter(is_bangla=True)
                hundred_grades = hundred_grades.filter(is_bangla=True)

            # ===============================
            # Table Data Prepare (grading scale table)
            # ===============================
            table_data = []
            all_grade_ids = set(
                list(fifty_grades.values_list("grade_id", flat=True)) + 
                list(hundred_grades.values_list("grade_id", flat=True))
            )
            grades = in_letter_grade_mode.objects.filter(grade_id__in=all_grade_ids).order_by("grade_id")

            for grade in grades:
                fifty_map = fifty_grades.filter(grade_id=grade).first()
                hundred_map = hundred_grades.filter(grade_id=grade).first()
                table_data.append({
                    "grade_name": grade.is_grade_name or "",
                    "fifty_interval": f"{fifty_map.from_marks}-{fifty_map.to_marks}" if fifty_map else "",
                    "hundred_interval": f"{hundred_map.from_marks}-{hundred_map.to_marks}" if hundred_map else "",
                    "grade_point": fifty_map.grade_point if fifty_map else (hundred_map.grade_point if hundred_map else "")
                })

            # -------------------------
            # Subjects ordering
            # -------------------------
            base_filter = {
                "class_id": registration.class_id,
                "groups_id": registration.groups_id,
                "org_id": registration.org_id,
                "is_active": True
            }
            if is_english:
                base_filter["is_english"] = True
            if is_bangla:
                base_filter["is_bangla"] = True
            subjects_qs = (
                in_subjects.objects
                .filter(**base_filter)
                .annotate(
                    is_numeric=Case(
                        When(subjects_no__regex=r'^\d+$', then=Value(1)),
                        default=Value(0),
                        output_field=IntegerField(),
                    ),
                    subjects_as_int=Case(
                        When(subjects_no__regex=r'^\d+$', then=Cast('subjects_no', IntegerField())),
                        default=Value(999999999),
                        output_field=IntegerField(),
                    )
                )
                .order_by('-is_numeric', 'subjects_as_int', 'subjects_no')
            )
            # build subjects_list skeleton (keeps compatibility with your frontend)
            subjects_list = []
            for s in subjects_qs:
                subjects_list.append({
                    "id": s.subjects_id,
                    "name": s.subjects_name,
                    "full_marks": s.is_marks,
                    "pass_marks": s.is_pass_marks or 0,
                    "is_applicable_pass_marks": s.is_applicable_pass_marks,
                    "modes_half": {}, # per-mode data for half exam
                    "modes_annual": {}, # per-mode data for annual exam
                    "is_optional": s.is_optional and s.subjects_id == registration.is_optional_sub_id,
                    "is_not_countable": s.is_not_countable,
                    "letter_grade": "",
                    "gp": "-"
                })
            # -------------------------
            # load percentage policy
            # -------------------------
            policy = annual_exam_percentance_policy.objects.filter(
                org_id_id=org_id,
                class_id_id=class_id
            ).first()
            half_percent = int(policy.half_yearly_per) if policy and policy.half_yearly_per else 0
            annual_percent = int(policy.annual_per) if policy and policy.annual_per else 0
            # -------------------------
            # load half and annual result rows separately
            # -------------------------
            half_qs = in_result_finalizationdtls.objects.filter(
                org_id_id=org_id,
                branch_id_id=branch_id,
                reg_id_id=reg_id,
                class_id_id=class_id,
                shifts_id_id=shift_id,
                groups_id_id=groups_id,
                finalize_year=is_year,
                is_half_yearly=True,
                is_approved=True
            ).select_related("subject_id", "def_mode_id")
            annual_qs = in_result_finalizationdtls.objects.filter(
                org_id_id=org_id,
                branch_id_id=branch_id,
                reg_id_id=reg_id,
                class_id_id=class_id,
                shifts_id_id=shift_id,
                groups_id_id=groups_id,
                finalize_year=is_year,
                is_yearly=True,
                is_approved=True
            ).select_related("subject_id", "def_mode_id")
            # -------------------------
            # build mode maps: subject_id -> mode_name -> dict(actual, pass, default, def_mode_id)
            # -------------------------
            half_map = {}
            annual_map = {}
            mode_names_set = set()
        
            exam_type_name = None
            if annual_qs.exists():
                exam_type_name = annual_qs.first().exam_type_id.exam_type_name
            for r in half_qs:
                sid = r.subject_id.subjects_id
                mode = r.is_mode_name or ""
                mode_names_set.add(mode)
                half_map.setdefault(sid, {})
                half_map[sid].setdefault(mode, {"actual": 0.0, "pass": 0.0, "default": 0.0, "def_mode_id": None})
                half_map[sid][mode]["actual"] += float(r.is_actual_marks or 0.0)
                half_map[sid][mode]["pass"] = float(r.is_pass_marks or 0.0)
                half_map[sid][mode]["default"] = float(r.is_default_marks or 0.0)
                half_map[sid][mode]["def_mode_id"] = getattr(r.def_mode_id, "def_mode_id", None)
            for r in annual_qs:
                sid = r.subject_id.subjects_id
                mode = r.is_mode_name or ""
                mode_names_set.add(mode)
                annual_map.setdefault(sid, {})
                annual_map[sid].setdefault(mode, {"actual": 0.0, "pass": 0.0, "default": 0.0, "def_mode_id": None})
                annual_map[sid][mode]["actual"] += float(r.is_actual_marks or 0.0)
                annual_map[sid][mode]["pass"] = float(r.is_pass_marks or 0.0)
                annual_map[sid][mode]["default"] = float(r.is_default_marks or 0.0)
                annual_map[sid][mode]["def_mode_id"] = getattr(r.def_mode_id, "def_mode_id", None)
            # order mode names by the existing defaults_exam_modes order if possible
            ordered_modes_qs = defaults_exam_modes.objects.filter(is_active=True, is_mode_name__in=list(mode_names_set)).order_by("order_by")
            mode_names_ordered = [m.is_mode_name for m in ordered_modes_qs] if ordered_modes_qs.exists() else sorted(list(mode_names_set))
            # -------------------------
            # Calculation per-subject
            # For each subject:
            # - For each mode: compute weighted_half_mode, weighted_annual_mode
            # - mode_total = weighted_half_mode + weighted_annual_mode
            # - total_subject = sum(mode_total for all modes)
            # - determine letter & gp by full_marks (100/50) using in_letter_gradeHundredMap / FiftyMap
            # - keep old fail/optional logic (adapted)
            # -------------------------
            final_subjects = []
            total_obtained_all_subjects = 0.0
            for sub in subjects_list:
                sid = sub["id"]
                full_marks = float(sub["full_marks"] or 0)
                pass_marks = float(sub["pass_marks"] or 0)
                is_optional = sub["is_optional"]
                is_not_countable = sub["is_not_countable"]
                is_applicable_pass_marks = sub["is_applicable_pass_marks"]
                # per mode results
                per_mode_entries = {}
                subject_half_total = 0.0
                subject_annual_total = 0.0
                # set of all mode names for this subject (union of half and annual modes)
                subject_modes = set()
                subject_modes.update(half_map.get(sid, {}).keys())
                subject_modes.update(annual_map.get(sid, {}).keys())
                # keep mode order
                subject_modes_ordered = [m for m in mode_names_ordered if m in subject_modes] + [m for m in subject_modes if m not in mode_names_ordered]
                # Build per-mode weighted marks
                total_subject_weighted = Decimal('0.00')
                for mode in subject_modes_ordered:
                    half_mode = half_map.get(sid, {}).get(mode, {"actual": 0.0, "pass": 0.0, "default": 0.0, "def_mode_id": None})
                    annual_mode = annual_map.get(sid, {}).get(mode, {"actual": 0.0, "pass": 0.0, "default": 0.0, "def_mode_id": None})
                    half_actual = float(half_mode["actual"] or 0.0)
                    annual_actual = float(annual_mode["actual"] or 0.0)
                    subject_half_total += half_actual
                    subject_annual_total += annual_actual
                    # weighted contributions
                    weighted_half = (Decimal(str(half_actual)) * Decimal(str(half_percent))) / Decimal(100) if half_percent else Decimal('0.00')
                    weighted_annual = (Decimal(str(annual_actual)) * Decimal(str(annual_percent))) / Decimal(100) if annual_percent else Decimal('0.00')
                    mode_total_weighted = (weighted_half + weighted_annual).quantize(Decimal('0.01'))
                    per_mode_entries[mode] = {
                        "def_mode_id": half_mode.get("def_mode_id") or annual_mode.get("def_mode_id"),
                        "half_actual": round(half_actual, 2),
                        "annual_actual": round(annual_actual, 2),
                        f"{half_percent}% of Half Yearly Exam": float(weighted_half),
                        f"{annual_percent}% of Annual Exam": float(weighted_annual),
                        "Total mode_names Marks": float(mode_total_weighted)
                    }
                    total_subject_weighted += mode_total_weighted
                # total subject weighted marks as float
                total_subject_marks = float(total_subject_weighted.quantize(Decimal('0.01')))
                # If subject marked not countable, keep '-' for gp / grade
                if is_not_countable:
                    letter_grade = "-"
                    gp_display = 0.0 # <- must be numeric
                else:
                    # Floor the marks for grade lookup to handle float mismatches with integer-ish ranges
                    lookup_marks = total_subject_weighted // Decimal('1')
                    # Determine grade using hundred/fifty mapping based on full_marks
                    filter_kwargs = {
                        "org_id_id": org_id,
                        "class_id_id": registration.class_id,
                        "from_marks__lte": float(lookup_marks),
                        "to_marks__gte": float(lookup_marks),
                        "is_active": True
                    }
                    if is_english:
                        filter_kwargs["is_english"] = True
                    if is_bangla:
                        filter_kwargs["is_bangla"] = True
                    grade_obj = None
                    if full_marks == 100:
                        grade_obj = in_letter_gradeHundredMap.objects.filter(**filter_kwargs).first()
                    elif full_marks == 50:
                        grade_obj = in_letter_gradeFiftyMap.objects.filter(**filter_kwargs).first()
                    else:
                        # fallback: prefer hundred_map if exists
                        grade_obj = in_letter_gradeHundredMap.objects.filter(**filter_kwargs).first() or in_letter_gradeFiftyMap.objects.filter(**filter_kwargs).first()
                    if grade_obj:
                        # your grade models use related field grade_id -> letter/gp in earlier code
                        # adapt to actual model fields:
                        # in your earlier code you used grade_qs.grade_id.is_grade_name and grade_qs.grade_point
                        # Here attempt both attributes (safe)
                        try:
                            letter_grade = grade_obj.grade_id.is_grade_name
                        except Exception:
                            # fallback attribute names
                            letter_grade = getattr(grade_obj, "letter_grade", "F")
                        # gp might be stored as grade_point or gp_display etc.
                        gp_display = float(getattr(grade_obj, "grade_point", getattr(grade_obj, "gp", 0.0) or 0.0))
                    else:
                        # if no grade found, assume fail (but with floor fix, should rarely happen)
                        letter_grade = "F"
                        gp_display = 0.0
                # build final subject entry
                subject_entry = {
                    "id": sid,
                    "name": sub["name"],
                    "full_marks": full_marks,
                    "pass_marks": pass_marks,
                    "is_optional": is_optional,
                    "is_not_countable": is_not_countable,
                    "modes_ordered": subject_modes_ordered,
                    "modes": per_mode_entries,
                    "Total mode_names Marks": total_subject_marks,
                    "letter_grade": letter_grade,
                    "gp": float(gp_display)
                }
                final_subjects.append(subject_entry)
                # only sum subjects which are countable (your earlier logic sums all subject totals into total_marks regardless; keep same)
                total_obtained_all_subjects += total_subject_marks
                # TOTAL FULL MARKS (Correct)
                total_full_marks = sum(s["full_marks"] for s in final_subjects)
            # -------------------------
            # Extra Calculation Part: GPA, average letter mapping, remarks
            # Keep your original logic: optional handling and fail_flag across all subjects
            # -------------------------
            total_marks = total_obtained_all_subjects
            count_subjects = 0
            total_gp = 0.0
            overall_fail_flag = False
            optional_bonus = 0.0
            for s in final_subjects:
                if s["is_not_countable"]:
                    continue
                if not s["is_optional"]:
                    count_subjects += 1
                    if isinstance(s["gp"], (int, float)):
                        total_gp += s["gp"]
                    if s["gp"] == 0.00:
                        overall_fail_flag = True
                else:
                    # optional subject handling: bonus = gp - 2.00 positive part
                    if isinstance(s["gp"], (int, float)):
                        bonus = s["gp"] - 2.00
                        if bonus > 0:
                            optional_bonus += bonus
                    # check subject optional fail mapping from subjects_qs (is_optional_wise_grade_cal)
                    subj_obj = next((x for x in subjects_qs if x.subjects_id == s["id"]), None)
                    if subj_obj and not subj_obj.is_optional_wise_grade_cal and s["letter_grade"] == "F":
                        overall_fail_flag = True
            if count_subjects > 0:
                adjusted_gp = total_gp + optional_bonus
                average_gpa = adjusted_gp / count_subjects
            else:
                average_gpa = 0.00
            if overall_fail_flag:
                average_gpa = 0.00
            if average_gpa > 5.00:
                average_gpa = 5.00
            # Average letter grade mapping (same thresholds you used)
            if average_gpa == 0.00:
                average_letter_grade = "F"
            elif average_gpa >= 5.00:
                average_letter_grade = "A+"
            elif average_gpa >= 4.00:
                average_letter_grade = "A"
            elif average_gpa >= 3.50:
                average_letter_grade = "A-"
            elif average_gpa >= 3.00:
                average_letter_grade = "B"
            elif average_gpa >= 2.00:
                average_letter_grade = "C"
            elif average_gpa >= 1.00:
                average_letter_grade = "D"
            else:
                average_letter_grade = "F"
            remarks_map = {
                "A+": "Outstanding Achievement!",
                "A": "Impressive Performance!",
                "A-": "Commendable Performance!",
                "B": "Encouraging Performance!",
                "C": "An Average Performance!",
                "D": "Needs Significant Improvement!",
                "F": "Unsatisfactory Performance!"
            }
            remarks_status = remarks_map.get(average_letter_grade, "")
            result_status = "Failed" if average_gpa == 0.00 and average_letter_grade == "F" else "Passed"
            # ===============================
            # Transaction Data
            # ===============================
            def title_case(value):
                return ' '.join(word.capitalize() for word in str(value or "").split()) if value else ''

            transaction = {
                'create_date': card_entry.create_date or '',
                'reg_id': registration.reg_id if registration else '',
                'org_name': card_entry.org_id.org_name if card_entry.org_id else '',
                'full_name': title_case(registration.full_name),
                'roll_no': registration.roll_no or '',
                'father_name': title_case(registration.father_name),
                'mother_name': title_case(registration.mother_name),
                'class_name': card_entry.class_id.class_name if card_entry.class_id else '',
                'section_name': card_entry.section_id.section_name if card_entry.section_id else '',
                'shift_name': card_entry.shift_id.shift_name if card_entry.shift_id else '',
                'groups_name': card_entry.groups_id.groups_name if card_entry.groups_id else '',
                'total_working_days': card_entry.total_working_days or '',
                'total_present_days': card_entry.total_present_days or '',
                'is_remarks': card_entry.is_remarks or '',
                'date_of_publication': card_entry.date_of_publication or '',
                'is_average_gpa': card_entry.is_average_gpa or '',
                'average_letter_grade': card_entry.average_letter_grade or '',
                'total_obtained_marks': card_entry.total_obtained_marks or '',
                'result_status': card_entry.result_status or '',
                'merit_position': merit_position,
                'is_year': is_year,
                'merit_id': merit_id,
                "exam_type_name": exam_type_name,
            }
            
            # -------------------------
            # Response for this reg_id
            # -------------------------
            final_response[reg_id] = {
                "success": True,
                "half_percent": half_percent,
                "annual_percent": annual_percent,
                "mode_names": mode_names_ordered,
                "half_yearly_exam": [
                    {
                        "subject_id": sid,
                        "modes": half_map.get(sid, {}),
                        "subject_total_half": sum([v["actual"] for v in half_map.get(sid, {}).values()]) if half_map.get(sid) else 0.0
                    } for sid in sorted(list(half_map.keys()))
                ],
                "annual_exam": [
                    {
                        "subject_id": sid,
                        "modes": annual_map.get(sid, {}),
                        "subject_total_annual": sum([v["actual"] for v in annual_map.get(sid, {}).values()]) if annual_map.get(sid) else 0.0
                    } for sid in sorted(list(annual_map.keys()))
                ],
                "final_subjects": final_subjects,
                "total_full_marks": round(total_full_marks, 2),
                "total_obtained_marks": round(total_marks, 2),
                "average_gpa": round(average_gpa, 2),
                "average_letter_grade": average_letter_grade,
                "remarks_status": remarks_status,
                "result_status": result_status,
            }
            
            # print("final_response:", final_response[reg_id])
            

            html = render_to_string(
                'result_card_entry/annual_result_card/annual_card_report/annual_report_card_report.html',
                {
                    "transaction": transaction,
                    "registration": registration,
                    "table_data": table_data,
                    "final_response": final_response[reg_id],
                }
            )

            rendered_pages.append(html)
            
    return HttpResponse("".join(rendered_pages))

@login_required()
def printisAnnualDetailsResultAPI(request):
    if request.method != 'GET':
        return JsonResponse({"success": False, "message": "Invalid request"})

    # -------------------------
    # GET params
    # -------------------------
    org_id = request.GET.get("org_id")
    branch_id = request.GET.get("branch_id")
    reg_ids = request.GET.getlist("reg_ids")
    class_id = request.GET.get("class_id")
    shifts_id = request.GET.get("shift_id")
    groups_id = request.GET.get("groups_id")
    groups_id = int(groups_id) if groups_id and groups_id != "null" else None
    year = request.GET.get("is_year")
    version = request.GET.get("is_version")  # "english" / "bangla"
    merit_id = request.GET.get("merit_id")

    if not reg_ids:
        return JsonResponse({"success": False, "message": "No reg_id provided"})

    is_english = version == "english"
    is_bangla = version == "bangla"

    final_response = {}

    # Fetch all merit positions at once
    merit_qs = in_merit_position_approvaldtls.objects.filter(
        merit_id=merit_id,
        reg_id__in=reg_ids
    ).values("reg_id", "merit_position")
    merit_dict = {str(item["reg_id"]): item["merit_position"] for item in merit_qs}

    # Sort reg_ids by merit_position ascending
    reg_ids_sorted = sorted(reg_ids, key=lambda rid: merit_dict.get(str(rid), float('inf')))

    for reg_id in reg_ids_sorted:
        merit_position = merit_dict.get(str(reg_id), 0)

        # -------------------------
        # Get card entry
        # -------------------------
        card_entry = in_results_card_entry.objects.filter(
            reg_id=reg_id,
            org_id=org_id,
            branch_id=branch_id,
            class_id=class_id,
            shift_id=shifts_id,
            groups_id=groups_id,
            is_annual=True,
            is_half_year=False
        ).first()

        if not card_entry:
            final_response[str(reg_id)] = {"success": False, "message": f"No result card found for RegID={reg_id}"}
            continue

        registration = card_entry.reg_id  # Django model instance

        # -------------------------
        # Serialize registration
        # -------------------------
        registration_serialized = {
            "reg_id": registration.reg_id,
            "full_name": registration.full_name,
            "roll_no": registration.roll_no,
            "father_name": registration.father_name,
            "mother_name": registration.mother_name,
            "class_id": registration.class_id.class_id if registration.class_id else None,
            "groups_id": registration.groups_id.groups_id if registration.groups_id else None,
            "is_optional_sub_id": registration.is_optional_sub_id,
        }

        # -------------------------
        # Serialize card_entry
        # -------------------------
        card_entry_serialized = {
            "create_date": str(card_entry.create_date) if card_entry.create_date else "",
            "total_working_days": card_entry.total_working_days or 0,
            "total_present_days": card_entry.total_present_days or 0,
            "is_remarks": card_entry.is_remarks or "",
            "date_of_publication": str(card_entry.date_of_publication) if card_entry.date_of_publication else "",
            "is_average_gpa": card_entry.is_average_gpa or 0,
            "average_letter_grade": card_entry.average_letter_grade or "",
            "total_obtained_marks": card_entry.total_obtained_marks or 0,
            "result_status": card_entry.result_status or "",
            "org_name": card_entry.org_id.org_name if card_entry.org_id else "",
            "class_name": card_entry.class_id.class_name if card_entry.class_id else "",
            "section_name": card_entry.section_id.section_name if card_entry.section_id else "",
            "shift_name": card_entry.shift_id.shift_name if card_entry.shift_id else "",
        }

        # -------------------------
        # Transaction dict
        # -------------------------
        def title_case(value):
            return ' '.join(word.capitalize() for word in value.split()) if value else ''

        transaction = {
            "reg_id": registration_serialized["reg_id"],
            "full_name": title_case(registration_serialized["full_name"]),
            "roll_no": registration_serialized["roll_no"],
            "father_name": title_case(registration_serialized["father_name"]),
            "mother_name": title_case(registration_serialized["mother_name"]),
            "class_name": card_entry_serialized["class_name"],
            "section_name": card_entry_serialized["section_name"],
            "shift_name": card_entry_serialized["shift_name"],
            "total_working_days": card_entry_serialized["total_working_days"],
            "total_present_days": card_entry_serialized["total_present_days"],
            "is_remarks": card_entry_serialized["is_remarks"],
            "date_of_publication": card_entry_serialized["date_of_publication"],
            "is_average_gpa": card_entry_serialized["is_average_gpa"],
            "average_letter_grade": card_entry_serialized["average_letter_grade"],
            "total_obtained_marks": card_entry_serialized["total_obtained_marks"],
            "result_status": card_entry_serialized["result_status"],
            "merit_position": merit_position,
            "org_name": card_entry_serialized["org_name"],
            "create_date": card_entry_serialized["create_date"],
            "is_year": year
        }

        # -------------------------
        # Collect Grade Maps
        # -------------------------
        fifty_grades = in_letter_gradeFiftyMap.objects.filter(is_active=True, org_id=org_id, class_id=class_id)
        hundred_grades = in_letter_gradeHundredMap.objects.filter(is_active=True, org_id=org_id, class_id=class_id)
        if is_english:
            fifty_grades = fifty_grades.filter(is_english=True)
            hundred_grades = hundred_grades.filter(is_english=True)
        if is_bangla:
            fifty_grades = fifty_grades.filter(is_bangla=True)
            hundred_grades = hundred_grades.filter(is_bangla=True)

        fifty_grade_ids = list(fifty_grades.values_list("grade_id", flat=True))
        hundred_grade_ids = list(hundred_grades.values_list("grade_id", flat=True))
        grade_ids = set(fifty_grade_ids + hundred_grade_ids)

        grades = in_letter_grade_mode.objects.filter(grade_id__in=grade_ids).order_by("grade_id")
        table_data = []
        for grade in grades:
            fifty_map = fifty_grades.filter(grade_id=grade).first()
            hundred_map = hundred_grades.filter(grade_id=grade).first()
            table_data.append({
                "grade_name": grade.is_grade_name,
                "fifty_interval": f"{fifty_map.from_marks}-{fifty_map.to_marks}" if fifty_map else "",
                "hundred_interval": f"{hundred_map.from_marks}-{hundred_map.to_marks}" if hundred_map else "",
                "grade_point": float(fifty_map.grade_point) if fifty_map else (float(hundred_map.grade_point) if hundred_map else 0.0)
            })
        
        # -------------------------
        # Subjects (same ordering logic you had)
        # -------------------------
        base_filter = {
            "class_id": registration.class_id,
            "groups_id": registration.groups_id,
            "org_id": registration.org_id,
            "is_active": True
        }
        if is_english:
            base_filter["is_english"] = True
        if is_bangla:
            base_filter["is_bangla"] = True
        
        subjects_qs = (
            in_subjects.objects
            .filter(**base_filter)
            .annotate(
                is_numeric=Case(
                    When(subjects_no__regex=r'^\d+$', then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                ),
                subjects_as_int=Case(
                    When(subjects_no__regex=r'^\d+$', then=Cast('subjects_no', IntegerField())),
                    default=Value(999999999),
                    output_field=IntegerField(),
                )
            )
            .order_by('-is_numeric', 'subjects_as_int', 'subjects_no')
        )
        
        subjects_list = []
        for s in subjects_qs:
            subjects_list.append({
                "id": s.subjects_id,
                "name": s.subjects_name,
                "full_marks": s.is_marks,
                "pass_marks": s.is_pass_marks or 0,
                "is_applicable_pass_marks": s.is_applicable_pass_marks,
                "modes_half": {},
                "modes_annual": {},
                "is_optional": s.is_optional and s.subjects_id == registration.is_optional_sub_id,
                "is_not_countable": s.is_not_countable,
                "letter_grade": "",
                "gp": "-"
            })
        
        # -------------------------
        # load percentage policy
        # -------------------------
        policy = annual_exam_percentance_policy.objects.filter(
            org_id_id=org_id,
            class_id_id=class_id
        ).first()
        half_percent = int(policy.half_yearly_per) if policy and policy.half_yearly_per else 0
        annual_percent = int(policy.annual_per) if policy and policy.annual_per else 0
        
        # -------------------------
        # load half and annual result rows
        # -------------------------
        half_qs = in_result_finalizationdtls.objects.filter(
            org_id_id=org_id,
            branch_id_id=branch_id,
            reg_id_id=reg_id,
            class_id_id=class_id,
            shifts_id_id=shifts_id,
            groups_id_id=groups_id,
            finalize_year=year,
            is_half_yearly=True,
            is_approved=True
        ).select_related("subject_id", "def_mode_id")
        
        annual_qs = in_result_finalizationdtls.objects.filter(
            org_id_id=org_id,
            branch_id_id=branch_id,
            reg_id_id=reg_id,
            class_id_id=class_id,
            shifts_id_id=shifts_id,
            groups_id_id=groups_id,
            finalize_year=year,
            is_yearly=True,
            is_approved=True
        ).select_related("subject_id", "def_mode_id")
        
        # -------------------------
        # build mode maps
        # -------------------------
        half_map = {}
        annual_map = {}
        mode_names_set = set()
        exam_type_name = annual_qs.first().exam_type_id.exam_type_name if annual_qs.exists() else ""  # Corrected: use empty string instead of None to avoid null
        
        for r in half_qs:
            sid = r.subject_id.subjects_id
            mode = r.is_mode_name or ""
            mode_names_set.add(mode)
            half_map.setdefault(sid, {})
            half_map[sid].setdefault(mode, {"actual": 0.0, "pass": 0.0, "default": 0.0, "def_mode_id": None})
            half_map[sid][mode]["actual"] += float(r.is_actual_marks or 0.0)
            half_map[sid][mode]["pass"] = float(r.is_pass_marks or 0.0)
            half_map[sid][mode]["default"] = float(r.is_default_marks or 0.0)
            half_map[sid][mode]["def_mode_id"] = getattr(r.def_mode_id, "def_mode_id", None)
        
        for r in annual_qs:
            sid = r.subject_id.subjects_id
            mode = r.is_mode_name or ""
            mode_names_set.add(mode)
            annual_map.setdefault(sid, {})
            annual_map[sid].setdefault(mode, {"actual": 0.0, "pass": 0.0, "default": 0.0, "def_mode_id": None})
            annual_map[sid][mode]["actual"] += float(r.is_actual_marks or 0.0)
            annual_map[sid][mode]["pass"] = float(r.is_pass_marks or 0.0)
            annual_map[sid][mode]["default"] = float(r.is_default_marks or 0.0)
            annual_map[sid][mode]["def_mode_id"] = getattr(r.def_mode_id, "def_mode_id", None)
        
        ordered_modes_qs = defaults_exam_modes.objects.filter(is_active=True, is_mode_name__in=list(mode_names_set)).order_by("order_by")
        mode_names_ordered = [m.is_mode_name for m in ordered_modes_qs] if ordered_modes_qs.exists() else sorted(list(mode_names_set))
        
        # -------------------------
        # Calculate per-subject totals
        # -------------------------
        final_subjects = []
        total_obtained_all_subjects = 0.0
        for sub in subjects_list:
            sid = sub["id"]
            full_marks = float(sub["full_marks"] or 0)
            pass_marks = float(sub["pass_marks"] or 0)
            is_optional = sub["is_optional"]
            is_not_countable = sub["is_not_countable"]
            is_applicable_pass_marks = sub["is_applicable_pass_marks"]
            per_mode_entries = {}
            subject_half_total = 0.0
            subject_annual_total = 0.0
            subject_modes = set()
            subject_modes.update(half_map.get(sid, {}).keys())
            subject_modes.update(annual_map.get(sid, {}).keys())
            subject_modes_ordered = [m for m in mode_names_ordered if m in subject_modes] + [m for m in subject_modes if m not in mode_names_ordered]
            total_subject_weighted = Decimal('0.00')
            failed_flag_for_subject = False
            for mode in subject_modes_ordered:
                half_mode = half_map.get(sid, {}).get(mode, {"actual": 0.0, "pass": 0.0, "default": 0.0, "def_mode_id": None})
                annual_mode = annual_map.get(sid, {}).get(mode, {"actual": 0.0, "pass": 0.0, "default": 0.0, "def_mode_id": None})
                half_actual = float(half_mode["actual"] or 0.0)
                annual_actual = float(annual_mode["actual"] or 0.0)
                subject_half_total += half_actual
                subject_annual_total += annual_actual
                weighted_half = (Decimal(str(half_actual)) * Decimal(str(half_percent))) / Decimal(100) if half_percent else Decimal('0.00')
                weighted_annual = (Decimal(str(annual_actual)) * Decimal(str(annual_percent))) / Decimal(100) if annual_percent else Decimal('0.00')
                mode_total_weighted = (weighted_half + weighted_annual).quantize(Decimal('0.01'))
                per_mode_entries[mode] = {
                    "def_mode_id": half_mode.get("def_mode_id") or annual_mode.get("def_mode_id"),
                    "half_actual": round(half_actual, 2),
                    "annual_actual": round(annual_actual, 2),
                    f"{half_percent}% of Half Yearly Exam": float(weighted_half),
                    f"{annual_percent}% of Annual Exam": float(weighted_annual),
                    "Total mode_names Marks": float(mode_total_weighted)
                }
                total_subject_weighted += mode_total_weighted
                # FAIL LOGIC
                half_pass_val = float(half_mode.get("pass") or 0.0)
                annual_pass_val = float(annual_mode.get("pass") or 0.0)
                if half_actual and half_pass_val and (half_actual < half_pass_val):
                    failed_flag_for_subject = True
                if annual_actual and annual_pass_val and (annual_actual < annual_pass_val):
                    failed_flag_for_subject = True
            
            if is_applicable_pass_marks:
                if subject_half_total and (subject_half_total < pass_marks):
                    failed_flag_for_subject = True
                if subject_annual_total and (subject_annual_total < pass_marks):
                    failed_flag_for_subject = True
            
            total_subject_marks = float(total_subject_weighted.quantize(Decimal('0.01')))
            
            # letter & GP
            if is_not_countable:
                letter_grade = "-"
                gp_display = 0.0
            else:
                filter_kwargs = {
                    "org_id_id": org_id,
                    "class_id_id": registration.class_id,
                    "from_marks__lte": total_subject_marks,
                    "to_marks__gte": total_subject_marks,
                    "is_active": True
                }
                if is_english:
                    filter_kwargs["is_english"] = True
                if is_bangla:
                    filter_kwargs["is_bangla"] = True
                
                grade_obj = None
                if full_marks == 100:
                    grade_obj = in_letter_gradeHundredMap.objects.filter(**filter_kwargs).first()
                elif full_marks == 50:
                    grade_obj = in_letter_gradeFiftyMap.objects.filter(**filter_kwargs).first()
                else:
                    grade_obj = in_letter_gradeHundredMap.objects.filter(**filter_kwargs).first() or in_letter_gradeFiftyMap.objects.filter(**filter_kwargs).first()
                
                if grade_obj:
                    try:
                        letter_grade = grade_obj.grade_id.is_grade_name
                    except Exception:
                        letter_grade = getattr(grade_obj, "letter_grade", "F")
                    gp_display = float(getattr(grade_obj, "grade_point", getattr(grade_obj, "gp", 0.0) or 0.0))
                else:
                    letter_grade = "F" if failed_flag_for_subject else "F"  # Note: this seems like a potential bug in original; always "F" if no grade_obj
                
            if failed_flag_for_subject:
                letter_grade = "F"
                gp_display = 0.0
            
            subject_entry = {
                "id": sid,
                "name": sub["name"],
                "full_marks": full_marks,
                "pass_marks": pass_marks,
                "is_optional": is_optional,
                "is_not_countable": is_not_countable,
                "modes_ordered": subject_modes_ordered,
                "modes": per_mode_entries,
                "Total mode_names Marks": total_subject_marks,
                "letter_grade": letter_grade,
                "gp": float(gp_display)
            }
            final_subjects.append(subject_entry)
            total_obtained_all_subjects += total_subject_marks
        
        # GPA and remarks
        total_marks = total_obtained_all_subjects
        count_subjects = 0
        total_gp = 0.0
        overall_fail_flag = False
        optional_bonus = 0.0
        for s in final_subjects:
            if s["is_not_countable"]:
                continue
            if not s["is_optional"]:
                count_subjects += 1
                if isinstance(s["gp"], (int, float)):
                    total_gp += s["gp"]
                if s["gp"] == 0.00:
                    overall_fail_flag = True
            else:
                if isinstance(s["gp"], (int, float)):
                    bonus = s["gp"] - 2.00
                    if bonus > 0:
                        optional_bonus += bonus
                subj_obj = next((x for x in subjects_qs if x.subjects_id == s["id"]), None)
                if subj_obj and not subj_obj.is_optional_wise_grade_cal and s["letter_grade"] == "F":
                    overall_fail_flag = True
        
        average_gpa = (total_gp + optional_bonus) / count_subjects if count_subjects > 0 else 0.0
        if overall_fail_flag:
            average_gpa = 0.0
        if average_gpa > 5.0:
            average_gpa = 5.0
        
        # Average letter grade
        if average_gpa == 0.0:
            average_letter_grade = "F"
        elif average_gpa >= 5.0:
            average_letter_grade = "A+"
        elif average_gpa >= 4.0:
            average_letter_grade = "A"
        elif average_gpa >= 3.50:
            average_letter_grade = "A-"
        elif average_gpa >= 3.0:
            average_letter_grade = "B"
        elif average_gpa >= 2.0:
            average_letter_grade = "C"
        elif average_gpa >= 1.0:
            average_letter_grade = "D"
        else:
            average_letter_grade = "F"
        
        remarks_map = {
            "A+": "Outstanding Achievement!",
            "A": "Impressive Performance!",
            "A-": "Commendable Performance!",
            "B": "Encouraging Performance!",
            "C": "An Average Performance!",
            "D": "Needs Significant Improvement!",
            "F": "Unsatisfactory Performance!"
        }
        remarks_status = remarks_map.get(average_letter_grade, "")
        
        result_status = "Failed" if average_gpa == 0.0 and average_letter_grade == "F" else "Passed"
        
        # -------------------------
        # Response for this reg_id
        # -------------------------
        final_response[reg_id] = {
            "success": True,
            "half_percent": half_percent,
            "annual_percent": annual_percent,
            "mode_names": mode_names_ordered,
            # "transaction": transaction,
            # "table_data": table_data,
            "half_yearly_exam": [
                {
                    "subject_id": sid,
                    "modes": half_map.get(sid, {}),
                    "subject_total_half": sum([v["actual"] for v in half_map.get(sid, {}).values()]) if half_map.get(sid) else 0.0
                } for sid in sorted(list(half_map.keys()))
            ],
            "annual_exam": [
                {
                    "subject_id": sid,
                    "modes": annual_map.get(sid, {}),
                    "subject_total_annual": sum([v["actual"] for v in annual_map.get(sid, {}).values()]) if annual_map.get(sid) else 0.0
                } for sid in sorted(list(annual_map.keys()))
            ],
            "final_subjects": final_subjects,
            "total_obtained_marks": round(total_marks, 2),
            "average_gpa": round(average_gpa, 2),
            "average_letter_grade": average_letter_grade,
            "remarks_status": remarks_status,
            "result_status": result_status,
            "exam_type_name": exam_type_name,
        }
    
    return JsonResponse(final_response)


def testingAPI(request):
    

    return render(request, 'result_card_entry/print_result_card_half_yearly_report.html')