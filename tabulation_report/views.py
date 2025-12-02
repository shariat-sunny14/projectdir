import sys
import json
import base64, zlib, json
from django.db.models.functions import Cast
from collections import defaultdict, OrderedDict
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.db.models import Q, F, Sum, ExpressionWrapper, fields, FloatField, Case, When, Value, IntegerField, Max
from django.db import transaction
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from attendant_manager.models import in_student_attendant, in_student_attendantdtls
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

# Create your views here.
@login_required()
def reportTabulationListManagerAPI(request):
    
    return render(request, 'tabulation_report/tabulation_list.html')


@login_required()
def halfYearlyTabulationReportsManagerAPI(request):

    org_data = organizationlst.objects.filter(is_active=True).first()
    
    context = {
        "org_data": org_data
    }

    return render(request, 'tabulation_report/half_yearly_reports.html', context)


@login_required()
def annualTabulationReportsManagerAPI(request):

    org_data = organizationlst.objects.filter(is_active=True).first()
    
    context = {
        "org_data": org_data
    }

    return render(request, 'tabulation_report/annual_reports.html', context)


@login_required()
def getSectionsByClassManagerAPI(request):
    class_id = request.GET.get("filter_class")
    shifts_id = request.GET.get("filter_shifts")
    groups_id = request.GET.get("filter_groups")
    org_id = request.GET.get("filter_org")
    branch_id = request.GET.get("filter_branch")
    filter_version = request.GET.get("filter_version")   # <-- extra param

    qs = in_registrations.objects.all()

    if class_id:
        qs = qs.filter(class_id=class_id)
    if shifts_id:
        qs = qs.filter(shift_id=shifts_id)
    if groups_id:
        qs = qs.filter(groups_id=groups_id)
    if org_id:
        qs = qs.filter(org_id=org_id)
    if branch_id:
        qs = qs.filter(branch_id=branch_id)

    # 👉 Version filter apply
    if filter_version == "english":
        qs = qs.filter(is_english=True)
    elif filter_version == "bangla":
        qs = qs.filter(is_bangla=True)

    # unique + order by section name
    sections = qs.values(
        "section_id__section_id", "section_id__section_name",
        "shift_id__shift_name", "class_id__class_name",
        "groups_id__groups_name", "org_id__org_name",
        "branch_id__branch_name"
    ).distinct().order_by("section_id__section_name")   # ✅ ordering

    data = list(sections)
    return JsonResponse({"data": data})


# ===================================== tabulation report =====================================
"""
    Returns JSON like:
    {
      "meta": {
        "class_name": "Nine",
        "section_name": "A",
        "shift_name": "Morning",
        "groups_name": "Science",
        "status": "Approved",
        "subjects": [
          {"id": 123, "name": "Bangla -1", "modes": ["MCQ","Written"]},
          {"id": 124, "name": "Bangla -2", "modes": ["MCQ","Written"]},
          ...
        ],
        "mode_order": ["MCQ","Written","MT","Practical","Oral"]
      },
      "rows": [
        {
          "sl": 1,
          "roll_no": "101",
          "full_name": "John Doe",
          "groups_name": "Science",
          "marks": { "<subject_id>": { "MCQ": "30", "Written": "70", ... }, ... }
        },
        ...
      ]
    }
"""

@login_required()
def halfYearlyTabulationReportsAPI(request):
    
    def _to_int(val):
        try:
            return int(val) if str(val).strip() != "" else None
        except (TypeError, ValueError):
            return None

    def _bool_or_none(val):
        if val is None:
            return None
        v = str(val).lower().strip()
        if v in ["true", "1", "yes"]:
            return True
        if v in ["false", "0", "no"]:
            return False
        return None

    params = request.GET
    org_id     = _to_int(params.get('org_id'))
    branch_id  = _to_int(params.get('branch_id'))
    class_id   = _to_int(params.get('class_id'))
    section_id = _to_int(params.get('section_id'))
    shifts_id  = _to_int(params.get('shifts_id'))
    groups_id  = _to_int(params.get('groups_id'))
    year       = _to_int(params.get('year'))
    is_version = (params.get('is_version') or '').lower().strip()

    # ------------------- Marks Data -------------------
    qs = in_result_finalizationdtls.objects.select_related(
        'subject_id', 'def_mode_id', 'reg_id',
        'class_id', 'section_id', 'shifts_id', 'groups_id',
        'org_id', 'branch_id'
    )

    if org_id:      qs = qs.filter(org_id=org_id)
    if branch_id:   qs = qs.filter(branch_id=branch_id)
    if class_id:    qs = qs.filter(class_id=class_id)
    if section_id:  qs = qs.filter(section_id=section_id)
    if shifts_id:   qs = qs.filter(shifts_id=shifts_id)
    if groups_id:   qs = qs.filter(groups_id=groups_id)
    if year:        qs = qs.filter(finalize_year=year)

    if is_version == 'english':
        qs = qs.filter(is_english=True)
    elif is_version == 'bangla':
        qs = qs.filter(is_bangla=True)
        
    # ------------------- Only Half Yearly Exam -------------------
    qs = qs.filter(is_yearly=False, is_half_yearly=True)


    if not qs.exists():
        return JsonResponse({"meta": {"subjects": [], "mode_order": []}, "rows": []})

    # ------------------- Attendance Data -------------------
    att_qs = in_student_attendant.objects.filter(
        attendant_year=year,
        org_id=org_id,
        branch_id=branch_id,
        class_id=class_id,
        section_id=section_id,
        shifts_id=shifts_id,
        is_half_yearly=True
    )
    if groups_id is not None:
        att_qs = att_qs.filter(Q(groups_id=groups_id) | Q(groups_id__isnull=True))
    if is_version == 'english':
        att_qs = att_qs.filter(is_english=True)
    elif is_version == 'bangla':
        att_qs = att_qs.filter(is_bangla=True)

    # Max working days
    working_days = att_qs.aggregate(max_days=Max("working_days"))["max_days"] or 0

    # Attendance details
    attdtl_qs = in_student_attendantdtls.objects.filter(
        attendant_year=year,
        org_id=org_id,
        branch_id=branch_id,
        class_id=class_id,
        section_id=section_id,
        shifts_id=shifts_id,
        is_half_yearly=True
    )
    if groups_id is not None:
        attdtl_qs = attdtl_qs.filter(Q(groups_id=groups_id) | Q(groups_id__isnull=True))
    if is_version == 'english':
        attdtl_qs = attdtl_qs.filter(is_english=True)
    elif is_version == 'bangla':
        attdtl_qs = attdtl_qs.filter(is_bangla=True)

    attendance_map = {a.reg_id_id: a.attendant_qty for a in attdtl_qs}

    # ------------------- Subjects -------------------
    subject_qs = in_subjects.objects.annotate(
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
    ).order_by('-is_numeric', 'subjects_as_int', 'subjects_no')
    subject_order = [s.pk for s in subject_qs]

    # ------------------- Students -------------------
    qs = qs.annotate(
        is_numeric=Case(
            When(roll_no__regex=r'^\d+$', then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        ),
        roll_as_int=Case(
            When(roll_no__regex=r'^\d+$', then=Cast('roll_no', IntegerField())),
            default=Value(999999999),
            output_field=IntegerField(),
        )
    ).order_by('-is_numeric', 'roll_as_int', 'roll_no')

    subject_map = OrderedDict()
    subject_modes = defaultdict(OrderedDict)
    mode_preference = ["MCQ", "WR", "MT", "PR", "Oral", "Viva"]

    students = {}
    for row in qs:
        subj = row.subject_id
        mode = row.def_mode_id
        reg = row.reg_id
        subject_id = subj.pk if subj else None
        subject_name = getattr(subj, 'short_name', None) or getattr(subj, 'subjects_name', None) or getattr(subj, 'name', None) or f"Subject-{subject_id}"
        mode_name = getattr(mode, 'short_name', None) or getattr(mode, 'is_mode_name', None) or getattr(mode, 'name', None) or f"Mode-{mode.pk}"

        if subject_id not in subject_map:
            subject_map[subject_id] = subject_name
        if mode_name not in subject_modes[subject_id]:
            subject_modes[subject_id][mode_name] = True

        roll_no = row.roll_no or ""
        full_name = getattr(reg, 'full_name', None) or getattr(reg, 'student_name', None) or "Unknown"
        groups_name = row.groups_name or getattr(row.groups_id, 'name', None) or "N/A"

        if reg.pk not in students:
            students[reg.pk] = {
                "roll_no": roll_no,
                "full_name": full_name,
                "groups_name": groups_name,
                "marks": defaultdict(dict),
                "attendant_qty": attendance_map.get(reg.pk, 0),
            }

        is_absent = (row.is_absent_present is False) if hasattr(row, 'is_absent_present') else False
        val = "A" if is_absent else ("" if row.is_actual_marks is None else (int(row.is_actual_marks) if float(row.is_actual_marks).is_integer() else float(row.is_actual_marks)))
        students[reg.pk]["marks"][subject_id][mode_name] = val
        
    # ------------------- Sort Modes -------------------
    # Load mode order from defaults_exam_modes table
    mode_order_map = {
        m.short_name or m.is_mode_name: m.order_by
        for m in defaults_exam_modes.objects.filter(is_active=True).order_by('order_by')
    }

    # ------------------- Sort Modes -------------------
    def sort_modes(modes):
        return sorted(modes, key=lambda m: (mode_order_map.get(m, 999), m.lower()))

    subjects_meta = []
    for sid in subject_order:
        if sid in subject_map:
            modes = list(subject_modes[sid].keys())
            subjects_meta.append({"id": sid, "name": subject_map[sid], "modes": sort_modes(modes)})

    # ------------------- Build Rows -------------------
    rows = []
    for sl, (reg_id, st) in enumerate(students.items(), start=1):
        row = {
            "sl": sl,
            "roll_no": st["roll_no"],
            "full_name": st["full_name"],
            "groups_name": st["groups_name"],
            "marks": {str(sid): {m: st["marks"].get(sid, {}).get(m, "") for m in subj["modes"]} for subj in subjects_meta for sid in [subj["id"]]},
            "attendant_qty": st["attendant_qty"],
        }
        rows.append(row)

    first_row = qs.first()
    class_name = first_row.class_name or getattr(first_row.class_id, 'name', None) or ""
    section_name = first_row.section_name or getattr(first_row.section_id, 'name', None) or ""
    shift_name = first_row.shift_name or getattr(first_row.shifts_id, 'name', None) or ""
    groups_name = first_row.groups_name or getattr(first_row.groups_id, 'name', None) or ""
    status = "Approved" if first_row.is_approved else "Draft"

    return JsonResponse({
        "meta": {
            "class_name": class_name,
            "section_name": section_name,
            "shift_name": shift_name,
            "groups_name": groups_name,
            "status": status,
            "subjects": subjects_meta,
            "mode_order": mode_preference,
            "working_days": working_days,
        },
        "rows": rows,
    }, safe=False)
    

@login_required()
def annualTabulationdetailsReportsAPI(request):
    
    def _to_int(val):
        try:
            return int(val) if str(val).strip() != "" else None
        except (TypeError, ValueError):
            return None

    def _bool_or_none(val):
        if val is None:
            return None
        v = str(val).lower().strip()
        if v in ["true", "1", "yes"]:
            return True
        if v in ["false", "0", "no"]:
            return False
        return None

    params = request.GET
    org_id     = _to_int(params.get('org_id'))
    branch_id  = _to_int(params.get('branch_id'))
    class_id   = _to_int(params.get('class_id'))
    section_id = _to_int(params.get('section_id'))
    shifts_id  = _to_int(params.get('shifts_id'))
    groups_id  = _to_int(params.get('groups_id'))
    year       = _to_int(params.get('year'))
    is_version = (params.get('is_version') or '').lower().strip()

    # ------------------- Marks Data -------------------
    qs = in_result_finalizationdtls.objects.select_related(
        'subject_id', 'def_mode_id', 'reg_id',
        'class_id', 'section_id', 'shifts_id', 'groups_id',
        'org_id', 'branch_id'
    )

    if org_id:      qs = qs.filter(org_id=org_id)
    if branch_id:   qs = qs.filter(branch_id=branch_id)
    if class_id:    qs = qs.filter(class_id=class_id)
    if section_id:  qs = qs.filter(section_id=section_id)
    if shifts_id:   qs = qs.filter(shifts_id=shifts_id)
    if groups_id:   qs = qs.filter(groups_id=groups_id)
    if year:        qs = qs.filter(finalize_year=year)

    if is_version == 'english':
        qs = qs.filter(is_english=True) 
    elif is_version == 'bangla':
        qs = qs.filter(is_bangla=True)
        
    # ------------------- Only Annual Exam -------------------
    qs = qs.filter(is_yearly=True, is_half_yearly=False)

    if not qs.exists():
        return JsonResponse({"meta": {"subjects": [], "mode_order": []}, "rows": []})

    # ------------------- Attendance Data -------------------
    att_qs = in_student_attendant.objects.filter(
        attendant_year=year,
        org_id=org_id,
        branch_id=branch_id,
        class_id=class_id,
        section_id=section_id,
        shifts_id=shifts_id,
        is_yearly=True
    )
    if groups_id is not None:
        att_qs = att_qs.filter(Q(groups_id=groups_id) | Q(groups_id__isnull=True))
    if is_version == 'english':
        att_qs = att_qs.filter(is_english=True)
    elif is_version == 'bangla':
        att_qs = att_qs.filter(is_bangla=True)

    # Max working days
    working_days = att_qs.aggregate(max_days=Max("working_days"))["max_days"] or 0

    # Attendance details
    attdtl_qs = in_student_attendantdtls.objects.filter(
        attendant_year=year,
        org_id=org_id,
        branch_id=branch_id,
        class_id=class_id,
        section_id=section_id,
        shifts_id=shifts_id,
        is_yearly=True
    )
    if groups_id is not None:
        attdtl_qs = attdtl_qs.filter(Q(groups_id=groups_id) | Q(groups_id__isnull=True))
    if is_version == 'english':
        attdtl_qs = attdtl_qs.filter(is_english=True)
    elif is_version == 'bangla':
        attdtl_qs = attdtl_qs.filter(is_bangla=True)

    attendance_map = {a.reg_id_id: a.attendant_qty for a in attdtl_qs}

    # ------------------- Subjects -------------------
    subject_qs = in_subjects.objects.annotate(
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
    ).order_by('-is_numeric', 'subjects_as_int', 'subjects_no')
    subject_order = [s.pk for s in subject_qs]

    # ------------------- Students -------------------
    qs = qs.annotate(
        is_numeric=Case(
            When(roll_no__regex=r'^\d+$', then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        ),
        roll_as_int=Case(
            When(roll_no__regex=r'^\d+$', then=Cast('roll_no', IntegerField())),
            default=Value(999999999),
            output_field=IntegerField(),
        )
    ).order_by('-is_numeric', 'roll_as_int', 'roll_no')

    subject_map = OrderedDict()
    subject_modes = defaultdict(OrderedDict)
    mode_preference = ["MCQ", "WR", "MT", "PR", "Oral", "Viva"]

    students = {}
    for row in qs:
        subj = row.subject_id
        mode = row.def_mode_id
        reg = row.reg_id
        subject_id = subj.pk if subj else None
        subject_name = getattr(subj, 'short_name', None) or getattr(subj, 'subjects_name', None) or getattr(subj, 'name', None) or f"Subject-{subject_id}"
        mode_name = getattr(mode, 'short_name', None) or getattr(mode, 'is_mode_name', None) or getattr(mode, 'name', None) or f"Mode-{mode.pk}"

        if subject_id not in subject_map:
            subject_map[subject_id] = subject_name
        if mode_name not in subject_modes[subject_id]:
            subject_modes[subject_id][mode_name] = True

        roll_no = row.roll_no or ""
        full_name = getattr(reg, 'full_name', None) or getattr(reg, 'student_name', None) or "Unknown"
        groups_name = row.groups_name or getattr(row.groups_id, 'name', None) or "N/A"

        if reg.pk not in students:
            students[reg.pk] = {
                "roll_no": roll_no,
                "full_name": full_name,
                "groups_name": groups_name,
                "marks": defaultdict(dict),
                "attendant_qty": attendance_map.get(reg.pk, 0),
            }

        is_absent = (row.is_absent_present is False) if hasattr(row, 'is_absent_present') else False
        val = "A" if is_absent else ("" if row.is_actual_marks is None else (int(row.is_actual_marks) if float(row.is_actual_marks).is_integer() else float(row.is_actual_marks)))
        students[reg.pk]["marks"][subject_id][mode_name] = val
        
    # ------------------- Sort Modes -------------------
    # Load mode order from defaults_exam_modes table
    mode_order_map = {
        m.short_name or m.is_mode_name: m.order_by
        for m in defaults_exam_modes.objects.filter(is_active=True).order_by('order_by')
    }

    # ------------------- Sort Modes -------------------
    def sort_modes(modes):
        return sorted(modes, key=lambda m: (mode_order_map.get(m, 999), m.lower()))

    subjects_meta = []
    for sid in subject_order:
        if sid in subject_map:
            modes = list(subject_modes[sid].keys())
            subjects_meta.append({"id": sid, "name": subject_map[sid], "modes": sort_modes(modes)})

    # ------------------- Build Rows -------------------
    rows = []
    for sl, (reg_id, st) in enumerate(students.items(), start=1):
        row = {
            "sl": sl,
            "roll_no": st["roll_no"],
            "full_name": st["full_name"],
            "groups_name": st["groups_name"],
            "marks": {str(sid): {m: st["marks"].get(sid, {}).get(m, "") for m in subj["modes"]} for subj in subjects_meta for sid in [subj["id"]]},
            "attendant_qty": st["attendant_qty"],
        }
        rows.append(row)

    first_row = qs.first()
    class_name = first_row.class_name or getattr(first_row.class_id, 'name', None) or ""
    section_name = first_row.section_name or getattr(first_row.section_id, 'name', None) or ""
    shift_name = first_row.shift_name or getattr(first_row.shifts_id, 'name', None) or ""
    groups_name = first_row.groups_name or getattr(first_row.groups_id, 'name', None) or ""
    status = "Approved" if first_row.is_approved else "Draft"

    return JsonResponse({
        "meta": {
            "class_name": class_name,
            "section_name": section_name,
            "shift_name": shift_name,
            "groups_name": groups_name,
            "status": status,
            "subjects": subjects_meta,
            "mode_order": mode_preference,
            "working_days": working_days,
        },
        "rows": rows,
    }, safe=False)