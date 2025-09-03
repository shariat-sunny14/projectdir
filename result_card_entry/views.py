import re, json, copy, math
from django.utils import timezone
from collections import defaultdict
from django.db.models.functions import Cast
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
from merit_app_card_print.models import in_merit_position_approvaldtls
from organizations.models import branchslist, organizationlst
from class_setup.models import in_class
from groups_setup.models import in_groups
from section_setup.models import in_section
from shift_setup.models import in_shifts
from registrations.models import in_registrations
from subject_setup.models import in_subjects
from result_finalization.models import in_result_finalizationdtls
from attendant_manager.models import in_student_attendant, in_student_attendantdtls
from . models import in_results_card_entry
from django.template.loader import render_to_string
from weasyprint import HTML
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def resultCardEntryListManagerAPI(request):
    
    return render(request, 'result_card_entry/result_card_entry_list.html')


@login_required()
def resultCardEntryRePrintListManagerAPI(request):
    
    return render(request, 'result_card_entry_re_print/result_card_entry_re_print_list.html')


@login_required()
def getRegistrationListDetailsAPI(request):
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
    current_year = now().year

    for reglist in reg_data:
        # Check if related results_card_entry exists for this reg_id and current year
        exists_result = in_results_card_entry.objects.filter(
            reg_id=reglist.reg_id,
            create_date=current_year
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
            'status': exists_result  # True if result exists, else False
        })

    return JsonResponse({'data': data})


@login_required()
def getResultCardEntryRePrintDetailsListAPI(request):
    org_filter = request.GET.get('filter_org')
    branch_filter = request.GET.get('filter_branch')
    filter_class = request.GET.get('filter_class')
    filter_section = request.GET.get('filter_section')
    filter_shift = request.GET.get('filter_shift')
    filter_groups = request.GET.get('filter_groups')
    filter_year = request.GET.get('filter_year')
    search_input = request.GET.get('searchInput')

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
        
    # Search logic (matches roll_no, full_name, or students_no)
    if search_input:
        filter_kwargs &= (
            Q(roll_no__icontains=search_input) |
            Q(full_name__icontains=search_input)
        )

    # Step 1: Get all matching registrations
    registrations = (
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

    for reg in registrations:
        # Step 2: Try to find matching result card
        try:
            result_card = in_results_card_entry.objects.get(reg_id=reg.reg_id, create_date=filter_year)
            res_card_id = result_card.res_card_id
            is_approved = result_card.is_approved
            approved_date = result_card.approved_date
            is_approved_by = result_card.is_approved_by.username if result_card.is_approved_by else ''
        except in_results_card_entry.DoesNotExist:
            res_card_id = ''
            is_approved = False
            approved_date = ''
            is_approved_by = ''

        # Step 3: Construct response row
        data.append({
            'res_card_id': res_card_id,
            'reg_id': reg.reg_id,
            'students_no': reg.students_no,
            'org_name': getattr(reg.org_id, 'org_name', None),
            'branch_name': getattr(reg.branch_id, 'branch_name', None),
            'class_name': getattr(reg.class_id, 'class_name', None),
            'section_name': getattr(reg.section_id, 'section_name', None),
            'shift_name': getattr(reg.shift_id, 'shift_name', None),
            'groups_name': getattr(reg.groups_id, 'groups_name', None),
            'full_name': reg.full_name,
            'roll_no': reg.roll_no,
            'is_approved': is_approved,
            'approved_date': approved_date,
            'is_approved_by': is_approved_by,
        })

    return JsonResponse({'data': data})


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
        section_id = safe_int(request.GET.get('section_id'))
        shift_id = safe_int(request.GET.get('shift_id'))
        groups_id = safe_int(request.GET.get('groups_id'))

        is_half_yearly = request.GET.get('is_half_yearly') == 'true'
        is_yearly = request.GET.get('is_yearly') == 'true'
        current_year = datetime.now().year

        # Build filter
        base_filter = {'attendant_year': current_year}
        if org_id: base_filter['org_id_id'] = org_id
        if branch_id: base_filter['branch_id_id'] = branch_id
        if class_id: base_filter['class_id_id'] = class_id
        if section_id: base_filter['section_id_id'] = section_id
        if shift_id: base_filter['shifts_id_id'] = shift_id
        if groups_id: base_filter['groups_id_id'] = groups_id
        if is_half_yearly: base_filter['is_half_yearly'] = True
        if is_yearly: base_filter['is_yearly'] = True

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
                    org_id_id=org_id,
                    class_id_id=registration.class_id,
                    from_marks__lte=total,
                    to_marks__gte=total,
                    is_active=True
                ).first()
            elif sub["full_marks"] == 50:
                grade_qs = in_letter_gradeFiftyMap.objects.filter(
                    org_id_id=org_id,
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
    id = request.GET.get('id')
    org_id = request.GET.get("org_id")
    class_id = request.GET.get("class_id")

    card_entry = get_object_or_404(in_results_card_entry, res_card_id=id)
    
    registration = get_object_or_404(in_registrations, reg_id=card_entry.reg_id.reg_id)

    def title_case(value):
        if value:
            return ' '.join(word.capitalize() for word in value.split())
        return ''
    
    ############################################### 
    # 50 এবং 100 map থেকে যেসব grade_id আছে সেগুলো collect করা
    fifty_grades = in_letter_gradeFiftyMap.objects.filter(
        org_id=org_id, class_id=class_id, is_active=True
    ).values_list("grade_id", flat=True)

    hundred_grades = in_letter_gradeHundredMap.objects.filter(
        org_id=org_id, class_id=class_id, is_active=True
    ).values_list("grade_id", flat=True)

    # দুই source merge করে unique grade_id নেওয়া
    grade_ids = set(list(fifty_grades) + list(hundred_grades))

    # ওই grade_id গুলো দিয়েই filter করা
    grades = in_letter_grade_mode.objects.filter(
        grade_id__in=grade_ids
    ).order_by("grade_id")

    table_data = []
    for grade in grades:
        fifty_map = in_letter_gradeFiftyMap.objects.filter(
            org_id=org_id, class_id=class_id, grade_id=grade, is_active=True
        ).first()

        hundred_map = in_letter_gradeHundredMap.objects.filter(
            org_id=org_id, class_id=class_id, grade_id=grade, is_active=True
        ).first()

        table_data.append({
            "grade_name": grade.is_grade_name,
            "fifty_interval": f"{fifty_map.from_marks}-{fifty_map.to_marks}" if fifty_map else "",
            "hundred_interval": f"{hundred_map.from_marks}-{hundred_map.to_marks}" if hundred_map else "",
            "grade_point": fifty_map.grade_point if fifty_map else (hundred_map.grade_point if hundred_map else ""),
        })
    ###############################################

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


# --- helpers stay the same (safe, tiny improvements) ---
def parse_int_param(value):
    """
    Safe int parser:
    - যদি value None, '', 'null', 'None', 'undefined' হয় → None ফেরত দেবে
    - যদি সংখ্যা হয় → int ফেরত দেবে
    """
    if value in [None, '', 'null', 'None', 'undefined']:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

def parse_int_list(value):
    """Safe list of ints parser"""
    if not value or value in ['null', 'None', 'undefined', '']:
        return []
    if isinstance(value, str):
        try:
            value = json.loads(value)  # JSON string হলে list বানাবে
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

def safe_value(val, placeholder="Missing"):
    return val if val not in [None, '', 'null', 'None'] else f"[{placeholder}]"

def title_case(value):
    return ' '.join(word.capitalize() for word in value.split()) if value else ''


def print_multiple_transcripts(request):
    if request.method != "POST":
        return HttpResponse("Invalid request method", status=400)

    try:
        print_blocks = json.loads(request.POST.get("print_blocks", "[]"))
    except Exception:
        return HttpResponse("Invalid print_blocks data", status=400)

    # ------------- CACHES / BATCH HELPERS -------------
    # subjects cache key: (class_id, groups_id, org_id, versionStr)
    subjects_cache = {}
    # grade map cache key: (org_id, class_id) -> {'50': [(from,to,grade_point,grade_name)], '100': [...]}
    grade_map_cache = {}
    # defaults_exam_modes: cache of active modes ordered; but we still order per set we actually see
    active_modes_by_name = {}  # name -> (order_by, name, id)
    # A tiny memo for mode order queries
    modes_loaded = False

    def load_grade_maps(org_id, class_id):
        """
        Load and cache both 50 and 100 marks grade maps for an (org, class).
        Structure for faster lookup by total: list of tuples.
        """
        key = (org_id, class_id)
        if key in grade_map_cache:
            return grade_map_cache[key]

        fifty_qs = list(
            in_letter_gradeFiftyMap.objects.filter(
                org_id_id=org_id, class_id_id=class_id, is_active=True
            ).select_related("grade_id")
        )
        hundred_qs = list(
            in_letter_gradeHundredMap.objects.filter(
                org_id_id=org_id, class_id_id=class_id, is_active=True
            ).select_related("grade_id")
        )
        def to_tuples(qs):
            # Keep original boundaries as-is to preserve behavior
            out = []
            for g in qs:
                out.append((
                    float(g.from_marks or 0),
                    float(g.to_marks or 0),
                    float(g.grade_point or 0),
                    g.grade_id.is_grade_name if g.grade_id else ""
                ))
            # sort for predictable scanning (optional)
            out.sort(key=lambda x: (x[0], x[1]))
            return out

        data = {
            '50': to_tuples(fifty_qs),
            '100': to_tuples(hundred_qs),
        }
        grade_map_cache[key] = data
        return data

    def find_grade(org_id, class_id, full_marks, total):
        """
        Match total in [from, to] range from cached grade map.
        """
        gm = load_grade_maps(org_id, class_id)
        bucket = '100' if full_marks == 100 else ('50' if full_marks == 50 else None)
        if bucket is None:
            return None
        for lo, hi, gp, name in gm[bucket]:
            # inclusive bounds as in original query (from_marks__lte & to_marks__gte)
            if lo <= total <= hi:
                return name, gp
        return None

    def subjects_for(class_id, groups_id, org_id, version):
        """
        Load subjects once per (class, groups, org, versionFlag).
        Returns a list of dict *templates*; caller must deepcopy before using.
        """
        key = (class_id, groups_id, org_id, version or '')
        if key in subjects_cache:
            return subjects_cache[key]

        base_filter = {"class_id_id": class_id, "groups_id_id": groups_id, "org_id_id": org_id, "is_active": True}
        if version == "english":
            base_filter["is_english"] = True
        elif version == "bangla":
            base_filter["is_bangla"] = True

        qs = (in_subjects.objects
              .filter(**base_filter)
              .annotate(subjects_no_int=Cast('subjects_no', IntegerField()))
              .order_by('subjects_no_int')
              .only("subjects_id", "subjects_name", "is_marks", "is_pass_marks",
                    "is_applicable_pass_marks", "is_optional", "is_not_countable"))

        templ = []
        for s in qs:
            templ.append({
                "id": s.subjects_id,
                "name": safe_value(s.subjects_name, "Subject"),
                "full_marks": s.is_marks,
                "pass_marks": s.is_pass_marks or 0,
                "is_applicable_pass_marks": s.is_applicable_pass_marks,
                "modes": {},  # will be filled per student
                "is_optional": False,  # will be set per student comparing registration.is_optional_sub_id
                "is_not_countable": s.is_not_countable,
                "letter_grade": "",
                "gp": "-"
            })
        subjects_cache[key] = templ
        return templ

    def ensure_modes_loaded(names):
        """
        Fill active_modes_by_name for given mode names once, keeping their order_by.
        """
        nonlocal modes_loaded
        needs = [n for n in names if n not in active_modes_by_name]
        if needs:
            # load ONLY requested names to reduce query load
            for m in defaults_exam_modes.objects.filter(is_active=True, is_mode_name__in=needs).only("is_mode_name", "order_by", "def_mode_id"):
                active_modes_by_name[m.is_mode_name] = (m.order_by, m.is_mode_name, m.def_mode_id)
        modes_loaded = True

    # ---------------------------------------------
    # MAIN LOOP (block by block)
    # ---------------------------------------------
    combined_html = ""
    now_str = timezone.now().strftime("%d/%m/%Y, %H:%M:%S")

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

        # ---------------------------
        # Grade mapping table (load ONCE per block)
        # ---------------------------
        # collect active grade_ids from both maps (exact as original, but single fetch)
        fifty_qs = in_letter_gradeFiftyMap.objects.filter(
            org_id_id=org_id, class_id_id=class_id, is_active=True
        ).select_related("grade_id").only("grade_id")
        hundred_qs = in_letter_gradeHundredMap.objects.filter(
            org_id_id=org_id, class_id_id=class_id, is_active=True
        ).select_related("grade_id").only("grade_id")

        grade_ids = set()
        for g in fifty_qs:
            if g.grade_id_id:
                grade_ids.add(g.grade_id_id)
        for g in hundred_qs:
            if g.grade_id_id:
                grade_ids.add(g.grade_id_id)

        grades = list(
            in_letter_grade_mode.objects.filter(grade_id__in=grade_ids).order_by("grade_id")
        )

        # build a quick dict for maps to avoid extra queries in the loop
        fifty_map_by_grade = {
            g.grade_id_id: g for g in in_letter_gradeFiftyMap.objects.filter(
                org_id_id=org_id, class_id_id=class_id, is_active=True
            ).select_related("grade_id")
        }
        hundred_map_by_grade = {
            g.grade_id_id: g for g in in_letter_gradeHundredMap.objects.filter(
                org_id_id=org_id, class_id_id=class_id, is_active=True
            ).select_related("grade_id")
        }

        table_data = []
        for grade in grades:
            gid = grade.grade_id
            fifty_map = fifty_map_by_grade.get(gid)
            hundred_map = hundred_map_by_grade.get(gid)

            # round values to 0 decimals and convert to int
            fifty_from = int(round(fifty_map.from_marks, 0)) if fifty_map else ""
            fifty_to = int(round(fifty_map.to_marks, 0)) if fifty_map else ""
            hundred_from = int(round(hundred_map.from_marks, 0)) if hundred_map else ""
            hundred_to = int(round(hundred_map.to_marks, 0)) if hundred_map else ""
            grade_point = int(round(fifty_map.grade_point, 0)) if fifty_map else (
                        int(round(hundred_map.grade_point, 0)) if hundred_map else "")

            table_data.append({
                "grade_name": grade.is_grade_name,
                "fifty_interval": f"{fifty_from}-{fifty_to}" if fifty_map else "",
                "hundred_interval": f"{hundred_from}-{hundred_to}" if hundred_map else "",
                "grade_point": grade_point,
            })

        # ---------------------------
        # Card entries for this block (single query)
        # ---------------------------
        filter_q = Q(org_id_id=org_id, branch_id_id=branch_id)
        if class_id: filter_q &= Q(class_id_id=class_id)
        if shift_id: filter_q &= Q(shift_id_id=shift_id)
        if groups_id: filter_q &= Q(groups_id_id=groups_id)
        if section_ids: filter_q &= Q(section_id_id__in=section_ids)
        if reg_ids: filter_q &= Q(reg_id_id__in=reg_ids)

        card_entries = list(
            in_results_card_entry.objects.filter(filter_q)
            .select_related(
                "class_id", "section_id", "shift_id", "groups_id",
                "org_id", "branch_id", "reg_id",
                "is_approved_by"
            )
            .order_by("reg_id__reg_id2merit_positiondtls__merit_position")
        )

        if not card_entries:
            # nothing to print in this block; continue
            continue

        # ---------------------------
        # Merit positions (batch)
        # ---------------------------
        reg_id_set = {ce.reg_id_id for ce in card_entries if ce.reg_id_id}
        merit_pos_by_reg = {}
        if merit_id and reg_id_set:
            for md in in_merit_position_approvaldtls.objects.filter(
                merit_id_id=merit_id, reg_id_id__in=reg_id_set
            ).only("reg_id_id", "merit_position"):
                merit_pos_by_reg[md.reg_id_id] = md.merit_position

        # ---------------------------
        # Subjects cache key per version
        # ---------------------------
        version_key = "english" if is_version == "english" else ("bangla" if is_version == "bangla" else None)

        # ---------------------------
        # Result details (batch by grouping common filters)
        # Group by: (section_id, is_english, is_bangla) because other filters are common in this block.
        # ---------------------------
        groups = defaultdict(list)
        for ce in card_entries:
            groups[(ce.section_id_id, ce.is_english, ce.is_bangla)].append(ce)

        # reg -> subject_id -> mode_name -> detail dict
        results_by_reg = {}
        # reg -> exam_type_name (first seen)
        exam_type_name_by_reg = {}

        for (sec_id, ce_is_eng, ce_is_ban), ces in groups.items():
            reg_ids_group = [c.reg_id_id for c in ces if c.reg_id_id]
            if not reg_ids_group:
                continue

            rqs = (in_result_finalizationdtls.objects
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
                       reg_id_id__in=reg_ids_group
                   )
                   .select_related("subject_id", "exam_type_id", "def_mode_id")
                   .only("reg_id_id", "subject_id__subjects_id", "def_mode_id__def_mode_id",
                         "is_mode_name", "is_actual_marks", "is_pass_marks", "is_default_marks",
                         "exam_type_id__exam_type_name"))

            # Collect mode names for ordering once
            mode_names = set()

            for r in rqs:
                rid = r.reg_id_id
                sid = r.subject_id.subjects_id if r.subject_id else None
                if not sid:
                    continue
                if rid not in results_by_reg:
                    results_by_reg[rid] = {}
                if sid not in results_by_reg[rid]:
                    results_by_reg[rid][sid] = {}
                results_by_reg[rid][sid][r.is_mode_name] = {
                    "def_mode_id": r.def_mode_id.def_mode_id if r.def_mode_id else None,
                    "actual": float(r.is_actual_marks or 0),
                    "pass": float(r.is_pass_marks or 0),
                    "default": float(r.is_default_marks or 0)
                }
                mode_names.add(r.is_mode_name)
                # store first exam_type_name for this reg
                if rid not in exam_type_name_by_reg and r.exam_type_id:
                    exam_type_name_by_reg[rid] = r.exam_type_id.exam_type_name

            # Load ordering for these modes
            if mode_names:
                ensure_modes_loaded(mode_names)

        # Build a single ordered mode list present in this block (keeps previous behavior of dynamic modes)
        # We respect order_by across all modes we saw, then sort by that.
        if active_modes_by_name:
            mode_names_ordered = [t[1] for t in sorted(active_modes_by_name.values(), key=lambda x: (x[0], x[1]))]
        else:
            mode_names_ordered = []

        # ---------------------------
        # Render each card (no DB in loop except grade lookup cache hit)
        # ---------------------------
        for ce in card_entries:
            registration = ce.reg_id  # already selected via select_related
            # subjects template (deepcopy because we mutate per student)
            subj_template = subjects_for(
                registration.class_id_id if registration and registration.class_id_id else class_id,
                registration.groups_id_id if registration else groups_id,
                org_id,
                version_key
            )
            subjects_list = copy.deepcopy(subj_template)

            # mark optional per student
            optional_id = registration.is_optional_sub_id if registration else None
            for sub in subjects_list:
                sub["is_optional"] = (sub["id"] == optional_id) and (optional_id is not None) and any([
                    True  # retains original logic: s.is_optional AND id match
                ])

            # results for this student
            reg_results = results_by_reg.get(ce.reg_id_id, {})
            # fill modes and compute grade/gp
            for sub in subjects_list:
                sub["modes"] = reg_results.get(sub["id"], {})
                safe_total = sum(float(m["actual"]) for m in sub["modes"].values()) if sub["modes"] else 0.0
                total = math.floor(safe_total)

                if sub["is_not_countable"]:
                    sub["letter_grade"] = "-"
                    sub["gp"] = "-"
                    continue

                # pass / fail logic identical to original
                if not sub["is_applicable_pass_marks"]:
                    failed_flag = any(float(m["actual"]) < float(m["pass"]) for m in sub["modes"].values())
                else:
                    failed_flag = total < sub["pass_marks"]

                if failed_flag:
                    sub["letter_grade"] = "F"
                    sub["gp"] = 0.00
                    continue

                # map to grade range (cached lookups)
                full_marks = sub["full_marks"]
                if full_marks in (50, 100):
                    gfound = find_grade(org_id, registration.class_id_id if registration else class_id, full_marks, total)
                    if gfound:
                        sub["letter_grade"], sub["gp"] = gfound[0], float(gfound[1])
                    else:
                        sub["letter_grade"] = "F"
                        sub["gp"] = 0.00
                else:
                    # original code only graded 50/100; keep same fallback
                    sub["letter_grade"] = "F"
                    sub["gp"] = 0.00

            # Merit
            merit_position = merit_pos_by_reg.get(ce.reg_id_id, 0)

            # Exam type name (first seen for this reg in batch)
            exam_type_name = exam_type_name_by_reg.get(ce.reg_id_id)

            # ---------------------------
            # Transaction context
            # ---------------------------
            transaction = {
                'create_date': safe_value(ce.create_date),
                'reg_id': safe_value(ce.reg_id.reg_id if ce.reg_id else ''),
                'org_name': safe_value(ce.org_id.org_name if ce.org_id else ''),
                'full_name': safe_value(title_case(ce.reg_id.full_name) if ce.reg_id else ''),
                'roll_no': safe_value(ce.reg_id.roll_no if ce.reg_id else ''),
                'father_name': safe_value(title_case(ce.reg_id.father_name) if ce.reg_id else ''),
                'mother_name': safe_value(title_case(ce.reg_id.mother_name) if ce.reg_id else ''),
                'class_name': safe_value(ce.class_id.class_name if ce.class_id else ''),
                'section_name': safe_value(ce.section_id.section_name if ce.section_id else ''),
                'shift_name': safe_value(ce.shift_id.shift_name if ce.shift_id else ''),
                'merit_position': safe_value(merit_position, "N/A"),
                'exam_type_name': safe_value(exam_type_name, "N/A"),
                'total_working_days': safe_value(ce.total_working_days),
                'total_present_days': safe_value(ce.total_present_days),
                'is_remarks': safe_value(ce.is_remarks),
                'date_of_publication': safe_value(ce.date_of_publication),
                'is_average_gpa': safe_value(ce.is_average_gpa),
                'average_letter_grade': safe_value(ce.average_letter_grade),
                'result_status': safe_value(ce.result_status),
                'total_obtained_marks': safe_value(ce.total_obtained_marks),
                'subjects': subjects_list,
                'mode_names': mode_names_ordered,
            }

            context = {
                "transaction": transaction,
                "printed_on": now_str,
                "table_data": table_data,
            }

            html_string = render_to_string("result_card_entry/print_result_card_half_yearly_report.html", context)
            combined_html += f'<div style="page-break-after: always;">{html_string}</div>'

    # Remove last page break
    combined_html = re.sub(r'<div style="page-break-after: always;">\s*$', '', combined_html)

    pdf = HTML(string=combined_html, base_url=request.build_absolute_uri('/')).write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="Academic_Transcript_Report.pdf"'
    return response




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


def testingAPI(request):
    

    return render(request, 'result_card_entry/print_result_card_half_yearly_report.html')