import json
from django.utils import timezone
from collections import defaultdict
from django.db.models import Q, Sum, IntegerField, Value, Case, When, F, Prefetch, Max
from audioop import reverse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, Http404
from django.contrib import messages
from django.db.models.functions import Cast
from django.db import transaction, IntegrityError
from class_setup.models import in_class
from defaults_exam_mode.models import ExamModeTypeMap, defaults_exam_modes, in_letter_grade_mode, in_letter_gradeFiftyMap, in_letter_gradeHundredMap
from exam_type.models import in_exam_type
from groups_setup.models import in_groups
from half_yearly_roll_sec_change.models import in_half_yearly_roll_sec_change_history, in_half_yearly_roll_sec_change_info, in_half_yearly_rollsecchange_rollback_history
from merit_app_card_print.models import in_merit_position_approval, in_merit_position_approvaldtls
from organizations.models import organizationlst
from policy_setup.models import classSectionGroupingMap, half_year_roll_section_change_policy, in_class_wise_merit_policy, in_subject_wise_merit_policy
from registrations.models import in_registrations
from section_setup.models import in_section
from shift_setup.models import in_shifts
from subject_setup.models import in_subjects
from django.contrib.auth import get_user_model

from user_setup.models import access_list
User = get_user_model()


@login_required()
def halfYearlyRollSecChangeListManagerAPI(request):
    
    return render(request, 'half_yearly_roll_sec_change/half_yearly_roll_sec_change_list.html')

@login_required()
def halfYearlyRollSecChangingManagerAPI(request):
    
    return render(request, 'half_yearly_roll_sec_change/half_yearly_roll_sec_changing.html')


@login_required()
def halfYearlyRollSecChangeRollbackListManagerAPI(request):
    
    return render(request, 'half_yearly_roll_sec_change/half_yearly_roll_section_rollback_list.html')


@login_required()
def halfYearlyRollSecChangingRollBackManagerAPI(request):
    
    return render(request, 'half_yearly_roll_sec_change/half_yearly_roll_sec_changing_rollback.html')

# report view
@login_required()
def ReportHalfYearlyRollSecChangeAPI(request):
    
    return render(request, 'half_yearly_roll_sec_change/report_half_yearly_roll_sec_change.html')

# rollback history list view
@login_required()
def halfYearlyRollSecChangeRollbackHistoryListAPI(request):
    
    return render(request, 'half_yearly_roll_sec_change/half_yearly_roll_section_rollback_history_list.html')


# rollback history report view
@login_required()
def reportHalfYearlyRollSecChangeRollbackHistoryAPI(request):
    
    return render(request, 'half_yearly_roll_sec_change/report_rollback_history_half_yearly_roll_sec_change.html')

@login_required            
def getMeritApprovalsForHYRSCListManagerAPI(request):
    org_id = request.GET.get("org_id")
    branch_id = request.GET.get("branch_id")
    class_id = request.GET.get("class_id")
    shift_id = request.GET.get("shift_id")
    groups_id = request.GET.get("groups_id")
    year = request.GET.get("year")
    version = request.GET.get("version")  # english/bangla

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
            "reg_ids_by_section": reg_ids_by_section,  # ✅ integer IDs, grouped by section
            "shift": obj.shifts_id.shift_name if obj.shifts_id else "",
            "shift_id": obj.shifts_id.shift_id if obj.shifts_id else "",
            "groups": obj.groups_id.groups_name if obj.groups_id else "",
            "groups_id": obj.groups_id.groups_id if obj.groups_id else "",
            "is_half_roll_sec_change": obj.is_half_roll_sec_change or "",
            "is_half_roll_sec_change_date": obj.is_half_roll_sec_change_date or "",
            "is_half_roll_sec_change_by": obj.is_half_roll_sec_change_by.username if obj.is_half_roll_sec_change_by else "",
        })

    return JsonResponse({"data": data})


@login_required()
def getMeritPositionDetailsForHalfYearlyRollSecChangeAPI(request):
    merit_id = request.GET.get("merit_id")
    org_id = request.GET.get("org_id")
    year = request.GET.get("year")
    version = request.GET.get("version")
    class_id = request.GET.get("class_id")
    shift_id = request.GET.get("shift_id")
    group_id = request.GET.get("group_id")
    section_ids_str = request.GET.get("section_ids")  # optional comma-separated

    # parse section_ids (if provided)
    try:
        section_ids = [int(s.strip()) for s in (section_ids_str or "").split(",") if s.strip()]
    except ValueError:
        section_ids = []

    if not merit_id:
        return JsonResponse({"success": False, "message": "Merit ID missing!"}, status=400)

    # -------------------
    # fetch merit header
    # -------------------
    try:
        merit_obj = (
            in_merit_position_approval.objects
            .select_related("org_id", "branch_id", "class_id", "shifts_id", "groups_id")
            .prefetch_related("section_id")
            .get(merit_id=merit_id)
        )
    except in_merit_position_approval.DoesNotExist:
        return JsonResponse({"success": False, "message": "Invalid Merit ID!"}, status=404)

    # -------------------
    # fetch merit details (students) ordered by merit_position
    # -------------------
    dtls_qs = (
        in_merit_position_approvaldtls.objects
        .filter(merit_id__merit_id=merit_id)
        .select_related("reg_id__class_id", "reg_id__section_id", "reg_id__shift_id", "reg_id__groups_id")
        .order_by("merit_position")
    )

    # -------------------
    # determine version flags
    # -------------------
    is_english = bool(version and version.lower() == "english")
    is_bangla = bool(version and version.lower() == "bangla")

    # -------------------
    # fetch policies matching header filters
    # -------------------
    policy_qs = half_year_roll_section_change_policy.objects.filter(
        org_id__org_id=org_id,
        hyrscp_year=year,
        class_id__class_id=class_id,
        shift_id__shift_id=shift_id,
        is_english=is_english,
        is_bangla=is_bangla,
    )

    # optional groups filter (if provided)
    if group_id:
        policy_qs = policy_qs.filter(groups_id__groups_id=group_id)

    # optional section filter (if provided)
    if section_ids:
        policy_qs = policy_qs.filter(section_id__section_id__in=section_ids)

    if not policy_qs.exists():
        return JsonResponse({
            "success": False,
            "message": "Half Yearly Section Roll Changing Policy Not Found for selected filters."
        })

    # bring policies into memory for processing
    policies = list(policy_qs.select_related("section_id"))

    # -------------------
    # priority: invd policy (all -> one section)
    # -------------------
    invd_policy = next((p for p in policies if p.is_invd_flag), None)
    if invd_policy:
        fixed_section_id = getattr(invd_policy.section_id, "section_id", None)
        fixed_section_name = getattr(invd_policy.section_id, "section_name", "")
    else:
        fixed_section_id = None
        fixed_section_name = ""

    # -------------------
    # group policies processing:
    # Build mapping: group_serial -> list of (from_roll,to_roll, section)
    # -------------------
    group_map = defaultdict(list)   # key -> list of dict{f,t,section_id,section_name,policy_obj}
    for p in policies:
        if not p.is_group_flag:
            continue
        key = (p.group_serials or "").strip()
        # try parse numeric range; if missing or invalid, skip the range record
        try:
            f = int(p.from_roll) if p.from_roll is not None and str(p.from_roll).strip() != "" else None
            t = int(p.to_roll) if p.to_roll is not None and str(p.to_roll).strip() != "" else None
        except ValueError:
            f = t = None

        group_map[key].append({
            "from_roll": f,
            "to_roll": t,
            "section_id": getattr(p.section_id, "section_id", None),
            "section_name": getattr(p.section_id, "section_name", ""),
            "policy": p
        })

    # Normalize: sort intervals per group by from_roll (if present)
    for key in list(group_map.keys()):
        group_map[key] = sorted(group_map[key], key=lambda x: (x["from_roll"] if x["from_roll"] is not None else -1))

    # -------------------
    # For deterministic behavior: sort group keys (so same order every request)
    # -------------------
    sorted_group_keys = sorted(group_map.keys(), key=lambda k: (k if k != "" else "0"))

    # -------------------
    # Now build student data applying policy logic
    # -------------------
    student_data = []
    for sl, d in enumerate(dtls_qs, start=1):
        reg = d.reg_id
        
        # ----------------------------
        # Restriction Flag Check
        # ----------------------------
        restriction_fields = [
            "is_transferred", "is_promoted_passed_out", "is_fail_removed",
            "is_lack_of_attendance", "is_rusticated", "is_expelled",
            "is_misbehavior", "is_policy_violation", "is_family_shift",
            "is_financial_problem", "is_personal_health_problem",
            "is_family_decision", "is_court_ordered", "is_government_directive",
            "is_death", "is_missing", "is_admission_cancelled",
            "is_unauthorized_absent"
        ]

        # যদি যেকোনো একটি flag True হয় → skip this student
        if any(getattr(reg, field, False) for field in restriction_fields):
            continue
        # ----------------------------
        
        cur_section_name = getattr(reg.section_id, "section_name", "") if reg and reg.section_id else ""
        cur_section_id = getattr(reg.section_id, "section_id", None) if reg and reg.section_id else None
        merit_pos = int(d.merit_position or 0)

        new_section_name = cur_section_name
        new_section_id = cur_section_id
        new_roll_no = merit_pos  # default new roll = merit_position

        # if invd policy exists -> assign fixed section for everyone
        if invd_policy:
            new_section_name = fixed_section_name
            new_section_id = fixed_section_id
        else:
            # loop groups and their intervals; first group that has an interval containing merit_pos wins
            matched = False
            for gkey in sorted_group_keys:
                intervals = group_map[gkey]
                for iv in intervals:
                    f = iv["from_roll"]
                    t = iv["to_roll"]
                    # require both f and t to be present for interval matching
                    if f is None or t is None:
                        # skip invalid interval entries
                        continue
                    if f <= merit_pos <= t:
                        new_section_name = iv["section_name"] or new_section_name
                        new_section_id = iv["section_id"] or new_section_id
                        matched = True
                        break
                if matched:
                    break
            # if no match found -> keep current section (as requested)

        student_data.append({
            "sl": sl,
            "reg_id": getattr(reg, "reg_id", "") if reg else "",
            "merit_dtls_id": d.meritdtl_id,
            "full_name": getattr(reg, "full_name", "") if reg else "",
            "roll_no": d.roll_no or "",
            "class_id": getattr(reg.class_id, "class_id", "") if reg and reg.class_id else "",
            "class_name": getattr(reg.class_id, "class_name", "") if reg and reg.class_id else "",
            "section_name": cur_section_name,
            "section_id": cur_section_id,
            "shift_name": getattr(reg.shift_id, "shift_name", "") if reg and reg.shift_id else "",
            "shift_id": getattr(reg.shift_id, "shift_id", "") if reg and reg.shift_id else "",
            "group_id": getattr(reg.groups_id, "groups_id", "") if reg and reg.groups_id else "",
            "group_name": getattr(reg.groups_id, "groups_name", "") if reg and reg.groups_id else "",
            "merit_position": merit_pos,
            "new_section_name": new_section_name,
            "new_section_id": new_section_id,
            "new_roll_no": new_roll_no,
        })

    # -------------------
    # Response
    # -------------------
    return JsonResponse({
        "success": True,
        "header": {
            "merit_id": merit_id,
            "org_id": getattr(merit_obj.org_id, "org_id", ""),
            "org_name": getattr(merit_obj.org_id, "org_name", "") if merit_obj.org_id else "",
            "branch_id": getattr(merit_obj.branch_id, "branch_id", "") if merit_obj.branch_id else "",
            "branch_name": getattr(merit_obj.branch_id, "branch_name", "") if merit_obj.branch_id else "",
            "class_id": getattr(merit_obj.class_id, "class_id", "") if merit_obj.class_id else "",
            "class_name": getattr(merit_obj.class_id, "class_name", "") if merit_obj.class_id else "",
            "shift_id": getattr(merit_obj.shifts_id, "shift_id", "") if merit_obj.shifts_id else "",
            "shift_name": getattr(merit_obj.shifts_id, "shift_name", "") if merit_obj.shifts_id else "",
            "group_id": getattr(merit_obj.groups_id, "groups_id", "") if merit_obj.groups_id else "",
            "group_name": getattr(merit_obj.groups_id, "groups_name", "") if merit_obj.groups_id else "",
            "merit_year": merit_obj.merit_year,
            "is_english": merit_obj.is_english,
            "is_bangla": merit_obj.is_bangla,
        },
        "data": student_data
    })
    
    
@csrf_exempt
@login_required()
def saveHalfYearlyRollSectionChangeManagerAPI(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request method"})

    # ----- Common data -----
    merit_id    = request.POST.get("merit_id")
    org_id      = request.POST.get("filter_org_id")
    branch_id   = request.POST.get("filter_branch_id")
    class_id    = request.POST.get("filter_class_id")
    shift_id    = request.POST.get("filter_shift_id")
    group_id    = request.POST.get("filter_group_id")
    year        = request.POST.get("filter_year")

    version_raw = request.POST.get("filter_version", "").strip().lower()
    is_english  = "english" in version_raw
    is_bangla   = "bangla" in version_raw

    user = request.user

    # ----- Arrays -----
    reg_ids         = request.POST.getlist("reg_id[]")
    class_ids_list  = request.POST.getlist("class_id[]")
    old_section_ids = request.POST.getlist("section_id[]")
    old_rolls       = request.POST.getlist("current_roll_no[]")
    new_section_ids = request.POST.getlist("new_section_id[]")
    new_rolls       = request.POST.getlist("new_roll_no[]")

    if not reg_ids:
        return JsonResponse({"success": False, "message": "No students selected"})

    try:
        with transaction.atomic():
            # Get the record
            merit_id_obj = get_object_or_404(in_merit_position_approval, merit_id=merit_id)

            # Check condition
            if merit_id_obj.is_half_roll_sec_change:
                return JsonResponse({
                    "success": True,
                    "message": "Already Changed! Please Rollback First and Try Again.."
                })

            # ========== 1. Parent create ==========
            parent = in_half_yearly_roll_sec_change_info.objects.create(
                merit_id=merit_id_obj,
                org_id_id=org_id,
                branch_id_id=branch_id,
                class_id_id=class_id,
                shifts_id_id=shift_id,
                groups_id_id=group_id or None,
                hyrscinfo_year=year,
                is_half_yearly=True,
                is_yearly=False,
                is_english=is_english,
                is_bangla=is_bangla,
                is_changed=True,
                is_changed_by=user,
                is_changed_date=timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
                is_created_by=user,
                ss_creator=user,
            )

            # ========== 2. Update merit approval ==========
            if merit_id:
                in_merit_position_approval.objects.filter(merit_id=merit_id).update(
                    is_half_roll_sec_change=True,
                    is_half_roll_sec_change_by=user,
                    is_half_roll_sec_change_date=timezone.now().strftime("%Y-%m-%d %H:%M:%S")
                )

            # ========== 3. PK creation logic ==========
            last_pk = in_half_yearly_roll_sec_change_history.objects.aggregate(m=Max('hyrschistory_id'))['m']
            next_pk = (int(last_pk) + 1) if last_pk else 1479600000001

            last_created = in_half_yearly_roll_sec_change_history.objects.aggregate(m=Max('ss_created_session'))['m']
            next_created_session = (int(last_created) + 1) if last_created else 14700500300000

            last_modified = in_half_yearly_roll_sec_change_history.objects.aggregate(m=Max('ss_modified_session'))['m']
            next_modified_session = (int(last_modified) + 1) if last_modified else 10351076890000

            now = timezone.now()

            # ========== 4. Build history objects ==========
            history_objs = []
            total = len(reg_ids)

            # ⭐⭐ NEW: Prepare list for updating registrations ⭐⭐
            reg_update_list = []

            for i, reg_id in enumerate(reg_ids):
                cls_id     = class_ids_list[i] if i < len(class_ids_list) else class_id
                old_sec_id = old_section_ids[i] if i < len(old_section_ids) else None
                old_roll   = old_rolls[i] if i < len(old_rolls) else None
                new_sec_id = new_section_ids[i] if i < len(new_section_ids) else None
                new_roll   = new_rolls[i] if i < len(new_rolls) else None

                new_sec_id = None if str(new_sec_id or "").strip() in {"", "None"} else int(new_sec_id)
                new_roll   = None if str(new_roll   or "").strip() in {"", "None"} else new_roll
                old_sec_id = None if str(old_sec_id or "").strip() in {"", "None"} else int(old_sec_id)
                old_roll   = None if str(old_roll   or "").strip() in {"", "None"} else old_roll

                # ⭐⭐ push update data for registrations table ⭐⭐
                if new_sec_id or new_roll:
                    reg_update_list.append((reg_id, new_sec_id, new_roll))

                history_objs.append(
                    in_half_yearly_roll_sec_change_history(
                        hyrschistory_id=next_pk + i,
                        hyrscinfo_id=parent,
                        org_id_id=org_id,
                        branch_id_id=branch_id,
                        class_id_id=cls_id,
                        shifts_id_id=shift_id,
                        groups_id_id=group_id or None,
                        reg_id_id=reg_id,
                        hyrscinfo_year=year,
                        is_half_yearly=True,
                        is_english=is_english,
                        is_bangla=is_bangla,
                        old_section_id_id=old_sec_id,
                        new_section_id_id=new_sec_id,
                        old_roll_no=old_roll,
                        new_roll_no=new_roll,
                        ss_creator=user,
                        ss_created_on=now,
                        ss_created_session=next_created_session + i,
                        ss_modified_on=now,
                        ss_modified_session=next_modified_session + i,
                    )
                )

            # ========== 5. Bulk create ==========            
            batch_size = min(1500, max(total, 1000))
            in_half_yearly_roll_sec_change_history.objects.bulk_create(history_objs, batch_size=batch_size)

            # ===============================================================================
            # 6. UPDATE in_registrations TABLE
            # ===============================================================================
            for reg_id, sec_id, roll_no in reg_update_list:
                in_registrations.objects.filter(reg_id=reg_id).update(
                    section_id_id=sec_id,
                    roll_no=roll_no,
                    ss_modifier=user,
                    ss_modified_on=now,
                    ss_modified_session=F('ss_modified_session') + 1
                )
            # ===============================================================================

        return JsonResponse({"success": True, "message": f"Saved {total} records successfully!"})

    except Exception as e:
        return JsonResponse({"success": False, "message": f"Save failed: {str(e)}"})
    
 
# ============================================================================
# rollback list view
# ============================================================================
@login_required()
def getHalfYearlyRollSecChangeRollbacklistAPI(request):
    try:
        user = request.user
        org_id = request.GET.get("org_id")
        branch_id = request.GET.get("branch_id")
        class_id = request.GET.get("class_id")
        shift_id = request.GET.get("shift_id")
        groups_id = request.GET.get("groups_id")
        year = request.GET.get("year")
        version = request.GET.get("version")
        
        # ACCESS PERMISSION CHECK
        has_access = access_list.objects.filter(
            user_id=user,
            feature_id__feature_page_link='HLFYRLYSECRCHROLLBACKBTNACC',
            is_active=True
        ).exists()

        # ====== FILTERING ======
        filters = {}
        if org_id:
            filters["org_id_id"] = org_id
        if branch_id:
            filters["branch_id_id"] = branch_id
        if class_id:
            filters["class_id_id"] = class_id
        if shift_id:
            filters["shifts_id_id"] = shift_id
        if groups_id:
            filters["groups_id_id"] = groups_id
        if year:
            filters["hyrscinfo_year"] = year
        if version:
            if version.lower() == "english":
                filters["is_english"] = True
            elif version.lower() == "bangla":
                filters["is_bangla"] = True

        # ====== QUERY MAIN TABLE ======
        info_list = in_half_yearly_roll_sec_change_info.objects.filter(
            **filters,
            is_changed=True,
            is_rollback=False
        ).order_by("hyrscinfo_id")

        result = []

        # ====== BUILD RESPONSE WITH HISTORY DATA ======
        for row in info_list:

            # FETCH ALL old_section_id FOR THIS hyrscinfo_id
            history_qs = in_half_yearly_roll_sec_change_history.objects.filter(
                hyrscinfo_id=row.hyrscinfo_id
            ).select_related("old_section_id")

            # MULTIPLE OLD SECTION IDs POSSIBLE
            old_sections = []
            for h in history_qs:
                if h.old_section_id:
                    old_sections.append({
                        "section_id": h.old_section_id.section_id,
                        "section_name": h.old_section_id.section_name
                    })

            result.append({
                "hyrscinfo_id": row.hyrscinfo_id,
                "merit_id": row.merit_id.merit_id if row.merit_id else "",
                "org_id": row.org_id.org_name if row.org_id else "",
                "branch_id": row.branch_id.branch_name if row.branch_id else "",
                "class_id": row.class_id.class_name if row.class_id else "",
                "shift_id": row.shifts_id.shift_name if row.shifts_id else "",
                "groups_id": row.groups_id.groups_name if row.groups_id else "",
                "created_on": row.created_date.strftime("%Y-%m-%d") if row.created_date else "",
                "created_by": row.is_created_by.username if row.is_created_by else "",
                "is_changed_by": row.is_changed_by.username if row.is_changed_by else "",
                "is_changed_date": row.is_changed_date if row.is_changed_date else "",
                "has_access": has_access,
                # NEW FIELD ADDED
                "old_section_list": old_sections,
            })

        return JsonResponse({"success": True, "data": result}, safe=False)

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})
    
# ===========================================================================
# rollback processing view
# ===========================================================================
@login_required()
def getDetailsForHalfYearlyRollSecChangeRollbackAPI(request):
    hyrscinfo_id = request.GET.get("hyrscinfo_id")
    merit_id = request.GET.get("merit_id")
    org_id = request.GET.get("org_id")
    branch_id = request.GET.get("branch_id")
    class_id = request.GET.get("class_id")
    shift_id = request.GET.get("shift_id")
    group_id = request.GET.get("group_id")

    if not hyrscinfo_id:
        return JsonResponse({"success": False, "message": "hyrscinfo_id missing!"})

    # =======================
    # HEADER FETCH
    # =======================
    try:
        header = (
            in_half_yearly_roll_sec_change_info.objects
            .select_related("org_id", "branch_id", "class_id", "shifts_id", "groups_id", "merit_id")
            .get(hyrscinfo_id=hyrscinfo_id)
        )
    except in_half_yearly_roll_sec_change_info.DoesNotExist:
        return JsonResponse({"success": False, "message": "Invalid hyrscinfo_id!"})

    # ============================
    # HISTORY QUERY
    # ============================
    history_qs = (
        in_half_yearly_roll_sec_change_history.objects
        .filter(hyrscinfo_id=header)
        .select_related(
            "reg_id",
            "reg_id__class_id",
            "reg_id__section_id",
            "reg_id__shift_id",
            "reg_id__groups_id",
            "old_section_id",
            "new_section_id"
        )
    )

    # ========================
    # FILTER LOGIC FIXED
    # ========================
    if org_id:
        history_qs = history_qs.filter(org_id__org_id=org_id)

    if branch_id:
        history_qs = history_qs.filter(branch_id__branch_id=branch_id)

    if class_id:
        history_qs = history_qs.filter(reg_id__class_id__class_id=class_id)

    if shift_id:
        history_qs = history_qs.filter(reg_id__shift_id__shift_id=shift_id)

    if group_id:
        history_qs = history_qs.filter(reg_id__groups_id__groups_id=group_id)

    # =======================
    # ORDERING FIXED (NUMERIC)
    # =======================
    history_qs = history_qs.annotate(
        new_roll_int=Cast("new_roll_no", IntegerField())
    ).order_by("new_roll_int")

    # ======================
    # BUILD RESPONSE DATA
    # ======================
    data = []
    for sl, h in enumerate(history_qs, start=1):
        reg = h.reg_id

        data.append({
            "sl": sl,
            "reg_id": reg.reg_id if reg else "",
            "full_name": reg.full_name if reg else "",
            "new_roll_no": h.new_roll_no,
            "roll_no": h.old_roll_no,

            "class_id": reg.class_id.class_id if reg and reg.class_id else "",
            "class_name": reg.class_id.class_name if reg and reg.class_id else "",

            "new_section_id": h.new_section_id.section_id if h.new_section_id else "",
            "new_section_name": h.new_section_id.section_name if h.new_section_id else "",

            "section_id": h.old_section_id.section_id if h.old_section_id else "",
            "section_name": h.old_section_id.section_name if h.old_section_id else "",

            "shift_id": reg.shift_id.shift_id if reg and reg.shift_id else "",
            "shift_name": reg.shift_id.shift_name if reg and reg.shift_id else "",

            "group_id": reg.groups_id.groups_id if reg and reg.groups_id else "",
            "group_name": reg.groups_id.groups_name if reg and reg.groups_id else "",

            "merit_position": h.new_roll_no,
        })

    # =======================
    # HEADER RESPONSE
    # =======================
    header_data = {
        "hyrscinfo_id": header.hyrscinfo_id,
        "merit_id": header.merit_id.merit_id if header.merit_id else "",
        "org_id": header.org_id.org_id if header.org_id else "",
        "org_name": header.org_id.org_name if header.org_id else "",

        "branch_id": header.branch_id.branch_id if header.branch_id else "",
        "branch_name": header.branch_id.branch_name if header.branch_id else "",

        "class_id": header.class_id.class_id if header.class_id else "",
        "class_name": header.class_id.class_name if header.class_id else "",

        "shift_id": header.shifts_id.shift_id if header.shifts_id else "",
        "shift_name": header.shifts_id.shift_name if header.shifts_id else "",

        "group_id": header.groups_id.groups_id if header.groups_id else "",
        "group_name": header.groups_id.groups_name if header.groups_id else "",

        "is_english": header.is_english,
        "is_bangla": header.is_bangla,
        "merit_year": header.hyrscinfo_year,
    }

    return JsonResponse({
        "success": True,
        "header": header_data,
        "data": data
    })
    
    
@csrf_exempt
@login_required()
def rollbackHalfYearlyRollSectionChangeAPI(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request method"})

    try:
        # ------------------------ #
        #       BASIC FIELDS       #
        # ------------------------ #
        hyrscinfo_id = request.POST.get("hyrscinfo_id")
        merit_id = request.POST.get("merit_id")

        if not hyrscinfo_id or not hyrscinfo_id.isdigit():
            return JsonResponse({"success": False, "message": "Invalid hyrscinfo_id!"})

        hyrscinfo_id = int(hyrscinfo_id)

        # Filters
        org_id = request.POST.get("filter_org_id") or None
        branch_id = request.POST.get("filter_branch_id") or None
        class_id = request.POST.get("filter_class_id") or None
        shift_id = request.POST.get("filter_shift_id") or None
        group_id = request.POST.get("filter_group_id") or None
        year = request.POST.get("filter_year")

        # Version check
        version = (request.POST.get("filter_version") or "").strip().lower()
        is_english = (version == "english")
        is_bangla = (version == "bangla")

        user = request.user

        # ------------------------ #
        #        LIST FIELDS       #
        # ------------------------ #
        reg_ids = request.POST.getlist("reg_id[]")
        class_ids_list = request.POST.getlist("class_id[]")
        rollback_sections = request.POST.getlist("rollback_section_id[]")
        rollback_rolls = request.POST.getlist("rollback_roll_no[]")
        new_section_ids = request.POST.getlist("new_section_id[]")
        new_rolls = request.POST.getlist("new_roll_no[]")

        if not reg_ids:
            return JsonResponse({"success": False, "message": "No students selected!"})

        # ------------------------ #
        #     ATOMIC OPERATION     #
        # ------------------------ #
        with transaction.atomic():

            # ========== 1. MAIN CHANGE INFO RECORD ========== #
            hyrscinfo_obj = get_object_or_404(
                in_half_yearly_roll_sec_change_info,
                hyrscinfo_id=hyrscinfo_id
            )

            if hyrscinfo_obj.is_rollback:
                return JsonResponse({
                    "success": True,
                    "message": "Already Rolled Back!"
                })

            # Update main table
            hyrscinfo_obj.is_rollback = True
            hyrscinfo_obj.is_rollback_by = user
            hyrscinfo_obj.is_rollback_date = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
            hyrscinfo_obj.merit_id_id = None  # Clear merit link on rollback
            hyrscinfo_obj.save()

            # ========== 1.1 ALSO UPDATE MERIT APPROVAL ========== #
            if merit_id:
                in_merit_position_approval.objects.filter(merit_id=merit_id).update(
                    is_half_roll_sec_change=False,
                    is_half_roll_sec_change_by=None,
                    is_half_roll_sec_change_date=None
                )

            # ========== 2. AGGREGATE PK + SESSION IN ONE QUERY ========== #
            agg = in_half_yearly_rollsecchange_rollback_history.objects.aggregate(
                last_pk=Max("hyrscrollbackh_id"),
                last_created=Max("ss_created_session"),
                last_modified=Max("ss_modified_session"),
            )

            next_pk = (agg["last_pk"] or 1939400000001) + 1
            next_created = (agg["last_created"] or 14888900300000) + 1
            next_modified = (agg["last_modified"] or 10588096810000) + 1

            now = timezone.now()

            # ------------------------ #
            #   3. BUILD HISTORY ROWS  #
            # ------------------------ #
            history_objs = []
            reg_update_list = []

            for i, reg_id in enumerate(reg_ids):
                cls_id = class_ids_list[i] if i < len(class_ids_list) else class_id
                new_sec = new_section_ids[i] if i < len(new_section_ids) else None
                rollback_sec = rollback_sections[i] if i < len(rollback_sections) else None
                new_roll = new_rolls[i] if i < len(new_rolls) else None
                rollback_roll = rollback_rolls[i] if i < len(rollback_rolls) else None

                # Clean section IDs
                new_sec = int(new_sec) if new_sec and str(new_sec).isdigit() else None
                rollback_sec = int(rollback_sec) if rollback_sec and str(rollback_sec).isdigit() else None

                # If rollback exists → update registration later
                if rollback_sec or rollback_roll:
                    reg_update_list.append((reg_id, rollback_sec, rollback_roll))

                history_objs.append(
                    in_half_yearly_rollsecchange_rollback_history(
                        hyrscrollbackh_id=next_pk + i,
                        hyrscinfo_id=hyrscinfo_obj,
                        org_id_id=org_id,
                        branch_id_id=branch_id,
                        class_id_id=cls_id,
                        shifts_id_id=shift_id,
                        groups_id_id=group_id,
                        reg_id_id=reg_id,
                        hyrscinfo_year=year,
                        is_half_yearly=True,
                        is_english=is_english,
                        is_bangla=is_bangla,
                        new_section_id_id=new_sec,
                        new_roll_no=new_roll,
                        rollback_section_id_id=rollback_sec,
                        rollback_roll_no=rollback_roll,
                        ss_creator=user,
                        ss_created_on=now,
                        ss_created_session=next_created + i,
                        ss_modified_on=now,
                        ss_modified_session=next_modified + i,
                    )
                )

            # ------------------------ #
            #      4. BULK CREATE      #
            # ------------------------ #
            in_half_yearly_rollsecchange_rollback_history.objects.bulk_create(
                history_objs,
                batch_size=800
            )

            # ------------------------ #
            #     5. UPDATE STUDENT    #
            # ------------------------ #
            for reg_id, sec, roll in reg_update_list:
                in_registrations.objects.filter(reg_id=reg_id).update(
                    section_id_id=sec,
                    roll_no=roll,
                    ss_modifier=user,
                    ss_modified_on=now,
                    ss_modified_session=F("ss_modified_session") + 1
                )

        return JsonResponse({"success": True, "message": "Rollback completed!"})

    except Exception as e:
        return JsonResponse({"success": False, "message": f"Error: {str(e)}"})
    

# ===========================================================================
# report view
# ===========================================================================
def getDetailsForReportHalfYearlyRollSecChangeAPI(request):
    hyrscinfo_id = request.GET.get("hyrscinfo_id")
    org_id = request.GET.get("org_id")
    branch_id = request.GET.get("branch_id")
    class_id = request.GET.get("class_id")
    shift_id = request.GET.get("shift_id")
    group_id = request.GET.get("group_id")

    if not hyrscinfo_id:
        return JsonResponse({"success": False, "message": "hyrscinfo_id is required!"})

    # ------------------------------
    # FIXED: Removed invalid field is_changed_by__profile
    # ------------------------------
    try:
        header = (
            in_half_yearly_roll_sec_change_info.objects
            .select_related(
                "org_id", "branch_id", "class_id", "shifts_id", "groups_id",
                "is_changed_by"
            )
            .get(hyrscinfo_id=hyrscinfo_id)
        )
    except in_half_yearly_roll_sec_change_info.DoesNotExist:
        return JsonResponse({"success": False, "message": "Invalid hyrscinfo_id"})

    # ------------------------------
    # HISTORY LIST
    # ------------------------------
    history_qs = (
        in_half_yearly_roll_sec_change_history.objects
        .filter(hyrscinfo_id=hyrscinfo_id)
        .select_related(
            "reg_id",
            "reg_id__class_id", "reg_id__section_id", "reg_id__shift_id", "reg_id__groups_id",
            "old_section_id", "new_section_id"
        )
        .annotate(new_roll_int=Cast('new_roll_no', IntegerField()))
        .order_by("new_roll_int")
    )

    # Additional filters
    if org_id:
        history_qs = history_qs.filter(org_id__org_id=org_id)
    if branch_id:
        history_qs = history_qs.filter(branch_id__branch_id=branch_id)
    if class_id:
        history_qs = history_qs.filter(class_id__class_id=class_id)
    if shift_id:
        history_qs = history_qs.filter(shifts_id__shift_id=shift_id)
    if group_id:
        history_qs = history_qs.filter(groups_id__groups_id=group_id)

    # STUDENT DATA
    data = []
    for idx, h in enumerate(history_qs, start=1):
        reg = h.reg_id
        data.append({
            "sl": idx,
            "reg_id": reg.reg_id if reg else "",
            "full_name": reg.full_name if reg else "",
            "roll_no": h.old_roll_no or "-",
            "new_roll_no": h.new_roll_no or "-",
            "class_name": reg.class_id.class_name if reg and reg.class_id else "",
            "section_name": h.old_section_id.section_name if h.old_section_id else "-",
            "new_section_name": h.new_section_id.section_name if h.new_section_id else "-",
            "shift_name": reg.shift_id.shift_name if reg and reg.shift_id else "",
            "group_name": reg.groups_id.groups_name if reg and reg.groups_id else "",
            "merit_position": h.new_roll_no or "",
        })

    org = header.org_id
    branch = header.branch_id
    class_obj = header.class_id
    shift_obj = header.shifts_id
    group_obj = header.groups_id

    # CONTACT + LOGO PRIORITY
    address = (branch.address or org.address) if branch or org else ""
    email = (branch.email or org.email) if branch or org else ""
    website = (branch.website or org.website) if branch or org else ""

    phone_hotline = []
    if branch and branch.phone:
        phone_hotline.append(branch.phone)
    if branch and branch.hotline:
        phone_hotline.append(branch.hotline)
    if not phone_hotline and org:
        if org.phone: phone_hotline.append(org.phone)
        if org.hotline: phone_hotline.append(org.hotline)
    phone_hotline_str = " | ".join(phone_hotline) if phone_hotline else ""

    fax = (branch.fax or org.fax) if branch or org else ""

    logo_url = ""
    if branch and branch.branch_logo:
        logo_url = request.build_absolute_uri(branch.branch_logo.url)
    elif org and org.org_logo:
        logo_url = request.build_absolute_uri(org.org_logo.url)

    # Version
    version_text = "English Version" if header.is_english else "Bangla Version" if header.is_bangla else ""

    group_part = f" ({group_obj.groups_name})" if group_obj else ""
    exam_line = (
        f"{class_obj.class_name if class_obj else ''} - "
        f"{shift_obj.shift_name if shift_obj else ''} - "
        f"Half Yearly Roll & Section Change{group_part} - "
        f"{version_text} - {header.hyrscinfo_year}"
    )

    changed_info = ""
    if getattr(header, "is_changed", False) and header.is_changed_by:
        name = header.is_changed_by.get_full_name() or header.is_changed_by.username
        changed_info = f"Changed By: {name} on {header.is_changed_date}"

    # FINAL HEADER DATA
    header_data = {
        "org_name": org.org_name if org else "",
        "branch_name": branch.branch_name if branch else "",
        "address": address,
        "email": email,
        "website": website,
        "phone_hotline": phone_hotline_str,
        "fax": fax,
        "logo": logo_url,
        "exam_line": exam_line,
        "changed_info": changed_info,
    }

    return JsonResponse({
        "success": True,
        "header": header_data,
        "data": data
    })
    
    

# ============================================================================
# rollback history list view
# ============================================================================
@login_required()
def getHalfYearlyRollSecChangeRollbackHistoryListAPI(request):
    try:
        user = request.user
        org_id = request.GET.get("org_id")
        branch_id = request.GET.get("branch_id")
        class_id = request.GET.get("class_id")
        shift_id = request.GET.get("shift_id")
        groups_id = request.GET.get("groups_id")
        year = request.GET.get("year")
        version = request.GET.get("version")
        
        # ACCESS PERMISSION CHECK
        has_access = access_list.objects.filter(
            user_id=user,
            feature_id__feature_page_link='HLFYRLYSECRCHROLLBACKBTNACC',
            is_active=True
        ).exists()

        # ====== FILTERING ======
        filters = {}
        if org_id:
            filters["org_id_id"] = org_id
        if branch_id:
            filters["branch_id_id"] = branch_id
        if class_id:
            filters["class_id_id"] = class_id
        if shift_id:
            filters["shifts_id_id"] = shift_id
        if groups_id:
            filters["groups_id_id"] = groups_id
        if year:
            filters["hyrscinfo_year"] = year
        if version:
            if version.lower() == "english":
                filters["is_english"] = True
            elif version.lower() == "bangla":
                filters["is_bangla"] = True

        # ====== QUERY MAIN TABLE ======
        info_list = in_half_yearly_roll_sec_change_info.objects.filter(
            **filters,
            is_changed=True,
            is_rollback=True
        ).order_by("hyrscinfo_id")

        result = []

        # ====== BUILD RESPONSE WITH HISTORY DATA ======
        for row in info_list:

            # FETCH ALL new_section_id FOR THIS hyrscinfo_id
            history_qs = in_half_yearly_rollsecchange_rollback_history.objects.filter(
                hyrscinfo_id=row.hyrscinfo_id
            ).select_related("new_section_id")

            # MULTIPLE NEW SECTION IDs POSSIBLE
            new_sections = []
            for h in history_qs:
                if h.new_section_id:
                    new_sections.append({
                        "section_id": h.new_section_id.section_id,
                        "section_name": h.new_section_id.section_name
                    })

            result.append({
                "hyrscinfo_id": row.hyrscinfo_id,
                "merit_id": row.merit_id.merit_id if row.merit_id else "",
                "org_id": row.org_id.org_name if row.org_id else "",
                "branch_id": row.branch_id.branch_name if row.branch_id else "",
                "class_id": row.class_id.class_name if row.class_id else "",
                "shift_id": row.shifts_id.shift_name if row.shifts_id else "",
                "groups_id": row.groups_id.groups_name if row.groups_id else "",
                "created_on": row.created_date.strftime("%Y-%m-%d") if row.created_date else "",
                "created_by": row.is_created_by.username if row.is_created_by else "",
                "is_rollback_by": row.is_rollback_by.username if row.is_rollback_by else "",
                "is_rollback_date": row.is_rollback_date if row.is_rollback_date else "",
                "has_access": has_access,
                # NEW FIELD ADDED
                "new_section_list": new_sections,
            })

        return JsonResponse({"success": True, "data": result}, safe=False)

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})
    
    
# ===========================================================================
# Rollback history report view
# ===========================================================================
@login_required()
def getDetailsForReportHalfYearlyRollSecChangeRollbackHistoryAPI(request):
    hyrscinfo_id = request.GET.get("hyrscinfo_id")
    org_id = request.GET.get("org_id")
    branch_id = request.GET.get("branch_id")
    class_id = request.GET.get("class_id")
    shift_id = request.GET.get("shift_id")
    group_id = request.GET.get("group_id")

    if not hyrscinfo_id:
        return JsonResponse({"success": False, "message": "hyrscinfo_id is required!"})

    # HEADER DATA FETCH
    try:
        header = (
            in_half_yearly_roll_sec_change_info.objects
            .select_related(
                "org_id", "branch_id", "class_id", "shifts_id", "groups_id",
                "is_changed_by"
            )
            .get(hyrscinfo_id=hyrscinfo_id)
        )
    except in_half_yearly_roll_sec_change_info.DoesNotExist:
        return JsonResponse({"success": False, "message": "Invalid hyrscinfo_id"})

    # HISTORY DATA
    history_qs = (
        in_half_yearly_rollsecchange_rollback_history.objects
        .filter(hyrscinfo_id=hyrscinfo_id)
        .select_related(
            "reg_id",
            "rollback_section_id",
            "new_section_id",
            "class_id",
            "branch_id",
            "groups_id",
            "shifts_id"
        )
        .annotate(
            rollback_roll_int=Cast('rollback_roll_no', IntegerField())
        )
        .order_by("rollback_roll_int")
    )

    # OPTIONAL FILTERS
    if org_id:
        history_qs = history_qs.filter(org_id__org_id=org_id)
    if branch_id:
        history_qs = history_qs.filter(branch_id__branch_id=branch_id)
    if class_id:
        history_qs = history_qs.filter(class_id__class_id=class_id)
    if shift_id:
        history_qs = history_qs.filter(shifts_id__shift_id=shift_id)
    if group_id:
        history_qs = history_qs.filter(groups_id__groups_id=group_id)

    # BUILD DATA JSON
    data = []
    for idx, h in enumerate(history_qs, start=1):
        reg = h.reg_id
        data.append({
            "sl": idx,
            "reg_id": reg.reg_id if reg else "",
            "full_name": reg.full_name if reg else "",
            "new_roll_no": h.new_roll_no or "-",
            "rollback_roll_no": h.rollback_roll_no or "-",
            "class_name": reg.class_id.class_name if reg and reg.class_id else "",
            "new_section_name": h.new_section_id.section_name if h.new_section_id else "-",
            "rollback_section_name": h.rollback_section_id.section_name if h.rollback_section_id else "-",
            "shift_name": reg.shift_id.shift_name if reg and reg.shift_id else "",
            "group_name": reg.groups_id.groups_name if reg and reg.groups_id else "",
            "merit_position": h.new_roll_no or "",
        })

    # HEADER OBJECTS
    org = header.org_id
    branch = header.branch_id
    class_obj = header.class_id
    shift_obj = header.shifts_id
    group_obj = header.groups_id

    # CONTACT DETAILS
    address = (branch.address or org.address) if branch or org else ""
    email = (branch.email or org.email) if branch or org else ""
    website = (branch.website or org.website) if branch or org else ""

    phone_hotline_list = []
    if branch:
        if branch.phone: phone_hotline_list.append(branch.phone)
        if branch.hotline: phone_hotline_list.append(branch.hotline)
    if not phone_hotline_list and org:
        if org.phone: phone_hotline_list.append(org.phone)
        if org.hotline: phone_hotline_list.append(org.hotline)

    phone_hotline = " | ".join(phone_hotline_list) if phone_hotline_list else ""

    fax = (branch.fax or org.fax) if branch or org else ""

    # LOGO URL
    if branch and branch.branch_logo:
        logo_url = request.build_absolute_uri(branch.branch_logo.url)
    elif org and org.org_logo:
        logo_url = request.build_absolute_uri(org.org_logo.url)
    else:
        logo_url = ""

    # VERSION TEXT
    version_text = (
        "English Version" if header.is_english else
        "Bangla Version" if header.is_bangla else ""
    )

    # GROUP PART
    group_part = f" ({group_obj.groups_name})" if group_obj else ""

    # EXAM TITLE LINE
    exam_line = (
        f"{class_obj.class_name if class_obj else ''} - "
        f"{shift_obj.shift_name if shift_obj else ''} - "
        f"Half Yearly Roll & Section Change Rollback History"
        f"{group_part} - {version_text} - {header.hyrscinfo_year}"
    )

    # CHANGE INFO
    if header.is_changed and header.is_changed_by:
        changer = header.is_changed_by.get_full_name() or header.is_changed_by.username
        changed_info = f"Changed By: {changer} on {header.is_changed_date}"
    else:
        changed_info = ""

    # FINAL HEADER JSON
    header_data = {
        "org_name": org.org_name if org else "",
        "branch_name": branch.branch_name if branch else "",
        "address": address,
        "email": email,
        "website": website,
        "phone_hotline": phone_hotline,
        "fax": fax,
        "logo_url": logo_url,
        "exam_line": exam_line,
        "changed_info": changed_info,
    }

    # FINAL RETURN
    return JsonResponse({
        "success": True,
        "header": header_data,
        "data": data
    })