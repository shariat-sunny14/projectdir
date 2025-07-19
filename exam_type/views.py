from django.db.models import Q
from audioop import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, Http404
from django.contrib import messages
from django.db import transaction, IntegrityError
from organizations.models import organizationlst
from exam_type.models import in_exam_type
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def examTypeSaveandUpdateManagerAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST
    exam_type_id = data.get('exam_type_id')

    try:
        with transaction.atomic():

            org_instance = organizationlst.objects.filter(org_id=data.get('org')).first()

            # Check if supplier_id is provided for an update or add operation
            if exam_type_id and exam_type_id.isnumeric() and int(exam_type_id) > 0:
                # This is an update operation
                type_data = in_exam_type.objects.get(exam_type_id=exam_type_id)

                # Check if the provided exam_type_no or exam_type_name already exists for other items
                checkexam_type_no = in_exam_type.objects.exclude(exam_type_id=exam_type_id).filter(Q(exam_type_no=data.get('exam_type_no')) & Q(org_id=org_instance)).exists()
                checkexam_type_name = in_exam_type.objects.exclude(exam_type_id=exam_type_id).filter(exam_type_name=data.get('exam_type_name'), org_id=org_instance).exists()

                if checkexam_type_no:
                    return JsonResponse({'success': False, 'errmsg': 'Exam Type No. Already Exists'})
                elif checkexam_type_name:
                    return JsonResponse({'success': False, 'errmsg': 'Exam Type Name Already Exists'})
            
            else:
                # This is an add operation
                # Check if the provided exam_type_no or exam_type_name already exists for other items
                checkexam_type_no = in_exam_type.objects.filter(exam_type_no=data.get('exam_type_no'), org_id=org_instance).exists()
                checkexam_type_name = in_exam_type.objects.filter(exam_type_name=data.get('exam_type_name'), org_id=org_instance).exists()

                if checkexam_type_no:
                    return JsonResponse({'success': False, 'errmsg': 'Exam Type No. Already Exists'})
                elif checkexam_type_name:
                    return JsonResponse({'success': False, 'errmsg': 'Exam Type Name Already Exists'})
                
                # This is an add operation
                type_data = in_exam_type()

            # Update or set the fields based on request data
            type_data.exam_type_no = data.get('exam_type_no')
            type_data.exam_type_name = data.get('exam_type_name')
            type_data.org_id = org_instance
            type_data.is_active = data.get('is_active', 0)
            type_data.ss_creator = request.user
            type_data.ss_modifier = request.user
            type_data.save()
            
            resp['success'] = True
            resp['msg'] = 'Saved successfully'
    except Exception as e:
        resp['errmsg'] = str(e)

    return JsonResponse(resp)


@login_required()
def getExamTypeDataManagerAPI(request):
    typeoption = request.GET.get('typeoption')
    type_search_query = request.GET.get('type_search_query', '')
    org_id_wise_filter = request.GET.get('org_filter', '')

    filter_kwargs = Q()  # Initialize an empty Q object

    # Add search conditions only if type_search_query is not empty
    if type_search_query:
        filter_kwargs |= Q(exam_type_name__icontains=type_search_query) | Q(exam_type_no__icontains=type_search_query)

    # Add org_id filter condition only if org_id_wise_filter is not empty
    if org_id_wise_filter:
        filter_kwargs &= Q(org_id=org_id_wise_filter)

    # Add is_active filter condition based on typeoption
    if typeoption == 'true':
        filter_kwargs &= Q(is_active=True)
    elif typeoption == 'false':
        filter_kwargs &= Q(is_active=False)

    type_data = in_exam_type.objects.filter(filter_kwargs)

    data = []
    for type_item in type_data:
        org_name = type_item.org_id.org_name if type_item.org_id else None
        data.append({
            'exam_type_id': type_item.exam_type_id,
            'exam_type_no': type_item.exam_type_no,
            'exam_type_name': type_item.exam_type_name,
            'org_name': org_name,
            'is_active': type_item.is_active
        })

    return JsonResponse({'data': data})


@login_required()
def selectExamTypeDataManagerAPI(request, exam_type_id):

    try:
        type_list = get_object_or_404(in_exam_type, exam_type_id=exam_type_id)

        type_Dtls = []

        type_Dtls.append({
            'exam_type_id': type_list.exam_type_id,
            'exam_type_no': type_list.exam_type_no,
            'exam_type_name': type_list.exam_type_name,
            'org_name': type_list.org_id.org_name,
            'is_active': type_list.is_active,
        })

        context = {
            'type_Dtls': type_Dtls,
        }

        return JsonResponse(context)
    except Exception as e:
        return JsonResponse({'error': str(e)})