import json
from django.db.models import Q
from audioop import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, Http404
from django.contrib import messages
from django.db import transaction, IntegrityError
from exam_type.models import in_exam_type
from organizations.models import organizationlst
from class_setup.models import in_class
from defaults_exam_mode.models import ExamModeTypeMap, defaults_exam_modes, in_exam_modes
from subject_setup.models import in_subjects
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def defaultsExamModesSetupManagerAPI(request):
    
    examtypelist = in_exam_type.objects.filter(is_active=True).all()

    context = {
        'examtypelist': examtypelist,
    }
    
    return render(request, 'exam_mode/defaults_exam_modes_setup.html', context)


@login_required()
def get_exam_modes_combinedAPI(request):
    org_id = request.GET.get("org")
    class_id = request.GET.get("class_id")
    subject_id = request.GET.get("subject_id")
    exam_type_id = request.GET.get("exam_type_id")
    is_version = request.GET.get("is_version")  # english / bangla

    # -------------------------
    # Base Filters
    # -------------------------
    base_filters = {
        "org_id": org_id,
        "class_id": class_id,
        "exam_type_id": exam_type_id,
    }
    if is_version == "english":
        base_filters["is_english"] = True
    elif is_version == "bangla":
        base_filters["is_bangla"] = True

    # -------------------------
    # 1. ExamModeTypeMap থেকে default setup
    # -------------------------
    exam_modes_map = ExamModeTypeMap.objects.filter(**base_filters).select_related("def_mode_id")

    # -------------------------
    # 2. in_exam_modes থেকে saved data
    # -------------------------
    in_modes_filters = {
        "org_id_id": org_id,
        "class_id_id": class_id,
        "subjects_id_id": subject_id,
        "exam_type_id_id": exam_type_id,
    }
    if is_version == "english":
        in_modes_filters["is_english"] = True
    else:
        in_modes_filters["is_bangla"] = True

    in_modes_qs = in_exam_modes.objects.filter(**in_modes_filters)
    in_modes_dict = {obj.is_exam_modes_id: obj for obj in in_modes_qs}

    # -------------------------
    # Merge Logic
    # -------------------------
    combined_modes = []
    for i, q in enumerate(exam_modes_map, start=1):
        saved_obj = in_modes_dict.get(q.def_mode_id.def_mode_id)

        if saved_obj:
            combined_modes.append({
                "sl": i,
                "def_mode_id": saved_obj.is_exam_modes_id,
                "exam_mode_id": saved_obj.exam_mode_id,
                "is_mode_name": saved_obj.is_exam_modes.is_mode_name,
                "is_default_marks": saved_obj.is_default_marks,
                "is_pass_marks": saved_obj.is_pass_marks,
                "is_active": saved_obj.is_active,
                "is_saved": True,
            })
        else:
            combined_modes.append({
                "sl": i,
                "def_mode_id": q.def_mode_id.def_mode_id,
                "exam_mode_id": None,
                "is_mode_name": q.def_mode_id.is_mode_name,
                "is_default_marks": getattr(q, "default_marks", 0),
                "is_pass_marks": getattr(q, "pass_marks", 0),
                "is_active": q.def_mode_id.is_active,
                "is_saved": False,
            })

    return JsonResponse({
        "status": "ok",
        "modes": combined_modes
    })
    

@login_required()
def getExamModesListManagerAPI(request):
    org_id = request.GET.get("org")
    class_id = request.GET.get("class_id")
    subject_id = request.GET.get("subject_id")
    exam_type_id = request.GET.get("exam_type_id")
    is_version = request.GET.get("is_version")  # english / bangla

    # -------------------------
    # Base Filters
    # -------------------------
    base_filters = {
        "org_id": org_id,
        "class_id": class_id,
        "exam_type_id": exam_type_id,
    }
    if is_version == "english":
        base_filters["is_english"] = True
    elif is_version == "bangla":
        base_filters["is_bangla"] = True

    # -------------------------
    # 1. ExamModeTypeMap থেকে default setup
    # -------------------------
    exam_modes_map = ExamModeTypeMap.objects.filter(**base_filters).select_related("def_mode_id")

    # -------------------------
    # 2. in_exam_modes থেকে saved data
    # -------------------------
    in_modes_filters = {
        "org_id_id": org_id,
        "class_id_id": class_id,
        "subjects_id_id": subject_id,
        "exam_type_id_id": exam_type_id,
    }
    if is_version == "english":
        in_modes_filters["is_english"] = True
    else:
        in_modes_filters["is_bangla"] = True

    # সব saved data (active + inactive)
    in_modes_all = in_exam_modes.objects.filter(**in_modes_filters)
    # Active data dict
    in_modes_dict = {obj.is_exam_modes_id: obj for obj in in_modes_all if obj.is_active}
    # Inactive def_mode list
    inactive_mode_ids = {obj.is_exam_modes_id for obj in in_modes_all if not obj.is_active}

    # -------------------------
    # Merge Logic
    # -------------------------
    combined_modes = []
    for i, q in enumerate(exam_modes_map, start=1):
        # যদি inactive list-এ থাকে, skip করব
        if q.def_mode_id.def_mode_id in inactive_mode_ids:
            continue

        saved_obj = in_modes_dict.get(q.def_mode_id.def_mode_id)

        if saved_obj:
            combined_modes.append({
                "sl": i,
                "def_mode_id": saved_obj.is_exam_modes_id,
                "exam_mode_id": saved_obj.exam_mode_id,
                "is_mode_name": saved_obj.is_exam_modes.is_mode_name,
                "is_default_marks": saved_obj.is_default_marks,
                "is_pass_marks": saved_obj.is_pass_marks,
                "is_active": saved_obj.is_active,
                "is_saved": True,
            })
        else:
            combined_modes.append({
                "sl": i,
                "def_mode_id": q.def_mode_id.def_mode_id,
                "exam_mode_id": None,
                "is_mode_name": q.def_mode_id.is_mode_name,
                "is_default_marks": getattr(q, "default_marks", 0),
                "is_pass_marks": getattr(q, "pass_marks", 0),
                "is_active": q.def_mode_id.is_active,
                "is_saved": False,
            })

    return JsonResponse({
        "status": "ok",
        "modes": combined_modes
    })


@login_required()
def saveDefaultsExamModesSetupManagerAPI(request):
    resp = {'status': 'failed', 'errmsg': 'Failed ...'}
    data = request.POST

    try:
        org_id = data.get("org")
        class_id = data.get("is_class_id")
        subject_id = data.get("is_subjects")
        exam_type_id = data.get("is_exam_type")
        is_version = data.get("is_version")
        
        if is_version == 'english':
            is_english = True
            is_bangla = False
        if is_version == 'bangla':
            is_english = False
            is_bangla = True

        with transaction.atomic():
            org = organizationlst.objects.get(org_id=org_id)
            class_obj = in_class.objects.get(class_id=class_id)
            subject = in_subjects.objects.get(subjects_id=subject_id)
            exam_type = in_exam_type.objects.get(exam_type_id=exam_type_id)
            
            if org and class_obj and subject and exam_type:
                in_exam_modes.objects.filter(org_id=org, class_id=class_obj, subjects_id=subject, exam_type_id=exam_type, is_english=is_english, is_bangla=is_bangla).delete()

            zip_datas = zip(
                data.getlist('def_mode_id[]'),
                data.getlist('is_default_marks[]'),
                data.getlist('is_pass_marks[]'),
                data.getlist('is_active[]'),
            )

            for fields in zip_datas:
                (
                    def_mode_id, default_marks, pass_marks, is_active
                ) = fields
                
                exam_modes_instance = defaults_exam_modes.objects.get(def_mode_id=def_mode_id)

                in_exam_modesDtl = in_exam_modes.objects.create(
                    org_id=org,
                    class_id=class_obj,
                    subjects_id=subject,
                    exam_type_id=exam_type,
                    is_exam_modes=exam_modes_instance,
                    is_default_marks=default_marks,
                    is_pass_marks=pass_marks,
                    is_active=is_active,
                    is_english=is_english,
                    is_bangla=is_bangla,
                    ss_creator=request.user,
                    ss_modifier=request.user,
                )

        return JsonResponse({'success': True, 'msg': 'Result finalization saved successfully.'})

    except organizationlst.DoesNotExist:
        resp['errmsg'] = 'Invalid organization ID.'
    except in_subjects.DoesNotExist:
        resp['errmsg'] = 'Invalid subject ID.'
    except in_exam_type.DoesNotExist:
        resp['errmsg'] = 'Invalid exam type ID.'
    except Exception as e:
        print("Unhandled Error:", str(e))
        resp['errmsg'] = str(e)

    return HttpResponse(json.dumps(resp), content_type="application/json")

