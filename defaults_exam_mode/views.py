from django.db.models import Q
from audioop import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, Http404
from django.contrib import messages
from django.db import transaction, IntegrityError
from organizations.models import organizationlst
from class_setup.models import in_class
from defaults_exam_mode.models import in_exam_modes
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def defaultsExamModesSetupManagerAPI(request):
    
    return render(request, 'exam_mode/defaults_exam_modes_setup.html')


@login_required()
def saveDefaultsExamModesSetupManagerAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}

    if request.method == 'POST':
        data = request.POST
        class_id = data.get('is_class_id')
        org_id = data.get('org')

        if not class_id or not org_id:
            return JsonResponse({'success': False, 'errmsg': 'Class or Organization missing'})

        org_instance = organizationlst.objects.filter(org_id=org_id).first()
        class_instance = in_class.objects.filter(class_id=class_id).first()

        if not org_instance or not class_instance:
            return JsonResponse({'success': False, 'errmsg': 'Invalid class or organization'})

        try:
            # Extract exam mode keys
            exam_modes_keys = []
            for key in data.keys():
                if key.startswith("is_exam_modes["):
                    mode_name = key[len("is_exam_modes["):-1]  # extract 'CQ' from 'is_exam_modes[CQ]'
                    exam_modes_keys.append(mode_name)

            with transaction.atomic():
                # Clear existing records
                in_exam_modes.objects.filter(org_id=org_instance, class_id=class_instance).delete()

                for mode_key in exam_modes_keys:
                    exam_mode = data.get(f"is_exam_modes[{mode_key}]")
                    default_mark = data.get(f"is_default_marks[{mode_key}]") or 0
                    is_active = data.get(f"is_active[{mode_key}]") == '1'

                    new_mode = in_exam_modes(
                        org_id=org_instance,
                        class_id=class_instance,
                        is_exam_modes=exam_mode,
                        is_default_marks=int(default_mark),
                        is_active=is_active,
                        is_common=False,
                        ss_creator=request.user,
                        ss_modifier=request.user,
                    )
                    new_mode.save()

                resp['success'] = True
                resp['msg'] = 'Exam modes saved successfully'

        except Exception as e:
            resp['errmsg'] = str(e)

    return JsonResponse(resp)


@login_required()
def getDefaultsExamModesManagerAPI(request):
    modes_search_query = request.GET.get('modes_search_query', '')
    org_filter = request.GET.get('org_filter', '')
    class_filter = request.GET.get('class_filter', '')

    filter_kwargs = Q()

    if modes_search_query:
        filter_kwargs |= Q(class_id__class_name__icontains=modes_search_query) | Q(class_id__class_no__icontains=modes_search_query)

    if org_filter:
        filter_kwargs &= Q(org_id=org_filter)

    if class_filter:
        filter_kwargs &= Q(class_id=class_filter)

    modes_data = in_exam_modes.objects.filter(filter_kwargs)

    seen = set()
    data = []

    for modesItem in modes_data:
        class_id = modesItem.class_id.class_id if modesItem.class_id else None
        org_id = modesItem.org_id.org_id if modesItem.org_id else None

        key = (class_id, org_id)
        if key in seen:
            continue
        seen.add(key)

        data.append({
            'class_id': class_id,
            'class_No': modesItem.class_id.class_no if modesItem.class_id else None,
            'class_name': modesItem.class_id.class_name if modesItem.class_id else None,
            'org_id': org_id,
            'org_name': modesItem.org_id.org_name if modesItem.org_id else None,
        })

    return JsonResponse({'data': data})


@login_required()
def selectDefaultsExamModesManagerAPI(request, class_id):

    try:
        # Get all exam modes for the given class
        modes_queryset = in_exam_modes.objects.filter(class_id=class_id)

        if not modes_queryset.exists():
            return JsonResponse({'error': 'No exam modes found for this class.'}, status=404)

        # Take class and org details from the first item
        first_mode = modes_queryset.first()
        class_info = {
            'class_id': first_mode.class_id.class_id if first_mode.class_id else None,
            'class_name': first_mode.class_id.class_name if first_mode.class_id else None,
            'org_name': first_mode.org_id.org_name if first_mode.org_id else None,
        }

        modesDtls = []
        for mode in modes_queryset:
            modesDtls.append({
                'is_exam_modes': mode.is_exam_modes,
                'is_default_marks': mode.is_default_marks,
                'is_active': mode.is_active,
            })

        # Combine and return
        response_data = {
            **class_info,
            'modesDtls': modesDtls
        }

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)