from django.db.models import Q
from audioop import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, Http404
from django.contrib import messages
from django.db import transaction, IntegrityError
from organizations.models import organizationlst
from shift_setup.models import in_shifts
from django.contrib.auth import get_user_model
User = get_user_model()



@login_required()
def shiftsSaveandUpdateManagerAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST
    shift_id = data.get('shift_id')

    try:
        with transaction.atomic():

            org_instance = organizationlst.objects.filter(org_id=data.get('org')).first()

            # Check if supplier_id is provided for an update or add operation
            if shift_id and shift_id.isnumeric() and int(shift_id) > 0:
                # This is an update operation
                shiftData = in_shifts.objects.get(shift_id=shift_id)

                # Check if the provided shift_no or shift_name already exists for other items
                checkshift_no = in_shifts.objects.exclude(shift_id=shift_id).filter(Q(shift_no=data.get('shift_no')) & Q(org_id=org_instance)).exists()
                checkshift_name = in_shifts.objects.exclude(shift_id=shift_id).filter(Q(shift_name=data.get('shift_name')) & Q(org_id=org_instance)).exists()

                if checkshift_no:
                    return JsonResponse({'success': False, 'errmsg': 'Shifts No Already Exists'})
                elif checkshift_name:
                    return JsonResponse({'success': False, 'errmsg': 'Shifts Name Already Exists'})
            
            else:
                # This is an add operation
                # Check if the provided shift_no or shift_name already exists for other items
                checkshift_no = in_shifts.objects.filter(Q(shift_no=data.get('shift_no')) & Q(org_id=org_instance)).exists()
                checkshift_name = in_shifts.objects.filter(Q(shift_name=data.get('shift_name')) & Q(org_id=org_instance)).exists()

                if checkshift_no:
                    return JsonResponse({'success': False, 'errmsg': 'Shifts No Already Exists'})
                elif checkshift_name:
                    return JsonResponse({'success': False, 'errmsg': 'Shifts Name Already Exists'})
                
                # This is an add operation
                shiftData = in_shifts()

            # Update or set the fields based on request data
            shiftData.shift_no = data.get('shift_no')
            shiftData.shift_name = data.get('shift_name')
            shiftData.org_id = org_instance
            shiftData.is_active = data.get('is_active', 0)
            shiftData.ss_creator = request.user
            shiftData.ss_modifier = request.user
            shiftData.save()
            
            resp['success'] = True
            resp['msg'] = 'Saved successfully'
    except Exception as e:
        resp['errmsg'] = str(e)

    return JsonResponse(resp)


@login_required()
def getShiftsDataManagerAPI(request):
    shiftoption = request.GET.get('shiftoption')
    shift_search_query = request.GET.get('shift_search_query', '')
    org_filter = request.GET.get('org_filter', '')

    filter_kwargs = Q()  # Initialize an empty Q object

    # Add search conditions only if shift_search_query is not empty
    if shift_search_query:
        filter_kwargs |= Q(shift_name__icontains=shift_search_query) | Q(shift_no__icontains=shift_search_query)

    # Add org_id filter condition only if org_id_wise_filter is not empty
    if org_filter:
        filter_kwargs &= Q(org_id=org_filter)

    # Add is_active filter condition based on typeoption
    if shiftoption == 'true':
        filter_kwargs &= Q(is_active=True)
    elif shiftoption == 'false':
        filter_kwargs &= Q(is_active=False)

    shiftData = in_shifts.objects.filter(filter_kwargs)

    data = []
    for shiftItem in shiftData:
        org_name = shiftItem.org_id.org_name if shiftItem.org_id else None
        data.append({
            'shift_id': shiftItem.shift_id,
            'shift_no': shiftItem.shift_no,
            'shift_name': shiftItem.shift_name,
            'org_name': org_name,
            'is_active': shiftItem.is_active
        })

    return JsonResponse({'data': data})


@login_required()
def selectShiftsDataManagerAPI(request, shift_id):

    try:
        shiftList = get_object_or_404(in_shifts, shift_id=shift_id)

        shiftsDtls = []

        shiftsDtls.append({
            'shift_id': shiftList.shift_id,
            'shift_no': shiftList.shift_no,
            'shift_name': shiftList.shift_name,
            'org_name': shiftList.org_id.org_name,
            'is_active': shiftList.is_active,
        })

        context = {
            'shiftsDtls': shiftsDtls,
        }

        return JsonResponse(context)
    except Exception as e:
        return JsonResponse({'error': str(e)})