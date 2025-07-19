from django.db.models import Q
from audioop import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, Http404
from django.contrib import messages
from django.db import transaction, IntegrityError
from organizations.models import organizationlst
from subject_setup.models import in_subjects
from class_setup.models import in_class
from groups_setup.models import in_groups
from django.contrib.auth import get_user_model
User = get_user_model()



@login_required()
def subjectsSaveandUpdateManagerAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST
    subjects_id = data.get('subjects_id')
    groups_id = data.get('is_groups_id')

    try:
        with transaction.atomic():

            org_instance = organizationlst.objects.filter(org_id=data.get('subjects_org')).first()
            class_instance = in_class.objects.filter(class_id=data.get('is_class_id')).first()
            

            if groups_id:
                groups_instance = in_groups.objects.filter(groups_id=groups_id).first()
            else:
                groups_instance = None

            # Check if supplier_id is provided for an update or add operation
            if subjects_id and subjects_id.isnumeric() and int(subjects_id) > 0:
                # This is an update operation
                subjects_data = in_subjects.objects.get(subjects_id=subjects_id)

                # Check if the provided subjects_no or subjects_name already exists for other items
                checksubjects_no = in_subjects.objects.exclude(subjects_id=subjects_id).filter(Q(subjects_no=data.get('subjects_no')) & Q(org_id=org_instance)).exists()
                checksubjects_name = in_subjects.objects.exclude(subjects_id=subjects_id).filter(Q(subjects_name=data.get('subjects_name')) & Q(org_id=org_instance) & Q(class_id=class_instance) & Q(groups_id=groups_instance)).exists()

                if checksubjects_no:
                    return JsonResponse({'success': False, 'errmsg': 'Subjects No Already Exists'})
                elif checksubjects_name:
                    return JsonResponse({'success': False, 'errmsg': 'Subjects Name Already Exists'})
            
            else:
                # This is an add operation
                # Check if the provided subjects_no or subjects_name already exists for other items
                checksubjects_no = in_subjects.objects.filter(Q(subjects_no=data.get('subjects_no')) & Q(org_id=org_instance)).exists()
                checksubjects_name = in_subjects.objects.filter(Q(subjects_name=data.get('subjects_name')) & Q(org_id=org_instance) & Q(class_id=class_instance) & Q(groups_id=groups_instance)).exists()

                if checksubjects_no:
                    return JsonResponse({'success': False, 'errmsg': 'Subjects No Already Exists'})
                elif checksubjects_name:
                    return JsonResponse({'success': False, 'errmsg': 'Subjects Name Already Exists'})
                
                # This is an add operation
                subjects_data = in_subjects()

            # Update or set the fields based on request data
            subjects_data.subjects_no = data.get('subjects_no')
            subjects_data.subjects_name = data.get('subjects_name')
            subjects_data.is_marks = data.get('is_marks')
            subjects_data.org_id = org_instance
            subjects_data.class_id = class_instance
            subjects_data.groups_id = groups_instance
            subjects_data.is_active = data.get('is_active', 0)
            subjects_data.ss_creator = request.user
            subjects_data.ss_modifier = request.user
            subjects_data.save()
            
            resp['success'] = True
            resp['msg'] = 'Saved successfully'
    except Exception as e:
        resp['errmsg'] = str(e)

    return JsonResponse(resp)


@login_required()
def getSubjectsDataManagerAPI(request):
    subjectsoption = request.GET.get('subjectsoption')
    subjects_search_query = request.GET.get('subjects_search_query', '')
    subjects_org_filter = request.GET.get('subjects_org_filter', '')
    class_name_filter = request.GET.get('class_name_filter', '')
    groups_name_filter = request.GET.get('groups_name_filter', '')

    filter_kwargs = Q()  # Initialize an empty Q object

    # Add search conditions only if subjects_search_query is not empty
    if subjects_search_query:
        filter_kwargs |= Q(subjects_name__icontains=subjects_search_query) | Q(subjects_no__icontains=subjects_search_query)

    # Add org_id filter condition only if org_id_wise_filter is not empty
    if subjects_org_filter:
        filter_kwargs &= Q(org_id=subjects_org_filter)

    if class_name_filter:
        filter_kwargs &= Q(class_id=class_name_filter)

    if groups_name_filter:
        filter_kwargs &= Q(groups_id=groups_name_filter)

    # Add is_active filter condition based on typeoption
    if subjectsoption == 'true':
        filter_kwargs &= Q(is_active=True)
    elif subjectsoption == 'false':
        filter_kwargs &= Q(is_active=False)

    subjectsData = in_subjects.objects.filter(filter_kwargs)

    data = []
    for subItem in subjectsData:
        org_name = subItem.org_id.org_name if subItem.org_id else None
        data.append({
            'subjects_id': subItem.subjects_id,
            'subjects_no': subItem.subjects_no,
            'subjects_name': subItem.subjects_name,
            'org_name': org_name,
            'is_active': subItem.is_active
        })

    return JsonResponse({'data': data})


@login_required()
def selectSubjectsDataManagerAPI(request, subjects_id):

    try:
        subjects_list = get_object_or_404(in_subjects, subjects_id=subjects_id)

        subjectsDtls = []

        subjectsDtls.append({
            'subjects_id': subjects_list.subjects_id,
            'subjects_no': subjects_list.subjects_no,
            'subjects_name': subjects_list.subjects_name,
            'is_marks': subjects_list.is_marks,
            'org_name': subjects_list.org_id.org_name,
            'is_class_name': subjects_list.class_id.class_name,
            'is_groups_name': subjects_list.groups_id.groups_name if subjects_list.groups_id else None,
            'is_active': subjects_list.is_active,
        })

        context = {
            'subjectsDtls': subjectsDtls,
        }

        return JsonResponse(context)
    except Exception as e:
        return JsonResponse({'error': str(e)})