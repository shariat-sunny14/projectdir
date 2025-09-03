import re
from django.db.models.functions import Cast
from django.db.models import Q, Sum, IntegerField, Value, Case, When, F
from audioop import reverse
from datetime import datetime
from django.utils.timezone import now
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, Http404
from django.contrib import messages
from django.db import transaction, IntegrityError
from defaults_exam_mode.models import defaults_exam_modes, in_letter_gradeFiftyMap, in_letter_gradeHundredMap
from exam_type.models import in_exam_type
from merit_app_card_print.models import in_merit_position_approval, in_merit_position_approvaldtls
from organizations.models import branchslist, organizationlst
from class_setup.models import in_class
from groups_setup.models import in_groups
from policy_setup.models import classSectionGroupingMap, in_class_wise_merit_policy, in_subject_wise_merit_policy
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
User = get_user_model()


@login_required()
def meritPositionAppAndCardPrintManagerAPI(request):
    
    return render(request, 'merit_pos_app_card_print/results_card_print_list.html')

@login_required()
def meritPositionApprovalManagerAPI(request):
    
    examtypelist = in_exam_type.objects.filter(is_active=True).filter(Q(is_half_yearly=True) | Q(is_yearly=True))

    return render(request, 'merit_pos_app_card_print/merit_position_approve.html', {'examtypelist': examtypelist})


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

    # Normalize incoming section_ids: handle comma string or list, convert to ints, remove duplicates
    if len(section_ids) == 1 and section_ids[0] and "," in section_ids[0]:
        section_ids = section_ids[0].split(",")
    section_ids = [int(s) for s in section_ids if s and str(s).isdigit()]
    section_ids = list(dict.fromkeys(section_ids))  # preserve order but unique

    # ==============================
    # 🔹 Check already created data
    # ==============================
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

    # =========================
    # 1) Subject Wise Policy
    # =========================
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

    # =========================
    # 2) Base Student Data (filtered set used for display & ranking)
    # =========================
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

    card_qs = in_results_card_entry.objects.filter(**card_filters)
    if year:
        card_qs = card_qs.filter(create_date=year)

    # include section_id for grouping mapping
    card_qs = card_qs.values(
        "reg_id",
        "reg_id__roll_no",
        "reg_id__full_name",
        "is_average_gpa",
        "total_obtained_marks",
        "section_id",
        "section_id__section_name"
    )

    # =========================
    # 3) Subject Marks (and per-mode data)
    # =========================
    fin_filters = {
        "org_id": org_id,
        "branch_id": branch_id,
        "class_id": class_id,
        "shifts_id": shift_id,
        "finalize_year": year,
        "is_english": (version == "english"),
        "is_bangla": (version == "bangla"),
        "exam_type_id": exam_type_id,
        "is_half_yearly": is_half_year,
        "is_yearly": is_yearly,
        "is_approved": True,
    }
    if section_ids:
        fin_filters["section_id__in"] = section_ids
    if group_id:
        fin_filters["groups_id"] = group_id
    else:
        fin_filters["groups_id__isnull"] = True

    fin_qs = in_result_finalizationdtls.objects.filter(**fin_filters).select_related("subject_id")

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

    # =========================
    # 3c) All subjects metadata (for fail count calculation)
    # =========================
    all_subjects_qs = in_subjects.objects.filter(class_id=class_id).values(
        "subjects_id", "subjects_name", "is_marks", "is_pass_marks", "is_applicable_pass_marks", "is_not_countable"
    )
    all_subjects_meta = {
        x["subjects_id"]: {
            "full_marks": x["is_marks"],
            "pass_marks": float(x["is_pass_marks"] or 0.0),
            "is_applicable_pass_marks": bool(x["is_applicable_pass_marks"]),
            "is_not_countable": bool(x["is_not_countable"]),
            "name": x["subjects_name"]
        }
        for x in all_subjects_qs
    }

    # =========================
    # 4) Combine Student Rows (+ Fail Count)
    # =========================
    policy = in_class_wise_merit_policy.objects.filter(
        org_id=org_id,
        class_id=class_id,
        is_english=(version == "english"),
        is_bangla=(version == "bangla"),
    ).first()

    use_fail_count = bool(policy and policy.is_fail_sub_count)
    use_gross = bool(policy and policy.is_gross_merit_position)

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
                if float(actual) < float(p):   # যদি কোনো mode fail করে
                    return True

        return False

    results = []
    display_subjects = (sub_group_subjects + normal_subjects)

    for c in card_qs:
        regid = c["reg_id"]
        section_id_val = c.get("section_id")
        
        # --- Roll no handling ---
        roll_no_raw = str(c.get("reg_id__roll_no") or "")
        # Numeric part
        roll_no_digits = re.findall(r'\d+', roll_no_raw)
        roll_no_val = int(roll_no_digits[0]) if roll_no_digits else 99999
        # Non-digit suffix
        roll_no_suffix_match = re.findall(r'\D+', roll_no_raw)
        roll_no_suffix = roll_no_suffix_match[0].strip("()") if roll_no_suffix_match else ""
        # Display roll_no as original format
        display_roll_no = str(roll_no_val)
        if roll_no_suffix:
            display_roll_no += f"({roll_no_suffix})"
        
        row = {
            "reg_id": regid,
            "roll_no": display_roll_no,
            "full_name": c["reg_id__full_name"],
            "is_average_gpa": float(c["is_average_gpa"] or 0.0),
            "total_obtained_marks": float(c["total_obtained_marks"] or 0.0),
            "subjects": {},
            "section": c.get("section_id__section_name", ""),
            "section_id": section_id_val
        }

        # Populate marks for policy display subjects
        for s in display_subjects:
            sid = s["subjects_id"]
            sname = s["subjects_id__subjects_name"]
            row["subjects"][sname] = marks_map.get(regid, {}).get(sid, 0)

        if sub_group_subjects:
            subgroup_total = sum(marks_map.get(regid, {}).get(s["subjects_id"], 0) for s in sub_group_subjects)
            row["subjects"]["Tot Group Marks"] = subgroup_total

        # Fail count using all_subjects_meta
        fail_count = 0
        for sid in all_subjects_meta.keys():
            if is_subject_failed(regid, sid):
                fail_count += 1
        row["fail_subject_count"] = fail_count

        results.append(row)

    # =========================
    # 5) Sorting Key (same as before)
    # =========================
    def base_tie_segments(r):
        segs = []
        if sub_group_subjects:
            segs.append(-r["subjects"].get("Tot Group Marks", 0))
        else:
            segs.append(0)
        for s in normal_subjects:
            sub_name = s["subjects_id__subjects_name"]
            segs.append(-r["subjects"].get(sub_name, 0))
        segs.append(r["roll_no"])
        return segs

    def combined_sort_key(r):
        if use_fail_count and float(r["is_average_gpa"]) == 0.0:
            key = [
                r.get("fail_subject_count", 0),
                -r["total_obtained_marks"],
            ]
            key.extend(base_tie_segments(r))
            return tuple(key)
        else:
            key = [
                -r["is_average_gpa"],
                -r["total_obtained_marks"],
            ]
            key.extend(base_tie_segments(r))
            return tuple(key)

    # =========================
    # 6) Merit position assignment
    # =========================
    if not use_gross:
        results.sort(key=combined_sort_key)
        merit_pos = 1
        prev_key = None
        for i, r in enumerate(results, start=1):
            curr_key = combined_sort_key(r)
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
            group_students.sort(key=combined_sort_key)
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

    # =========================
    # 7) Prepare Subject List (UI headers)
    # =========================
    subjects = []
    subjects.extend(sub_group_subjects)
    if sub_group_subjects:
        subjects.append({"subjects_id": None, "subjects_id__subjects_name": "Tot Group Marks", "subject_priority": 9998})
    subjects.extend(normal_subjects)

    # =========================
    # 8) Final sort by merit_position ascending
    # =========================
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
            reg_ids = request.POST.getlist('reg_id[]')
            merit_positions = request.POST.getlist('merit_position[]')

            for roll_no, reg_id, merit_pos in zip(roll_nos, reg_ids, merit_positions):
                in_merit_position_approvaldtls.objects.create(
                    merit_id=approval,
                    reg_id_id=reg_id,
                    roll_no=roll_no,
                    merit_position=int(merit_pos),
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
    org_id = request.GET.get("org_id")
    branch_id = request.GET.get("branch_id")
    year = request.GET.get("year")
    version = request.GET.get("version")  # english/bangla

    qs = in_merit_position_approval.objects.all()

    if org_id:
        qs = qs.filter(org_id_id=org_id)
    if branch_id:
        qs = qs.filter(branch_id_id=branch_id)
    if year:
        qs = qs.filter(merit_year=year)
    if version:
        if version.lower() == "english":
            qs = qs.filter(is_english=True)
        elif version.lower() == "bangla":
            qs = qs.filter(is_bangla=True)

    data = []
    for obj in qs:
        sections = ", ".join([s.section_name for s in obj.section_id.all()]) if obj.section_id.exists() else "-"
        section_ids = [s.section_id for s in obj.section_id.all()] if obj.section_id.exists() else []
        
        # related_name = "merit_id2merit_positiondtls"
        reg_ids = [d.reg_id.reg_id for d in obj.merit_id2merit_positiondtls.all() if d.reg_id]
        
        data.append({
            "merit_id": obj.merit_id,
            "created_date": obj.created_date.strftime("%Y-%m-%d") if obj.created_date else "",
            "class_id": obj.class_id.class_id if obj.class_id else "",
            "class_name": obj.class_id.class_name if obj.class_id else "",
            "sections": sections,
            "section_ids": section_ids,
            "reg_ids": reg_ids,
            "shift": obj.shifts_id.shift_name if obj.shifts_id else "",
            "shift_id": obj.shifts_id.shift_id if obj.shifts_id else "",
            "groups": obj.groups_id.groups_name if obj.groups_id else "",
            "groups_id": obj.groups_id.groups_id if obj.groups_id else "",
            "approved_date": obj.approved_date or "",
            "approved_by": obj.is_approved_by.username if obj.is_approved_by else "",
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