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
            "roll_no": display_roll_no,      # original দেখাবো
            "roll_no_val": roll_no_val,      # sort করার জন্য numeric
            "roll_no_suffix": roll_no_suffix,# suffix sort এর জন্য
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

        # Fail count
        fail_count = 0
        for sid in all_subjects_meta.keys():
            if is_subject_failed(regid, sid):
                fail_count += 1
        row["fail_subject_count"] = fail_count

        results.append(row)

    # # =========================
    # # 5) Sorting Key (same as before)
    # # =========================
    # def base_tie_segments(r):
    #     segs = []
    #     if sub_group_subjects:
    #         segs.append(-r["subjects"].get("Tot Group Marks", 0))
    #     else:
    #         segs.append(0)

    #     # Subject-wise tie break
    #     for s in normal_subjects:
    #         sub_name = s["subjects_id__subjects_name"]
    #         segs.append(-r["subjects"].get(sub_name, 0))

    #     # Roll no always last → integer form
    #     segs.append(int(re.findall(r'\d+', r["roll_no"])[0]) if re.findall(r'\d+', r["roll_no"]) else 99999)
    #     return segs

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