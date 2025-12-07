import re
import math
from decimal import Decimal
from django.db.models.functions import Cast
from django.db.models import Q, Sum, IntegerField, Value, Case, When, F, Prefetch
from audioop import reverse
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, Http404
from django.contrib import messages
from django.db import transaction, IntegrityError
from defaults_exam_mode.models import defaults_exam_modes, in_letter_gradeFiftyMap, in_letter_gradeHundredMap
from exam_type.models import in_exam_type
from merit_app_card_print.models import in_merit_position_approval, in_merit_position_approvaldtls, in_merit_position_subjectdtls
from organizations.models import branchslist, organizationlst
from class_setup.models import in_class
from groups_setup.models import in_groups
from policy_setup.models import annual_exam_percentance_policy, classSectionGroupingMap, in_class_wise_merit_policy, in_subject_wise_merit_policy
from result_card_entry.models import in_results_card_entry
from section_setup.models import in_section
from shift_setup.models import in_shifts
from registrations.models import in_registrations
from subject_setup.models import in_subjects
from result_finalization.models import in_result_finalizationdtls
from attendant_manager.models import in_student_attendant, in_student_attendantdtls
from django.template.loader import render_to_string
from weasyprint import HTML
from django.contrib.auth import get_user_model

from user_setup.models import access_list
User = get_user_model()


@login_required()
def meritPositionApproveListManagerAPI(request):
    
    return render(request, 'merit_pos_app_card_print/merit_position_approve_list.html')

@login_required()
def meritPositionAppAndCardPrintManagerAPI(request):
    
    return render(request, 'result_card_print/results_card_print_list.html')

@login_required()
def reportMeritPositionManagerAPI(request):
    
    return render(request, 'merit_pos_app_card_print/report_merit_position.html')

@login_required()
def meritPositionApprovalManagerAPI(request):
    
    examtypelist = in_exam_type.objects.filter(is_active=True).filter(Q(is_half_yearly=True) | Q(is_yearly=True))

    return render(request, 'merit_pos_app_card_print/merit_position_approve.html', {'examtypelist': examtypelist})


# ================================================================================================================
@login_required()
def getFinalizedResultDataForMeritPosAPI(request):
    org_id = request.GET.get("org_id")
    branch_id = request.GET.get("branch_id")
    class_id = request.GET.get("class_id")
    section_ids = request.GET.getlist("section_ids")
    shift_id = request.GET.get("shift_id")
    group_id = request.GET.get("group_id") or None
    year = int(request.GET.get("year") or 0)
    version = request.GET.get("version")  # english / bangla
    exam_type_id = request.GET.get("exam_type_id")
    is_half_year = str(request.GET.get("is_half_year", "")).lower() in ["1", "true", "yes"]
    is_yearly = str(request.GET.get("is_yearly", "")).lower() in ["1", "true", "yes"]
    
    # Normalize incoming section_ids
    section_ids = normalize_section_ids(section_ids)
    
    # Check already created data
    already_created_response = check_already_created(
        org_id, branch_id, class_id, shift_id, group_id, year, is_half_year, is_yearly, version, section_ids
    )
    if already_created_response:
        return already_created_response
    
    half_percent = 0
    annual_percent = 0
    if is_yearly:
        policy = annual_exam_percentance_policy.objects.filter(
            org_id_id=org_id,
            class_id_id=class_id
        ).first()
        half_percent = int(policy.half_yearly_per) if policy and policy.half_yearly_per else 40
        annual_percent = int(policy.annual_per) if policy and policy.annual_per else 60
    
    # Subject Wise Policy
    sub_group_subjects, normal_subjects = get_subject_policy(
        org_id, class_id, version, group_id
    )
    
    # Base Student Data
    card_qs, restricted_reg_ids = get_base_student_data(
        org_id, branch_id, class_id, shift_id, version, is_half_year, is_yearly, section_ids, group_id, year
    )
    
    # Subject Marks
    subject_marks, marks_map, mode_map = get_subject_marks(
        org_id, branch_id, class_id, shift_id, year, version, is_half_year, is_yearly, section_ids, group_id, restricted_reg_ids, half_percent=half_percent, annual_percent=annual_percent
    )
    
    # All subjects metadata
    all_subjects_meta = get_all_subjects_meta(org_id, class_id, group_id, version)
    
    # Policy and flags
    policy, use_fail_count, use_gross = get_policy_and_flags(org_id, class_id, version)
    
    # Combine Student Rows (+ Fail Count)
    results = combine_student_rows(
        card_qs, marks_map, mode_map, all_subjects_meta, sub_group_subjects, normal_subjects, use_fail_count, policy, org_id=org_id, class_id=class_id, version=version, is_yearly=is_yearly
    )
    
    # Sorting Key
    combined_sort_key_func = get_combined_sort_key_func(use_fail_count, policy, sub_group_subjects, normal_subjects)
    
    # Merit position assignment
    results = assign_merit_positions(results, use_gross, combined_sort_key_func, org_id, class_id, version, shift_id, group_id)
    
    # Prepare Subject List
    subjects = prepare_subject_list(sub_group_subjects, normal_subjects)
    
    # Final sort by merit_position ascending
    results.sort(key=lambda r: r.get("merit_position", 999999))
    
    return JsonResponse({
        "subjects": subjects,
        "results": results,
        "meta": {
            "fail_subject_count_enabled": use_fail_count,
            "gross_merit_enabled": use_gross,
            "note": "When gross_merit_enabled, groups (by classSectionGroupingMap) determine starting blocks; positions assigned within each group."
        }
    })

# Utility Functions 
def normalize_section_ids(section_ids):
    if len(section_ids) == 1 and section_ids[0] and "," in section_ids[0]:
        section_ids = section_ids[0].split(",")
    section_ids = [int(s) for s in section_ids if s and str(s).isdigit()]
    section_ids = list(dict.fromkeys(section_ids))  # preserve order but unique
    return section_ids

# Check Already Created Data
def check_already_created(org_id, branch_id, class_id, shift_id, group_id, year, is_half_year, is_yearly, version, section_ids):
    already_qs = in_merit_position_approval.objects.filter(
        org_id_id=org_id,
        branch_id_id=branch_id,
        class_id_id=class_id,
        shifts_id_id=shift_id,
        groups_id_id=group_id,
        merit_year=year,
        is_half_yearly=is_half_year,
        is_yearly=is_yearly,
        is_english=(version == "english"),
        is_bangla=(version == "bangla"),
    )
    if section_ids:
        already_qs = already_qs.filter(section_id__in=section_ids).distinct()
    if already_qs.exists():
        return JsonResponse({
            "already_created": True,
            "subject_count": 0,
        })
    return None

# Subject Wise Policy
def get_subject_policy(org_id, class_id, version, group_id):
    subject_policy_qs = in_subject_wise_merit_policy.objects.filter(
        org_id=org_id,
        class_id=class_id,
        is_english=(version == "english"),
        is_bangla=(version == "bangla"),
    )
    if group_id:
        subject_policy_qs = subject_policy_qs.filter(groups_id=group_id)
    else:
        subject_policy_qs = subject_policy_qs.filter(groups_id__isnull=True)
    sub_group_subjects = list(
        subject_policy_qs.filter(is_sub_groups=True)
        .order_by("subject_priority")
        .values("subjects_id", "subjects_id__subjects_name", "subject_priority")
    )
    normal_subjects = list(
        subject_policy_qs.filter(is_sub_groups=False)
        .order_by("subject_priority")
        .values("subjects_id", "subjects_id__subjects_name", "subject_priority")
    )
    return sub_group_subjects, normal_subjects

# Base Student Data
def get_base_student_data(org_id, branch_id, class_id, shift_id, version, is_half_year, is_yearly, section_ids, group_id, year):
    card_filters = {
        "org_id": org_id,
        "branch_id": branch_id,
        "class_id": class_id,
        "shift_id": shift_id,
        "is_english": (version == "english"),
        "is_bangla": (version == "bangla"),
        "is_half_year": is_half_year,
        "is_annual": is_yearly,
    }
    if section_ids:
        card_filters["section_id__in"] = section_ids
    if group_id:
        card_filters["groups_id"] = group_id
    # Restriction Filter
    restricted_reg_ids = set(
        in_registrations.objects.filter(
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
        ).values_list("reg_id", flat=True)
    )
    card_qs = in_results_card_entry.objects.filter(**card_filters)
    if year:
        card_qs = card_qs.filter(create_date=year)
    # Remove restricted students
    card_qs = card_qs.exclude(reg_id__in=restricted_reg_ids)
    # include section_id for grouping mapping
    card_qs = card_qs.values(
        "reg_id",
        "reg_id__roll_no",
        "reg_id__full_name",
        "is_average_gpa",
        "total_obtained_marks",
        "section_id",
        "section_id__section_name",
        "reg_id__is_optional_sub_id"
    )
    return card_qs, restricted_reg_ids

# Subject Marks
def get_subject_marks(org_id, branch_id, class_id, shift_id, year, version, is_half_year, is_yearly, section_ids, group_id, restricted_reg_ids, half_percent=0, annual_percent=0):
    fin_filters = {
        "org_id": org_id,
        "branch_id": branch_id,
        "class_id": class_id,
        "shifts_id": shift_id,
        "finalize_year": year,
        "is_english": (version == "english"),
        "is_bangla": (version == "bangla"),
        "is_approved": True,
    }
    if section_ids:
        fin_filters["section_id__in"] = section_ids
    if group_id:
        fin_filters["groups_id"] = group_id
    else:
        fin_filters["groups_id__isnull"] = True
    
    marks_map = {}
    mode_map = {}
    
    if is_yearly:
        fin_filters_half = fin_filters.copy()
        fin_filters_half['is_half_yearly'] = True
        fin_filters_half['is_yearly'] = False
        half_qs = in_result_finalizationdtls.objects.filter(**fin_filters_half).select_related("subject_id")
        half_qs = half_qs.exclude(reg_id__in=restricted_reg_ids)
        
        fin_filters_annual = fin_filters.copy()
        fin_filters_annual['is_half_yearly'] = False
        fin_filters_annual['is_yearly'] = True
        annual_qs = in_result_finalizationdtls.objects.filter(**fin_filters_annual).select_related("subject_id")
        annual_qs = annual_qs.exclude(reg_id__in=restricted_reg_ids)
        
        half_mode_map = {}
        for r in half_qs:
            regid = r.reg_id_id
            sid = r.subject_id_id if r.subject_id_id else None
            if not sid:
                continue
            mode = r.is_mode_name or ""
            half_mode_map.setdefault(regid, {}).setdefault(sid, {}).setdefault(mode, {'actual': 0.0, 'pass': 0.0, 'default': 0.0, 'def_mode_id': getattr(r.def_mode_id, 'def_mode_id', None)})
            half_mode_map[regid][sid][mode]['actual'] += float(r.is_actual_marks or 0.0)
            half_mode_map[regid][sid][mode]['pass'] = float(r.is_pass_marks or 0.0)
            half_mode_map[regid][sid][mode]['default'] = float(r.is_default_marks or 0.0)
        
        annual_mode_map = {}
        for r in annual_qs:
            regid = r.reg_id_id
            sid = r.subject_id_id if r.subject_id_id else None
            if not sid:
                continue
            mode = r.is_mode_name or ""
            annual_mode_map.setdefault(regid, {}).setdefault(sid, {}).setdefault(mode, {'actual': 0.0, 'pass': 0.0, 'default': 0.0, 'def_mode_id': getattr(r.def_mode_id, 'def_mode_id', None)})
            annual_mode_map[regid][sid][mode]['actual'] += float(r.is_actual_marks or 0.0)
            annual_mode_map[regid][sid][mode]['pass'] = float(r.is_pass_marks or 0.0)
            annual_mode_map[regid][sid][mode]['default'] = float(r.is_default_marks or 0.0)
        
        all_regids = set(half_mode_map.keys()) | set(annual_mode_map.keys())
        subject_marks = []
        for regid in all_regids:
            all_sids = set(half_mode_map.get(regid, {}).keys()) | set(annual_mode_map.get(regid, {}).keys())
            for sid in all_sids:
                all_modes = set(half_mode_map.get(regid, {}).get(sid, {}).keys()) | set(annual_mode_map.get(regid, {}).get(sid, {}).keys())
                combined_total = Decimal('0.0')
                mode_list = []
                for mode in all_modes:
                    h = half_mode_map.get(regid, {}).get(sid, {}).get(mode, {'actual':0.0, 'pass':0.0})
                    a = annual_mode_map.get(regid, {}).get(sid, {}).get(mode, {'actual':0.0, 'pass':0.0})
                    comb_a = Decimal(str(h['actual'])) * Decimal(str(half_percent)) / Decimal('100') + Decimal(str(a['actual'])) * Decimal(str(annual_percent)) / Decimal('100')
                    comb_p = Decimal(str(h['pass'])) * Decimal(str(half_percent)) / Decimal('100') + Decimal(str(a['pass'])) * Decimal(str(annual_percent)) / Decimal('100')
                    combined_total += comb_a
                    mode_list.append((float(comb_a), float(comb_p)))
                marks_map.setdefault(regid, {})[sid] = round(float(combined_total), 2)
                mode_map.setdefault(regid, {})[sid] = mode_list
                subject_marks.append({'reg_id': regid, 'subject_id': sid, 'total_marks': round(float(combined_total), 2)})
    else:
        fin_filters['is_half_yearly'] = is_half_year
        fin_filters['is_yearly'] = is_yearly
        fin_qs = in_result_finalizationdtls.objects.filter(**fin_filters).select_related("subject_id")
        # Remove restricted students
        fin_qs = fin_qs.exclude(reg_id__in=restricted_reg_ids)
        subject_marks = fin_qs.values("reg_id", "subject_id").annotate(total_marks=Sum("is_actual_marks"))
        marks_map = {}
        for sm in subject_marks:
            regid = sm["reg_id"]
            if regid not in marks_map:
                marks_map[regid] = {}
            marks_map[regid][sm["subject_id"]] = sm["total_marks"]
        mode_map = {}
        for r in fin_qs:
            regid = r.reg_id_id
            sid = r.subject_id_id if r.subject_id_id else None
            if not sid:
                continue
            mode_map.setdefault(regid, {}).setdefault(sid, []).append(
                (float(r.is_actual_marks or 0.0), float(r.is_pass_marks or 0.0))
            )
    return subject_marks, marks_map, mode_map

# All subjects metadata
def get_all_subjects_meta(org_id, class_id, group_id, version):
    base_filter = {
        "class_id": class_id,
        "org_id": org_id,
        "is_active": True
    }
    if group_id:
        base_filter["groups_id"] = group_id
    else:
        base_filter["groups_id__isnull"] = True
    if version == "english":
        base_filter["is_english"] = True
    if version == "bangla":
        base_filter["is_bangla"] = True
    all_subjects_qs = in_subjects.objects.filter(**base_filter).values(
        "subjects_id", "subjects_name", "is_marks", "is_pass_marks", "is_applicable_pass_marks", "is_not_countable", "is_optional_wise_grade_cal"
    )
    all_subjects_meta = {
        x["subjects_id"]: {
            "full_marks": x["is_marks"],
            "pass_marks": float(x["is_pass_marks"] or 0.0),
            "is_applicable_pass_marks": bool(x["is_applicable_pass_marks"]),
            "is_not_countable": bool(x["is_not_countable"]),
            "is_optional_wise_grade_cal": bool(x["is_optional_wise_grade_cal"]),
            "name": x["subjects_name"]
        }
        for x in all_subjects_qs
    }
    return all_subjects_meta

# Policy and flags
def get_policy_and_flags(org_id, class_id, version):
    policy = in_class_wise_merit_policy.objects.filter(
        org_id=org_id,
        class_id=class_id,
        is_english=(version == "english"),
        is_bangla=(version == "bangla"),
    ).first()
    use_fail_count = bool(policy and policy.is_fail_sub_count)
    use_gross = bool(policy and policy.is_gross_merit_position)
    return policy, use_fail_count, use_gross

# Combine Student Rows
def combine_student_rows(card_qs, marks_map, mode_map, all_subjects_meta, sub_group_subjects, normal_subjects, use_fail_count, policy, org_id=None, class_id=None, version=None, is_yearly=False):
    def is_subject_failed(regid, sid):
        meta = all_subjects_meta.get(sid)
        if not meta:
            return False
        if meta["is_not_countable"]:
            return False
        total = float(marks_map.get(regid, {}).get(sid, 0.0))  # subject total
        subject_pass_marks = float(meta.get("pass_marks") or 0.0)  # from in_subjects
        if meta.get("is_applicable_pass_marks"):
            # Case 1️⃣ Subject-level pass marks (from in_subjects)
            if total < subject_pass_marks:
                return True
        else:
            # Case 2️⃣ Mode-level pass marks (from in_result_finalizationdtls)
            for actual, p in mode_map.get(regid, {}).get(sid, []):
                if float(actual) < float(p):  # যদি কোনো mode fail করে
                    return True
        return False
    
    results = []
    display_subjects = (sub_group_subjects + normal_subjects)
    for c in card_qs:
        regid = c["reg_id"]
        section_id_val = c.get("section_id")
        # --- ✅ Roll no handling (numeric + suffix safe split) ---
        roll_no_raw = str(c.get("reg_id__roll_no") or "").strip()
        # pure digits হলে int, নাহলে 99999
        roll_no_digits = re.findall(r"\d+", roll_no_raw)
        roll_no_val = int(roll_no_digits[0]) if roll_no_digits else 99999
        # non-digit suffix বের করি
        roll_no_suffix_match = re.findall(r"[A-Za-z]+", roll_no_raw)
        roll_no_suffix = roll_no_suffix_match[0] if roll_no_suffix_match else ""
        # final display
        display_roll_no = roll_no_raw
        row = {
            "reg_id": regid,
            "roll_no": display_roll_no,  # original দেখাবো
            "roll_no_val": roll_no_val,  # sort করার জন্য numeric
            "roll_no_suffix": roll_no_suffix,  # suffix sort এর জন্য
            "full_name": c["reg_id__full_name"],
            "is_average_gpa": float(c["is_average_gpa"] or 0.0),
            "total_obtained_marks": float(c["total_obtained_marks"] or 0.0),
            "subjects": {},
            "section": c.get("section_id__section_name", ""),
            "section_id": section_id_val,
            "optional_sub_id": c.get("reg_id__is_optional_sub_id", None)
        }
        # Populate marks for policy display subjects
        for s in display_subjects:
            sid = s["subjects_id"]
            sname = s["subjects_id__subjects_name"]
            row["subjects"][sname] = marks_map.get(regid, {}).get(sid, 0)
        if sub_group_subjects:
            subgroup_total = sum(marks_map.get(regid, {}).get(s["subjects_id"], 0) for s in sub_group_subjects)
            row["subjects"]["Tot Group Marks"] = subgroup_total
        # Fail count
        fail_count = 0
        for sid in all_subjects_meta.keys():
            if is_subject_failed(regid, sid):
                fail_count += 1
        row["fail_subject_count"] = fail_count
        
        if is_yearly:
            # Override total_obtained_marks with combined sum
            row["total_obtained_marks"] = round(sum(marks_map.get(regid, {}).values()), 2)
            
            # Calculate is_average_gpa based on combined
            total_gp = 0.0
            count_subjects = 0
            overall_fail_flag = False
            optional_bonus = 0.0
            for sid in all_subjects_meta:
                meta = all_subjects_meta[sid]
                if meta["is_not_countable"]:
                    continue
                total_marks = marks_map.get(regid, {}).get(sid, 0.0)
                full_marks = meta["full_marks"]
                lookup_marks = math.floor(total_marks)
                filter_kwargs = {
                    "org_id_id": org_id,
                    "class_id_id": class_id,
                    "from_marks__lte": lookup_marks,
                    "to_marks__gte": lookup_marks,
                    "is_active": True
                }
                if version == "english":
                    filter_kwargs["is_english"] = True
                if version == "bangla":
                    filter_kwargs["is_bangla"] = True
                grade_obj = None
                if full_marks == 100:
                    grade_obj = in_letter_gradeHundredMap.objects.filter(**filter_kwargs).first()
                elif full_marks == 50:
                    grade_obj = in_letter_gradeFiftyMap.objects.filter(**filter_kwargs).first()
                else:
                    # fallback
                    grade_obj = in_letter_gradeHundredMap.objects.filter(**filter_kwargs).first() or in_letter_gradeFiftyMap.objects.filter(**filter_kwargs).first()
                if grade_obj:
                    letter_grade = grade_obj.grade_id.is_grade_name
                    gp = float(grade_obj.grade_point or 0.0)
                else:
                    letter_grade = "F"
                    gp = 0.0
                is_optional = (sid == row.get("optional_sub_id"))
                if not is_optional:
                    count_subjects += 1
                    total_gp += gp
                    if gp == 0.0:
                        overall_fail_flag = True
                else:
                    bonus = gp - 2.0
                    if bonus > 0:
                        optional_bonus += bonus
                    if not meta.get("is_optional_wise_grade_cal", False) and letter_grade == "F":
                        overall_fail_flag = True
            if count_subjects > 0:
                adjusted_gp = total_gp + optional_bonus
                average_gpa = adjusted_gp / count_subjects
            else:
                average_gpa = 0.0
            if overall_fail_flag:
                average_gpa = 0.0
            if average_gpa > 5.0:
                average_gpa = 5.0
            row["is_average_gpa"] = average_gpa
        
        results.append(row)
    return results

# Combined Sort Key
def get_combined_sort_key_func(use_fail_count, policy, sub_group_subjects, normal_subjects):
    def combined_sort_key(r):
        key = []
        # 🔹 Fail subject count priority (ascending, highest priority)
        if use_fail_count:
            key.append(r.get("fail_subject_count", 0))  # Ascending order
        # 🔹 GPA priority
        if policy and policy.is_average_gpa_priority is not None:
            key.append(-r["is_average_gpa"])  # Descending order
        # 🔹 Total marks
        if policy and policy.total_obtained_marks_priority is not None:
            key.append(-r["total_obtained_marks"])  # Descending order
        # 🔹 Group marks
        if sub_group_subjects:
            key.append(-r["subjects"].get("Tot Group Marks", 0))  # Descending order
        # 🔹 Subject wise priority
        for s in normal_subjects:
            key.append(-r["subjects"].get(s["subjects_id__subjects_name"], 0))  # Descending order
        # 🔹 Roll no priority (numeric first, then suffix lexicographic)
        if policy and policy.roll_no_priority is not None:
            key.append(r.get("roll_no_val", 99999))  # Ascending order
            key.append(r.get("roll_no_suffix", ""))  # Ascending order (lexicographic)
        return tuple(key)
    return combined_sort_key

# Assign Merit Positions
def assign_merit_positions(results, use_gross, combined_sort_key_func, org_id, class_id, version, shift_id, group_id):
    if not use_gross:
        results.sort(key=combined_sort_key_func)
        merit_pos = 1
        prev_key = None
        for i, r in enumerate(results, start=1):
            curr_key = combined_sort_key_func(r)
            if prev_key == curr_key:
                r["merit_position"] = merit_pos
            else:
                merit_pos = i
                r["merit_position"] = merit_pos
            prev_key = curr_key
    else:
        # Gross merit: section grouping map logic
        map_qs = classSectionGroupingMap.objects.filter(
            org_id=org_id,
            class_id=class_id,
            is_english=(version == "english"),
            is_bangla=(version == "bangla")
        ).order_by("is_order_by", "clss_sec_map_id")
        groups_ordered = []
        section_to_group_index = {}
        temp_group_by_no = {}
        ordered_entries = list(map_qs)
        for entry in ordered_entries:
            sid = entry.section_id_id
            if entry.is_grouping_flag and entry.is_group_no:
                gno = entry.is_group_no
                if gno not in temp_group_by_no:
                    temp_group_by_no[gno] = {
                        "order_by": entry.is_order_by or 0,
                        "sections": []
                    }
                temp_group_by_no[gno]["sections"].append(sid)
            elif entry.is_individual_flag:
                groups_ordered.append({
                    "order_by": entry.is_order_by or 0,
                    "sections": [sid],
                    "group_key": f"ind_{entry.clss_sec_map_id}"
                })
            else:
                groups_ordered.append({
                    "order_by": entry.is_order_by or 0,
                    "sections": [sid],
                    "group_key": f"map_{entry.clss_sec_map_id}"
                })
        for gno, info in temp_group_by_no.items():
            groups_ordered.append({
                "order_by": info.get("order_by", 0),
                "sections": info.get("sections", []),
                "group_key": f"group_{gno}"
            })
        groups_ordered = sorted(groups_ordered, key=lambda x: (x["order_by"] or 0))
        for idx, g in enumerate(groups_ordered):
            for sid in g["sections"]:
                section_to_group_index[sid] = idx
        filtered_section_ids = set(r["section_id"] for r in results if r.get("section_id"))
        mapped_section_ids = set(section_to_group_index.keys())
        unmapped_section_ids = list(filtered_section_ids - mapped_section_ids)
        if unmapped_section_ids:
            max_order = max([g["order_by"] or 0 for g in groups_ordered], default=0)
            groups_ordered.append({
                "order_by": max_order + 1,
                "sections": unmapped_section_ids,
                "group_key": "unmapped"
            })
            unmapped_idx = len(groups_ordered) - 1
            for sid in unmapped_section_ids:
                section_to_group_index[sid] = unmapped_idx
        group_sizes = []
        for g in groups_ordered:
            sids = [s for s in g["sections"] if s]
            if not sids:
                group_sizes.append(0)
                continue
            reg_filters = {
                "org_id": org_id,
                "class_id": class_id,
                "shift_id": shift_id,
                "is_english": (version == "english"),
                "is_bangla": (version == "bangla")
            }
            cnt = in_registrations.objects.filter(**reg_filters, section_id__in=sids).count()
            group_sizes.append(cnt)
        group_starts = []
        running = 1
        for sz in group_sizes:
            group_starts.append(running)
            running += (sz or 0)
        group_results_map = {i: [] for i in range(len(groups_ordered))}
        fallback_idx = len(groups_ordered) - 1 if groups_ordered else 0
        for r in results:
            sid = r.get("section_id")
            gi = section_to_group_index.get(sid, fallback_idx)
            group_results_map.setdefault(gi, []).append(r)
        assigned_positions = {}
        for gi, group in enumerate(groups_ordered):
            start_pos = group_starts[gi] if gi < len(group_starts) else running
            group_students = group_results_map.get(gi, [])
            group_students.sort(key=combined_sort_key_func)
            pos = start_pos
            for student in group_students:
                student["merit_position"] = pos
                assigned_positions[student["reg_id"]] = pos
                pos += 1
        assigned_regids = set(assigned_positions.keys())
        next_pos = running
        for r in results:
            if r["reg_id"] not in assigned_regids:
                r["merit_position"] = next_pos
                next_pos += 1
    return results

# Prepare Subject List
def prepare_subject_list(sub_group_subjects, normal_subjects):
    subjects = []
    subjects.extend(sub_group_subjects)
    if sub_group_subjects:
        subjects.append({"subjects_id": None, "subjects_id__subjects_name": "Tot Group Marks", "subject_priority": 9998})
    subjects.extend(normal_subjects)
    return subjects

# ================================================================================================================

    
# ========================================================
# Save Approved Merit Positions API
# ========================================================    
    
@login_required
def saveApproveMeritPositionAPI(request):
    if request.method == "POST":
        try:
            # =========================
            # 1️⃣ Approval-level fields
            # =========================
            org_id = request.POST.get('org')
            branch_id = request.POST.get('branchs')
            class_id = request.POST.get('is_class')
            shifts_id = request.POST.get('is_shifts')
            groups_id = request.POST.get('is_groups') or None
            sections_raw = request.POST.getlist('is_section')  # may contain single IDs or CSVs
            version = request.POST.get('is_version')
            exam_type_id = request.POST.get('exam_type')  # exam_type_id from select
            year = request.POST.get('is_year')

            # =========================
            # 2️⃣ Determine exam flags from in_exam_type table
            # =========================
            is_half_yearly = False
            is_yearly = False
            if exam_type_id:
                try:
                    exam = in_exam_type.objects.get(exam_type_id=exam_type_id)
                    is_half_yearly = exam.is_half_yearly
                    is_yearly = exam.is_yearly
                except in_exam_type.DoesNotExist:
                    pass  # defaults False

            # Language flags
            is_english = True if version == "english" else False
            is_bangla = True if version == "bangla" else False

            # =========================
            # 3️⃣ Create Approval Record
            # =========================
            approval = in_merit_position_approval.objects.create(
                org_id_id=org_id,
                branch_id_id=branch_id,
                class_id_id=class_id,
                shifts_id_id=shifts_id,
                groups_id_id=groups_id,
                is_half_yearly=is_half_yearly,
                is_yearly=is_yearly,
                is_english=is_english,
                is_bangla=is_bangla,
                merit_year=year,
                is_approved=True,
                is_approved_by=request.user,
                approved_date=datetime.now(),
                ss_creator=request.user,
                ss_modifier=request.user,
            )

            # =========================
            # 4️⃣ Save ManyToManyField sections
            # =========================
            section_ids = []
            for val in sections_raw:
                # split if CSV, else keep as is
                section_ids.extend(val.split(","))

            # cleanup (remove blanks, ensure unique)
            section_ids = [sid.strip() for sid in section_ids if sid.strip()]

            if section_ids:
                approval.section_id.set(section_ids)

            # =========================
            # 5️⃣ Student-level data
            # =========================
            roll_nos = request.POST.getlist('roll_no[]')
            fail_subject_counts = request.POST.getlist('fail_subject_count[]')
            reg_ids = request.POST.getlist('reg_id[]')
            merit_positions = request.POST.getlist('merit_position[]')

            for roll_no, fail_subject_count, reg_id, merit_pos in zip(roll_nos, fail_subject_counts, reg_ids, merit_positions):
                in_merit_position_approvaldtls.objects.create(
                    merit_id=approval,
                    reg_id_id=reg_id,
                    roll_no=roll_no,
                    fail_subject_count=int(fail_subject_count),
                    merit_position=int(merit_pos),
                    ss_creator=request.user
                )
                
            
            subject_ids = request.POST.getlist('subject_id[]')
            subject_names = request.POST.getlist('subject_name[]')
            subject_prioritys = request.POST.getlist('subject_priority[]')
            subjects_marks = request.POST.getlist('subject_marks[]')

            # One student subject count (from AJAX response);
            subject_count = int(request.POST.get("subject_count"))

            # Total students
            total_students = len(reg_ids)

            # Safety check
            expected_total_subject_rows = subject_count * total_students
            if len(subject_ids) != expected_total_subject_rows:
                print("Subject count mismatch!")
                # handle mismatch or raise error

            index = 0  # pointer through subject lists

            for reg_id in reg_ids:

                # প্রতিটি ছাত্রের subject_count অনুযায়ী ডাটা নেবো
                for x in range(subject_count):

                    sid = subject_ids[index]
                    sname = subject_names[index]
                    spriority = subject_prioritys[index]
                    smarks = subjects_marks[index]
                    index += 1  # NEXT pointer

                    # Handle null subject
                    if sid in ["", "null", None]:
                        subject_instance = None
                    else:
                        try:
                            subject_instance = in_subjects.objects.get(pk=sid)
                        except:
                            subject_instance = None

                    in_merit_position_subjectdtls.objects.create(
                        merit_id=approval,
                        reg_id_id=reg_id,
                        subject_id=subject_instance,
                        subject_name=sname,
                        subject_priority=int(spriority) if spriority else 0,
                        subject_marks=float(smarks) if smarks else 0,
                        ss_creator=request.user
                    )

            return JsonResponse({
                "success": True,
                "msg": "Merit positions approved successfully!"
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "errmsg": str(e)
            })
            
            
@login_required            
def getMeritApprovalsListManagerAPI(request):
    user = request.user
    org_id = request.GET.get("org_id")
    branch_id = request.GET.get("branch_id")
    class_id = request.GET.get("class_id")
    shift_id = request.GET.get("shift_id")
    groups_id = request.GET.get("groups_id")
    year = request.GET.get("year")
    version = request.GET.get("version")  # english/bangla
    is_exams_types = request.GET.get("is_exams_types")  # half_yearly/yearly
    
    has_access = access_list.objects.filter(
        user_id=user,
        feature_id__feature_page_link='MERITPROLLBACKBTNACC',
        is_active=True
    ).exists()

    qs = in_merit_position_approval.objects.all()

    if org_id:
        qs = qs.filter(org_id_id=org_id)
    if branch_id:
        qs = qs.filter(branch_id_id=branch_id)
    if class_id:
        qs = qs.filter(class_id_id=class_id)
    if shift_id:
        qs = qs.filter(shifts_id_id=shift_id)
    if groups_id:
        qs = qs.filter(groups_id_id=groups_id)
    if year:
        qs = qs.filter(merit_year=year)
    if version:
        if version.lower() == "english":
            qs = qs.filter(is_english=True)
        elif version.lower() == "bangla":
            qs = qs.filter(is_bangla=True)
            
    if is_exams_types:
        if is_exams_types.lower() == "is_half_yearly":
            qs = qs.filter(is_half_yearly=True)
        elif is_exams_types.lower() == "is_annual":
            qs = qs.filter(is_yearly=True)
    # ⚡ Bulk prefetch sections + dtls + reg info in one go
    qs = qs.prefetch_related(
        "section_id",
        Prefetch(
            "merit_id2merit_positiondtls",
            queryset=in_merit_position_approvaldtls.objects.select_related("reg_id__section_id"),
        )
    ).select_related("class_id", "shifts_id", "groups_id", "is_approved_by")

    data = []
    for obj in qs:
        sections_qs = obj.section_id.all()
        sections = ", ".join([s.section_name for s in sections_qs]) if sections_qs else "-"
        section_ids = [s.section_id for s in sections_qs] if sections_qs else []

        # Build reg_ids_by_section from prefetched dtls (no new queries!)
        reg_ids_by_section = {}
        for dtl in obj.merit_id2merit_positiondtls.all():
            if not dtl.reg_id:
                continue
            sec_id = dtl.reg_id.section_id_id  # integer
            reg_ids_by_section.setdefault(sec_id, []).append(dtl.reg_id.reg_id)

        data.append({
            "merit_id": obj.merit_id,
            "org_id": obj.org_id.org_id if obj.org_id else "",
            "branch_id": obj.branch_id.branch_id if obj.branch_id else "",
            "created_date": obj.created_date.strftime("%Y-%m-%d") if obj.created_date else "",
            "class_id": obj.class_id.class_id if obj.class_id else "",
            "class_name": obj.class_id.class_name if obj.class_id else "",
            "sections": sections,
            "section_ids": section_ids,
            "reg_ids_by_section": reg_ids_by_section,
            "shift": obj.shifts_id.shift_name if obj.shifts_id else "",
            "shift_id": obj.shifts_id.shift_id if obj.shifts_id else "",
            "groups": obj.groups_id.groups_name if obj.groups_id else "",
            "groups_id": obj.groups_id.groups_id if obj.groups_id else "",
            "approved_date": obj.approved_date or "",
            "approved_by": obj.is_approved_by.username if obj.is_approved_by else "",
            "merit_year": obj.merit_year or "",
            "is_half_yearly": obj.is_half_yearly,
            "is_yearly": obj.is_yearly,
            "is_english": obj.is_english,
            "is_bangla": obj.is_bangla,
            "is_half_roll_sec_change": obj.is_half_roll_sec_change,
            "is_approved": obj.is_approved,
            "is_half_roll_sec_change_by": obj.is_half_roll_sec_change_by.username if obj.is_half_roll_sec_change_by else "",
            "half_roll_sec_change_date": obj.is_half_roll_sec_change_date or "",
            "has_access": has_access,
        })

    return JsonResponse({"data": data})


@login_required
def get_sections_by_class(request):
    try:
        org_id = request.GET.get("org_id")
        class_id = request.GET.get("class_id")
        version = request.GET.get("version")  # english/bangla

        filters = {
            "org_id_id": org_id,
            "class_id_id": class_id,
        }

        if version == "english":
            filters["is_english"] = True
        elif version == "bangla":
            filters["is_bangla"] = True

        mappings = classSectionGroupingMap.objects.filter(**filters).select_related("section_id")

        section_list = []

        # Individual Sections
        for m in mappings.filter(is_individual_flag=True):
            section_list.append({
                "type": "individual",
                "value": str(m.section_id.section_id),
                "label": m.section_id.section_name
            })

        # Grouped Sections
        grouped = {}
        for m in mappings.filter(is_grouping_flag=True):
            grouped.setdefault(m.is_group_no, {
                "group_no": m.is_group_no,
                "group_name": m.is_group_name,
                "sections": []
            })
            grouped[m.is_group_no]["sections"].append({
                "id": m.section_id.section_id,
                "name": m.section_id.section_name
            })

        for g in grouped.values():
            section_list.append({
                "type": "group",
                "value": ",".join(str(s["id"]) for s in g["sections"]),
                "label": g["group_name"],
                "sections": g["sections"]
            })

        return JsonResponse({"sections": section_list})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
    

@login_required()
def rollbackMeritPositionManagerAPI(request):
    merit_data = {}
    if request.method == 'GET':
        data = request.GET
        merit_id = ''
        if 'merit_id' in data:
            merit_id = data['merit_id']
        if merit_id.isnumeric() and int(merit_id) > 0:
            merit_data = in_merit_position_approval.objects.filter(merit_id=merit_id).first()

    context = {
        'merit_data': merit_data,
    }
    return render(request, 'merit_pos_app_card_print/merit_position_rollback_confirmation.html', context)


@csrf_exempt
def permanently_delete_merit_positionManagerAPI(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "errmsg": "Invalid Request"}, status=200)

    merit_id = request.POST.get("merit_id")

    if not merit_id:
        return JsonResponse({"success": False, "errmsg": "Merit ID Missing"}, status=200)

    try:
        obj = in_merit_position_approval.objects.get(pk=merit_id)
    except in_merit_position_approval.DoesNotExist:
        return JsonResponse({"success": False, "errmsg": "Invalid Merit ID"}, status=200)

    # ❗ CONDITION: If roll/section changed → STOP DELETE
    if obj.is_half_roll_sec_change:
        return JsonResponse({
            "success": False,
            "errmsg": "This Merit Position wise Section and Roll Already Changed.. "
                      "Please Section Roll Rollback First and Try Again ..."
        }, status=200)

    try:
        with transaction.atomic():

            in_merit_position_approvaldtls.objects.filter(merit_id=obj).delete()
            in_merit_position_subjectdtls.objects.filter(merit_id=obj).delete()
            obj.section_id.clear()
            obj.delete()

        return JsonResponse({"success": True, "msg": "Merit Position Deleted Successfully"}, status=200)

    except Exception as e:
        return JsonResponse({"success": False, "errmsg": str(e)}, status=200)
    

# ===============================================================
# Merit Position Report Data API
# ===============================================================
@login_required()
def getMeritPositionReportDataManagerAPI(request):
    
    merit_id = request.GET.get("merit_id")
    org_id = request.GET.get("org_id")
    branch_id = request.GET.get("branch_id")
    year = request.GET.get("year")
    version = request.GET.get("version")
    exams_type = request.GET.get("exams_type")
    class_id = request.GET.get("class_id")
    shift_id = request.GET.get("shift_id")
    groups_id = request.GET.get("groups_id")

    try:
        # -----------------------------
        # Header data
        # -----------------------------
        org = organizationlst.objects.get(org_id=org_id)
        branch = branchslist.objects.get(branch_id=branch_id)
        merit_master = in_merit_position_approval.objects.get(merit_id=merit_id)
        section_ids = list(merit_master.section_id.values_list('pk', flat=True))
        merit_details = in_merit_position_approvaldtls.objects.filter(merit_id=merit_id).select_related("reg_id")

        table_data = []
        sl = 1

        filter_year = int(year) if year and year.isdigit() else None
        filter_class = int(class_id) if class_id and class_id.isdigit() else None
        filter_shift = int(shift_id) if shift_id and shift_id.isdigit() else None
        filter_groups = int(groups_id) if groups_id and groups_id.isdigit() else None

        # -----------------------------
        # SUBJECT LIST (header)
        # -----------------------------
        # Fetch only distinct subjects for the merit, independent of students
        subjects_qs = in_merit_position_subjectdtls.objects.filter(
            merit_id=merit_id
        ).values('subject_name', 'subject_priority').distinct()

        # Separate regular and group total
        regular_subs = [sub for sub in subjects_qs if sub['subject_priority'] != 9998]
        group_sub = next((sub for sub in subjects_qs if sub['subject_priority'] == 9998), None)

        # Find min priority for assumed group subjects
        min_priority = min((s['subject_priority'] for s in regular_subs), default=None)

        if min_priority is not None:
            group_subs = [s for s in regular_subs if s['subject_priority'] == min_priority]
            other_subs = [s for s in regular_subs if s['subject_priority'] != min_priority]
        else:
            group_subs = []
            other_subs = regular_subs

        # Sort group_subs by subject_name
        group_subs = sorted(group_subs, key=lambda s: s['subject_name'])

        # Sort other_subs by priority
        other_subs = sorted(other_subs, key=lambda s: s['subject_priority'])

        # Build the list of subs in order: group_subs + group_total + other_subs
        ordered_subs = group_subs
        if group_sub:
            ordered_subs += [group_sub]
        ordered_subs += other_subs

        # Now create subject_columns
        subject_columns = []
        for sub in ordered_subs:
            priority = sub['subject_priority']
            subject_name = "Tot Group Marks" if priority == 9998 else sub['subject_name']
            col_key = "grp_total" if priority == 9998 else f"sub_{subject_name.replace(' ', '_').lower()}"
            subject_columns.append({
                "col_key": col_key,
                "subject_name": subject_name,
                "priority": priority
            })

        # -----------------------------
        # LOOP STUDENTS
        # -----------------------------
        for row in merit_details:
            reg = row.reg_id

            # GPA lookup
            gpa_qs = in_results_card_entry.objects.filter(
                org_id=org_id,
                branch_id=branch_id,
                reg_id=reg,
                section_id__in=section_ids
            )

            if filter_class: gpa_qs = gpa_qs.filter(class_id=filter_class)
            if filter_shift: gpa_qs = gpa_qs.filter(shift_id=filter_shift)
            if filter_groups: gpa_qs = gpa_qs.filter(groups_id=filter_groups)
            if filter_year: gpa_qs = gpa_qs.filter(create_date__year=filter_year)

            if exams_type == "is_half_yearly":
                gpa_qs = gpa_qs.filter(is_half_year=True)
            elif exams_type == "is_annual":
                gpa_qs = gpa_qs.filter(is_annual=True)

            if version == "english":
                gpa_qs = gpa_qs.filter(is_english=True)
            elif version == "bangla":
                gpa_qs = gpa_qs.filter(is_bangla=True)

            gpa_obj = gpa_qs.order_by('-trans_date').first()

            student_gpa = gpa_obj.is_average_gpa if gpa_obj else ""
            student_tot_marks = gpa_obj.total_obtained_marks if gpa_obj else ""

            # INITIAL row data
            row_data = {
                "sl": sl,
                "name": reg.full_name,
                "roll": reg.roll_no,
                "class": reg.class_id.class_name if reg.class_id else "",
                "section": reg.section_id.section_name if reg.section_id else "",
                "shift": reg.shift_id.shift_name if reg.shift_id else "",
                "groups": reg.groups_id.groups_name if reg.groups_id else "",
                "total_obtained_marks": student_tot_marks,
                "gpa": student_gpa,
                "fails_count": row.fail_subject_count,
                "merit_position": row.merit_position,
            }

            # -----------------------------
            # STUDENT-SPECIFIC SUBJECT MARKS
            # -----------------------------
            student_sub_marks = in_merit_position_subjectdtls.objects.filter(
                merit_id=merit_id,
                reg_id=reg
            ).values('subject_name', 'subject_priority', 'subject_marks')

            # Convert to dict for lookup
            student_sub_dict = {}
            for s in student_sub_marks:
                if s['subject_priority'] == 9998:
                    student_sub_dict['grp_total'] = s['subject_marks']
                else:
                    student_sub_dict[s['subject_name']] = s['subject_marks']

            # Fill row data
            for col in subject_columns:
                if col['priority'] == 9998:
                    row_data[col['col_key']] = student_sub_dict.get('grp_total', "")
                else:
                    row_data[col['col_key']] = student_sub_dict.get(col['subject_name'], "")

            table_data.append(row_data)
            sl += 1

        # -----------------------------
        # HEADER TEXT
        # -----------------------------
        exam_type_text = "Half Yearly" if merit_master.is_half_yearly else "Annual"
        version_text = "English" if merit_master.is_english else "Bangla"
        class_name = merit_master.class_id.class_name if merit_master.class_id else ""

        exam_type_version_year = (
            f"Exam Type: {exam_type_text} - Version: {version_text} - "
            f"Year: {merit_master.merit_year} - Class: {class_name}"
        )

        header = {
            "org_name": org.org_name,
            "address": org.address,
            "email": org.email,
            "website": org.website,
            "hotline": org.hotline,
            "fax": org.fax,
            "logo": org.org_logo.url if org.org_logo else "",
            "branch_name": branch.branch_name,
            "exam_type_version_year": exam_type_version_year,
        }

        return JsonResponse({
            "status": "success",
            "header": header,
            "subjects": subject_columns,
            "table": table_data
        })

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})