import json
from django.db.models import Q, Count
from audioop import reverse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, Http404
from django.contrib import messages
from django.db import transaction, IntegrityError
from class_setup.models import in_class
from defaults_exam_mode.models import ExamModeTypeMap, defaults_exam_modes, in_letter_grade_mode, in_letter_gradeFiftyMap, in_letter_gradeHundredMap
from exam_type.models import in_exam_type
from groups_setup.models import in_groups
from merit_app_card_print.models import in_merit_position_approval, in_merit_position_approvaldtls
from organizations.models import organizationlst
from policy_setup.models import annual_exam_percentance_policy, classSectionGroupingMap, half_year_roll_section_change_policy, in_class_wise_merit_policy, in_subject_wise_merit_policy
from section_setup.models import in_section
from shift_setup.models import in_shifts
from subject_setup.models import in_subjects
from django.contrib.auth import get_user_model
User = get_user_model()

# Create your views here.
@login_required()
def policySetupManagerAPI(request):
    exam_type = in_exam_type.objects.filter(is_active=True).all()
    exam_mode = defaults_exam_modes.objects.filter(is_active=True).all()
    letter_grade = in_letter_grade_mode.objects.filter(is_active=True).all()

    context = {
        'exam_type': exam_type,
        'exam_mode': exam_mode,
        'letter_grade': letter_grade,
    }
    
    return render(request, 'policy_setup/policy_setup.html', context)


@login_required()
def getPolicySetupDataManagerAPI(request):
    is_version = request.GET.get("is_version", "english")
    org_id = request.GET.get("org")
    class_id = request.GET.get("is_class_id")

    is_english = (is_version == "english")
    is_bangla = (is_version == "bangla")

    exam_mode_type_data = ExamModeTypeMap.objects.filter(
        org_id=org_id,
        class_id=class_id,
        is_english=is_english,
        is_bangla=is_bangla
    ).values("def_mode_id", "exam_type_id")  # শুধু দরকারি ফিল্ড

    grade_hundred_data = in_letter_gradeHundredMap.objects.filter(
        org_id=org_id,
        class_id=class_id,
        is_english=is_english,
        is_bangla=is_bangla
    ).values("grade_id", "from_marks", "to_marks", "grade_point", "is_active")

    grade_fifty_data = in_letter_gradeFiftyMap.objects.filter(
        org_id=org_id,
        class_id=class_id,
        is_english=is_english,
        is_bangla=is_bangla
    ).values("grade_id", "from_marks", "to_marks", "grade_point", "is_active")

    data = {
        'exam_mode_type_data': list(exam_mode_type_data),
        'grade_hundred_data': list(grade_hundred_data),
        'grade_fifty_data': list(grade_fifty_data),
        'selected_org': org_id,
        'selected_class': class_id,
        'selected_version': is_version,
    }
    
    return JsonResponse(data)

@login_required
@csrf_exempt
def letterGradeXMtypePolicySaveandUpdate(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))

            org_id = organizationlst.objects.get(pk=data.get('id_org'))
            class_id = in_class.objects.get(pk=data.get('is_class_id'))
            is_version = data.get('is_version')
            is_version = data.get('is_version')
            if is_version == "english":
                is_english = True
                is_bangla = False
            if is_version == "bangla":
                is_english = False
                is_bangla = True
                
                
            if org_id and class_id:
                ExamModeTypeMap.objects.filter(org_id=org_id, class_id=class_id, is_english=is_english, is_bangla=is_bangla).delete()
                in_letter_gradeHundredMap.objects.filter(org_id=org_id, class_id=class_id, is_english=is_english, is_bangla=is_bangla).delete()
                in_letter_gradeFiftyMap.objects.filter(org_id=org_id, class_id=class_id, is_english=is_english, is_bangla=is_bangla).delete()
                

            # ---------- Save Table 1 ----------
            for item in data.get('examSelections', []):
                def_mode = defaults_exam_modes.objects.get(pk=item['def_mode_id'])
                exam_type = in_exam_type.objects.get(pk=item['exam_type_id'])
                ExamModeTypeMap.objects.create(
                    org_id=org_id,
                    class_id=class_id,
                    def_mode_id=def_mode,
                    exam_type_id=exam_type,
                    is_english=is_english,
                    is_bangla=is_bangla,
                    ss_creator=request.user
                )

            # ---------- Save Table 2 (Hundred Marks) ----------
            for item in data.get('hundredGrades', []):
                grade = in_letter_grade_mode.objects.get(pk=item['grade_id'])
                in_letter_gradeHundredMap.objects.create(
                    org_id=org_id,
                    class_id=class_id,
                    grade_id=grade,
                    from_marks=float(item['from_marks'] or 0.00),
                    to_marks=float(item['to_marks'] or 0.00),
                    grade_point=float(item['grade_point'] or 0.00),
                    is_active=item['is_active'],
                    is_english=is_english,
                    is_bangla=is_bangla,
                    ss_creator=request.user
                )

            # ---------- Save Table 3 (Fifty Marks) ----------
            for item in data.get('fiftyGrades', []):
                grade = in_letter_grade_mode.objects.get(pk=item['grade_id'])
                in_letter_gradeFiftyMap.objects.create(
                    org_id=org_id,
                    class_id=class_id,
                    grade_id=grade,
                    from_marks=float(item['from_marks'] or 0.00),
                    to_marks=float(item['to_marks'] or 0.00),
                    grade_point=float(item['grade_point'] or 0.00),
                    is_active=item['is_active'],
                    is_english=is_english,
                    is_bangla=is_bangla,
                    ss_creator=request.user
                )

            return JsonResponse({"msg": "Class data saved successfully!"})

        except Exception as e:
            return JsonResponse({"errmsg": str(e)}, status=400)

    return JsonResponse({"errmsg": "Invalid request"}, status=400)


# =============================================== merit_positions_policy ===============================================

@login_required()
def meritPositionsPolicyManagerAPI(request):

    user = request.user

    class_list = in_class.objects.filter(is_active=True, org_id=user.org_id).all()
    english_section = in_section.objects.filter(is_active=True, org_id=user.org_id, is_english=True)
    bangla_section = in_section.objects.filter(is_active=True, org_id=user.org_id, is_bangla=True)

    context = {
        "classes": class_list,
        "english_section": english_section,
        "bangla_section": bangla_section,
    }
    
    return render(request, 'policy_setup/merit_position/merit_positions_policy.html', context)


@login_required()
def getclassWiseMeritPolicyManagerAPI(request):
    user = request.user
    is_version = request.GET.get("is_version", "english")

    if is_version == "english":
        policies = in_class_wise_merit_policy.objects.filter(org_id=user.org_id, is_english=True)
    elif is_version == "bangla":
        policies = in_class_wise_merit_policy.objects.filter(org_id=user.org_id, is_bangla=True)
    else:
        policies = in_class_wise_merit_policy.objects.filter(org_id=user.org_id)

    policy_map = {
        p.class_id_id: {
            "is_average_gpa_priority": p.is_average_gpa_priority,
            "total_obtained_marks_priority": p.total_obtained_marks_priority,
            "roll_no_priority": p.roll_no_priority,
            "is_fail_sub_count": p.is_fail_sub_count,
            "is_gross_merit_position": p.is_gross_merit_position,
        }
        for p in policies
    }

    return JsonResponse({
        "policy_map": policy_map,
        "is_version": is_version,
    })
    
    

@csrf_exempt
@login_required()
def save_classwise_merit_policy(request):
    if request.method == "POST":
        try:
            org_id = request.POST.get("org")
            is_version = request.POST.get("is_version")

            class_ids = request.POST.getlist("class_id[]")
            gpa_priorities = request.POST.getlist("is_average_gpa_priority[]")
            marks_priorities = request.POST.getlist("total_obtained_marks_priority[]")
            roll_priorities = request.POST.getlist("roll_no_priority[]")
            is_fail_sub_counts = request.POST.getlist("is_fail_sub_count[]")
            is_gross_merit_positions = request.POST.getlist("is_gross_merit_position[]")

            with transaction.atomic():
                for i, class_id in enumerate(class_ids):
                    gpa_val = gpa_priorities[i] if gpa_priorities[i] else None
                    marks_val = marks_priorities[i] if marks_priorities[i] else None
                    roll_val = roll_priorities[i] if roll_priorities[i] else None
                    is_fail_sub_count = str(class_ids[i]) in is_fail_sub_counts
                    is_gross_merit_position = str(class_ids[i]) in is_gross_merit_positions

                    # Update or create
                    obj, created = in_class_wise_merit_policy.objects.update_or_create(
                        org_id_id=org_id,
                        class_id_id=class_id,
                        is_english=True if is_version == "english" else False,
                        is_bangla=True if is_version == "bangla" else False,
                        defaults={
                            "is_average_gpa_priority": gpa_val,
                            "total_obtained_marks_priority": marks_val,
                            "roll_no_priority": roll_val,
                            "is_fail_sub_count": is_fail_sub_count,
                            "is_gross_merit_position": is_gross_merit_position,
                            "ss_creator": request.user,
                            "ss_modifier": request.user,
                        }
                    )

            return JsonResponse({"success": True, "msg": "Merit policy saved successfully!"})

        except Exception as e:
            return JsonResponse({"success": False, "errmsg": str(e)})

    return JsonResponse({"success": False, "errmsg": "Invalid request"})


@login_required()
def save_subjectswise_merit_policy(request):
    if request.method == "POST":
        try:
            org_ids = request.POST.getlist("org_sub[]")
            class_ids = request.POST.getlist("is_class_sub[]")
            group_ids = request.POST.getlist("is_groups_id[]")  # can be empty
            subjects_ids = request.POST.getlist("subjects_id[]")
            versions = request.POST.getlist("is_version_sub[]")
            priorities = request.POST.getlist("subject_priority[]")
            sub_groups = request.POST.getlist("is_sub_groups[]")

            with transaction.atomic():
                for i in range(len(subjects_ids)):
                    org = organizationlst.objects.get(pk=org_ids[i])
                    cls = in_class.objects.get(pk=class_ids[i])

                    # group handle
                    grp_id = group_ids[i] if i < len(group_ids) else None
                    grp = in_groups.objects.get(pk=grp_id) if grp_id else None

                    subj = in_subjects.objects.get(pk=subjects_ids[i])
                    version = versions[i].lower().strip()
                    priority = int(priorities[i]) if priorities[i] else None

                    # ✅ Checkbox handle: subject_id আছে কিনা sub_groups এ
                    sub_group = str(subjects_ids[i]) in sub_groups  

                    # Version boolean mapping
                    is_english = version == "english"
                    is_bangla = version == "bangla"

                    existing = in_subject_wise_merit_policy.objects.filter(
                        org_id=org,
                        class_id=cls,
                        groups_id=grp,
                        subjects_id=subj,
                        is_english=is_english,
                        is_bangla=is_bangla
                    ).first()

                    if existing:
                        existing.subject_priority = priority
                        existing.is_sub_groups = sub_group
                        existing.ss_modifier = request.user
                        existing.save()
                    else:
                        in_subject_wise_merit_policy.objects.create(
                            org_id=org,
                            class_id=cls,
                            groups_id=grp,
                            subjects_id=subj,
                            subject_priority=priority,
                            is_sub_groups=sub_group,
                            is_english=is_english,
                            is_bangla=is_bangla,
                            ss_creator=request.user,
                            ss_modifier=request.user
                        )

            return JsonResponse({"success": True, "msg": "Subjects Merit Policy saved successfully!"})

        except Exception as e:
            return JsonResponse({"success": False, "errmsg": str(e)})

    return JsonResponse({"success": False, "errmsg": "Invalid request"})


@login_required()
def get_subjectswise_merit_policy(request):
    policies = (
        in_subject_wise_merit_policy.objects.select_related(
            'org_id', 'class_id', 'groups_id', 'subjects_id'
        )
        .order_by("class_id", "-is_english", "-is_bangla", "subject_priority")  
    )

    policyList = []
    for p in policies:
        policyList.append({
            "subswisep_id": p.subswisep_id,
            "org_id": p.org_id.org_id,
            "class_id": p.class_id.class_id,
            "class_name": p.class_id.class_name,
            "groups_id": p.groups_id.groups_id if p.groups_id else None,
            "group_name": p.groups_id.groups_name if p.groups_id else '',
            "subjects_id": p.subjects_id.subjects_id,
            "subject_name": p.subjects_id.subjects_name,
            "subject_priority": p.subject_priority,
            "is_sub_groups": p.is_sub_groups,
            "is_english": p.is_english,
            "is_bangla": p.is_bangla,
        })

    return JsonResponse({"policyList": policyList})


    # org_id = request.GET.get('org_id')
    # class_id = request.GET.get('class_id')
    # groups_id = request.GET.get('groups_id') or None
    # version = request.GET.get('version')

    # # Boolean filter for version
    # is_english = version == "english"
    # is_bangla = version == "bangla"

    # policies = in_subject_wise_merit_policy.objects.filter(
    #     org_id=org_id,
    #     class_id=class_id,
    #     groups_id=groups_id,
    #     is_english=is_english,
    #     is_bangla=is_bangla
    # ).select_related('subjects_id', 'class_id', 'groups_id', 'org_id')

    # policyList = []
    # for p in policies:
    #     policyList.append({
    #         "org_id": p.org_id.org_id,
    #         "class_id": p.class_id.class_id,
    #         "class_name": p.class_id.class_name,
    #         "groups_id": p.groups_id.groups_id if p.groups_id else None,
    #         "group_name": p.groups_id.groups_name if p.groups_id else '',
    #         "subjects_id": p.subjects_id.subjects_id,
    #         "subject_name": p.subjects_id.subjects_name,
    #         "subject_priority": p.subject_priority,
    #         "is_english": p.is_english,
    #         "is_bangla": p.is_bangla,
    #     })

    # return JsonResponse({"policyList": policyList})
    
    
@csrf_exempt  # CSRF AJAX call এর জন্য
@login_required()
def delete_subjectswise_policy(request):
    if request.method == "POST":
        try:
            subswisep_id = request.POST.get("subswisep_id")
            if not subswisep_id:
                return JsonResponse({"success": False, "errmsg": "Invalid ID"})

            obj = in_subject_wise_merit_policy.objects.filter(subswisep_id=subswisep_id)
            if obj.exists():
                obj.delete()
                return JsonResponse({"success": True, "msg": "Record deleted successfully!"})
            else:
                return JsonResponse({"success": False, "errmsg": "Record not found"})

        except Exception as e:
            return JsonResponse({"success": False, "errmsg": str(e)})

    return JsonResponse({"success": False, "errmsg": "Invalid request"})



@csrf_exempt
@login_required()
def save_class_section_grouping(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            org_id = data.get("id_org")
            is_english_version = data.get("is_english_version")
            is_bangla_version = data.get("is_bangla_version")
            section_mappings = data.get("sectionMappings", [])

            org = organizationlst.objects.get(pk=org_id)

            # ---------- প্রথমে পুরানো ডাটা ডিলিট করব ----------
            if is_english_version == "english":
                classSectionGroupingMap.objects.filter(org_id=org, is_english=True).delete()
            if is_bangla_version == "bangla":
                classSectionGroupingMap.objects.filter(org_id=org, is_bangla=True).delete()

            # ---------- নতুন ডাটা Save ----------
            for mapping in section_mappings:
                class_obj = in_class.objects.get(pk=mapping["class_id"])
                section_obj = in_section.objects.get(pk=mapping["section_id"])

                classSectionGroupingMap.objects.create(
                    org_id=org,
                    class_id=class_obj,
                    section_id=section_obj,
                    is_order_by=mapping["order_by"],
                    is_group_no=mapping["group_no"],
                    is_group_name=mapping["group_name"],
                    is_grouping_flag=mapping["is_grouping_flag"],
                    is_individual_flag=mapping["is_individual_flag"],
                    is_english=(is_english_version == "english"),
                    is_bangla=(is_bangla_version == "bangla"),
                    ss_creator=request.user
                )

            return JsonResponse({"msg": "Class Section Grouping saved successfully!"})

        except Exception as e:
            return JsonResponse({"errmsg": str(e)})

    return JsonResponse({"errmsg": "Invalid request"}, status=400)


@login_required()
def get_class_section_grouping_for_english(request):
    org_id = request.GET.get("org_id")
    is_english_version = request.GET.get("is_english_version", "english")

    if not org_id:
        return JsonResponse({"errmsg": "Organization ID required"}, status=400)

    if is_english_version == "english":
        mappings = classSectionGroupingMap.objects.filter(org_id_id=org_id, is_english=True)

    data = []
    for m in mappings:
        data.append({
            "class_id": m.class_id_id,
            "section_id": m.section_id_id,
            "is_order_by": m.is_order_by,
            "is_group_no": m.is_group_no,
            "is_group_name": m.is_group_name,
            "is_grouping_flag": m.is_grouping_flag,
            "is_individual_flag": m.is_individual_flag,
        })

    return JsonResponse({"data": data})



@login_required()
def get_class_section_grouping_for_bangla(request):
    org_id = request.GET.get("org_id")
    is_bangla_version = request.GET.get("is_bangla_version", "bangla")

    if not org_id:
        return JsonResponse({"errmsg": "Organization ID required"}, status=400)

    if is_bangla_version == "bangla":
        mappings = classSectionGroupingMap.objects.filter(org_id_id=org_id, is_bangla=True)

    data = []
    for m in mappings:
        data.append({
            "class_id": m.class_id_id,
            "section_id": m.section_id_id,
            "is_order_by": m.is_order_by,
            "is_group_no": m.is_group_no,
            "is_group_name": m.is_group_name,
            "is_grouping_flag": m.is_grouping_flag,
            "is_individual_flag": m.is_individual_flag,
        })

    return JsonResponse({"data": data})


# ===================================================================================
# half_year_roll_sec_change 
# ===================================================================================

@login_required()
def halfYearRollSecChangePolicyManagerAPI(request):

    shifts = in_shifts.objects.filter(is_active=True).values('shift_id', 'shift_name').order_by('shift_id')
    
    context = {
        'shifts': shifts,
    }

    return render(request, 'policy_setup/half_year_roll_sec_change_policy/half_year_roll_sec_change_policy.html', context)


@login_required()
def savehalfYearRollSecChangePolicyManagerAPI(request):
    resp = {'status': 'failed', 'errmsg': 'Failed ...'}

    try:
        data = request.POST
        org_id = data.get("org")
        class_id = data.get("is_class_id")
        shift_id = data.get("is_shift")
        groups_id = data.get("is_groups")
        version = data.get("is_version")

        # Determine version flags
        is_english = version == 'english'
        is_bangla = version == 'bangla'

        # Fetch FK instances
        org = organizationlst.objects.filter(org_id=org_id).first()
        class_obj = in_class.objects.filter(class_id=class_id).first()
        shift_obj = in_shifts.objects.filter(shift_id=shift_id).first()
        groups_obj = in_groups.objects.filter(groups_id=groups_id).first() if groups_id else None

        if not org or not class_obj or not shift_obj:
            return JsonResponse({'success': False, 'msg': 'Invalid organization, class, or shift.'})

        with transaction.atomic():
            # Delete existing records for same filter
            filters = {
                'org_id': org,
                'class_id': class_obj,
                'shift_id': shift_obj,
                'is_english': is_english,
                'is_bangla': is_bangla,
            }
            if groups_obj:
                filters['groups_id'] = groups_obj
            else:
                filters['groups_id__isnull'] = True

            half_year_roll_section_change_policy.objects.filter(**filters).delete()

            # Extract posted arrays
            section_ids = data.getlist('section_id[]')
            from_rolls = data.getlist('from_roll[]')
            to_rolls = data.getlist('to_roll[]')

            for section_id, from_roll, to_roll in zip(section_ids, from_rolls, to_rolls):
                section_obj = in_section.objects.filter(section_id=section_id).first()
                if not section_obj:
                    continue

                # Checkbox + group_serial field names
                invd_flag_key = f"is_invd_flag[{section_id}]"
                group_flag_key = f"is_group_flag[{section_id}]"
                group_serial_key = f"group_serials[{section_id}]"

                is_invd_flag = invd_flag_key in data
                is_group_flag = group_flag_key in data
                group_serial = data.get(group_serial_key, "").strip()

                from_roll = (from_roll or '').strip()
                to_roll = (to_roll or '').strip()

                # Case 1: if is_invd_flag=True → skip roll validation
                if is_invd_flag:
                    half_year_roll_section_change_policy.objects.create(
                        org_id=org,
                        class_id=class_obj,
                        shift_id=shift_obj,
                        groups_id=groups_obj,
                        section_id=section_obj,
                        from_roll=from_roll or "0",
                        to_roll=to_roll or "0",
                        is_invd_flag=True,
                        is_group_flag=is_group_flag,
                        group_serials=group_serial,
                        is_english=is_english,
                        is_bangla=is_bangla,
                        ss_creator=request.user,
                        ss_modifier=request.user,
                    )
                    continue

                # Case 2: Normal roll validation if not invd_flag
                if from_roll.isdigit() and to_roll.isdigit():
                    from_roll_int = int(from_roll)
                    to_roll_int = int(to_roll)

                    if from_roll_int > 0 and to_roll_int >= from_roll_int:
                        half_year_roll_section_change_policy.objects.create(
                            org_id=org,
                            class_id=class_obj,
                            shift_id=shift_obj,
                            groups_id=groups_obj,
                            section_id=section_obj,
                            from_roll=from_roll,
                            to_roll=to_roll,
                            is_invd_flag=False,
                            is_group_flag=is_group_flag,
                            group_serials=group_serial,
                            is_english=is_english,
                            is_bangla=is_bangla,
                            ss_creator=request.user,
                            ss_modifier=request.user,
                        )
                    else:
                        print(f"Skipped invalid range for section {section_id}: {from_roll}-{to_roll}")
                else:
                    print(f"Skipped non-numeric rolls for section {section_id}: {from_roll}, {to_roll}")

        return JsonResponse({'success': True, 'msg': 'Half-year roll section change policy saved successfully.'})

    except Exception as e:
        print("Unhandled Error:", str(e))
        resp['errmsg'] = str(e)
        return JsonResponse(resp)
    

@login_required()
def get_in_section_dataManagerAPI(request):
    org = request.GET.get("org")
    version = request.GET.get("is_version")
    class_id = request.GET.get("is_class_id")       # optional
    shift_id = request.GET.get("is_shift_id")
    groups_id = request.GET.get("is_groups_id")
    merit_year = request.GET.get("merit_year")

    # ---------------------------
    # 1️⃣ Basic Section Filtering
    # ---------------------------
    filters = {"org_id_id": org, "is_active": True}

    if version == "english":
        filters["is_english"] = True
    elif version == "bangla":
        filters["is_bangla"] = True

    sections_qs = in_section.objects.filter(**filters).order_by("section_id")

    # ---------------------------
    # 2️⃣ Merit Data Filtering
    # ---------------------------
    merit_filters = {"org_id_id": org}
    if class_id:
        merit_filters["class_id_id"] = class_id
    if shift_id:
        merit_filters["shifts_id_id"] = shift_id
    if groups_id:
        merit_filters["groups_id_id"] = groups_id
    if merit_year:
        try:
            merit_filters["merit_year"] = int(merit_year)
        except ValueError:
            pass

    merit_qs = in_merit_position_approval.objects.filter(**merit_filters).order_by("merit_id")

    # ---------------------------
    # 2️⃣1️⃣ Check if no merit records
    # ---------------------------
    if not merit_qs.exists():
        return JsonResponse({
            "success": False,
            "text_body": "This Class, Shift and Groups wise Students Merit Approval Not Found..."
        })

    # ---------------------------
    # 3️⃣ Build Maps
    # ---------------------------
    invd_map = {}          # section_id -> merit_id (single section)
    group_map = {}         # section_id -> {merit_id, serial} (multi-section)
    group_data = {}        # merit_id -> [section_ids]
    assigned_sections = set()

    for merit in merit_qs:
        sec_ids = list(merit.section_id.values_list("section_id", flat=True))
        if not sec_ids:
            continue

        group_data[merit.merit_id] = sec_ids

        # Single-section (INVD)
        if len(sec_ids) == 1:
            sid = sec_ids[0]
            if sid not in assigned_sections:
                invd_map[sid] = {"merit_id": merit.merit_id}
                assigned_sections.add(sid)

        # Multi-section (Grouped)
        else:
            for idx, sid in enumerate(sec_ids, start=1):
                if sid not in assigned_sections:
                    group_map[sid] = {"merit_id": merit.merit_id, "serial": idx}
                    assigned_sections.add(sid)

    # ---------------------------
    # 4️⃣ Get Student Count per Merit
    # ---------------------------
    merit_counts = in_merit_position_approvaldtls.objects.filter(
        merit_id__in=merit_qs.values_list("merit_id", flat=True)
    ).values("merit_id").annotate(student_count=Count("reg_id"))

    # Convert to dict for fast lookup: merit_id -> student_count
    merit_count_map = {mc["merit_id"]: mc["student_count"] for mc in merit_counts}

    # 5️⃣ Build Final Section Data
    data = []
    merit_section_count = {}  # merit_id -> number of sections

    for sec in sections_qs:
        sid = sec.section_id
        item = {
            "section_id": sid,
            "section_name": sec.section_name,
            "from_roll": "",
            "to_roll": "",
            "is_invd_flag": False,
            "is_group_flag": False,
            "group_serial": "",
            "disabled": False,
            "merit_id": None,
            "student_count": 0,
        }

        # If INVD
        if sid in invd_map:
            merit_id = invd_map[sid]["merit_id"]
            item.update({
                "is_invd_flag": True,
                "disabled": True,
                "merit_id": merit_id,
                "student_count": merit_count_map.get(merit_id, 0),
            })
            merit_section_count[merit_id] = 1

        # If Grouped
        elif sid in group_map:
            merit_id = group_map[sid]["merit_id"]
            item.update({
                "is_group_flag": True,
                "disabled": True,
                "merit_id": merit_id,
                "student_count": merit_count_map.get(merit_id, 0),
            })
            merit_section_count[merit_id] = len(group_data.get(merit_id, []))

        data.append(item)

    # ---------------------------
    # 6️⃣ Final JSON Response
    # ---------------------------
    return JsonResponse({
        "success": True,
        "data": data,
        "group_data": group_data,
        "merit_section_count": merit_section_count,  # <-- send for rowspan
    })


@login_required()
def get_halfyear_roll_policyManagerAPI(request):
    org = request.GET.get("org")
    class_id = request.GET.get("is_class_id")
    shift_id = request.GET.get("is_shift_id")
    groups_id = request.GET.get("is_groups")
    is_version = request.GET.get("is_version")
    hyrscp_year = request.GET.get("hyrscp_year")

    filters = {
        "org_id_id": org,
        "class_id_id": class_id,
        "shift_id_id": shift_id,
        "hyrscp_year": hyrscp_year,
    }

    # Strictly handle group filter
    if groups_id:
        filters["groups_id_id"] = groups_id
    else:
        filters["groups_id__isnull"] = True

    # Version language filter
    if is_version == "english":
        filters["is_english"] = True
    elif is_version == "bangla":
        filters["is_bangla"] = True

    # Query filtered records
    policies = half_year_roll_section_change_policy.objects.filter(**filters)

    if not policies.exists():
        return JsonResponse({
            "success": False,
            "data": [],
            "msg": "Class Roll Section Wise Policy Not Found for this Selected Criteria. Please Create First ..."
        })

    data = [
        {
            "section_id": rec.section_id_id,
            "section_name": rec.section_id.section_name,
            "from_roll": rec.from_roll,
            "to_roll": rec.to_roll,
            # Optional: include flags if your model has them
            "is_invd_flag": getattr(rec, "is_invd_flag", False),
            "is_group_flag": getattr(rec, "is_group_flag", False),
        }
        for rec in policies
    ]

    return JsonResponse({"success": True, "data": data})


# ===================================================================================
# Annual exam policy 
# ===================================================================================

@login_required()
def annualExamPercentancePolicyManagerAPI(request):

    classs = in_class.objects.filter(is_active=True).values('class_id', 'class_name').order_by('class_id')
    
    context = {
        'classs': classs,
    }

    return render(request, 'policy_setup/annual_policy/annual_exam_percentance_policy.html', context)


@csrf_exempt
@login_required()
def saveAnnualExamPercentancePolicyAPI(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "errmsg": "Invalid Request"})

    try:
        org_id = request.POST.get("org")
        year = request.POST.get("is_aepp_year")
        version = request.POST.get("is_version")

        # Determine version flags
        is_english = True if version == "english" else False
        is_bangla = True if version == "bangla" else False

        class_ids = request.POST.getlist("class_id[]")
        half_pers = request.POST.getlist("half_yearly_per[]")
        annual_pers = request.POST.getlist("annual_per[]")

        if not class_ids:
            return JsonResponse({"success": False, "errmsg": "No Class Data Found!"})

        with transaction.atomic():

            # -----------------------------------------------------------
            # DELETE EXISTING RECORDS IF SAME ORG + YEAR + VERSION EXISTS
            # -----------------------------------------------------------
            annual_exam_percentance_policy.objects.filter(
                org_id_id=org_id,
                aexperpo_year=year,
                is_english=is_english,
                is_bangla=is_bangla
            ).delete()

            # -----------------------------------------------------------
            # INSERT NEW RECORDS
            # -----------------------------------------------------------
            for i, class_id in enumerate(class_ids):

                half = half_pers[i] if i < len(half_pers) else 0
                annual = annual_pers[i] if i < len(annual_pers) else 0

                annual_exam_percentance_policy.objects.create(
                    org_id_id=org_id,
                    aexperpo_year=year,
                    class_id_id=class_id,
                    half_yearly_per=half,
                    annual_per=annual,
                    is_english=is_english,
                    is_bangla=is_bangla,
                    ss_creator=request.user
                )

        return JsonResponse({"success": True, "msg": "Saved Successfully!"})

    except Exception as e:
        return JsonResponse({"success": False, "errmsg": str(e)})


@login_required()
def getAnnualExamPercentancePolicyListAPI(request):
    org_id = request.GET.get('org_id')
    year = request.GET.get('year')
    version = request.GET.get('version')   # english / bangla

    filters = {
        "org_id_id": org_id,
        "aexperpo_year": year,
    }

    if version == "english":
        filters["is_english"] = True
    else:
        filters["is_bangla"] = True

    data_qs = annual_exam_percentance_policy.objects.filter(**filters).select_related("class_id")

    data = []
    for row in data_qs:
        data.append({
            "class_id": row.class_id.class_id,
            "class_name": row.class_id.class_name,
            "half_yearly_per": row.half_yearly_per,
            "annual_per": row.annual_per,
        })

    return JsonResponse({"status": True, "data": data})