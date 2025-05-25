from django.db.models import Q
from audioop import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, Http404
from django.contrib import messages
from django.db import transaction, IntegrityError
from organizations.models import organizationlst
from class_setup.models import in_class
from django.contrib.auth import get_user_model
User = get_user_model()

# Create your views here.
@login_required()
def classSaveAndUpdateManagerAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST
    class_id = data.get('class_id')

    try:
        with transaction.atomic():

            org_instance = organizationlst.objects.filter(org_id=data.get('org')).first()

            # Check if supplier_id is provided for an update or add operation
            if class_id and class_id.isnumeric() and int(class_id) > 0:
                # This is an update operation
                class_data = in_class.objects.get(class_id=class_id)

                # Check if the provided class_no or class_name already exists for other items
                checkclass_no = in_class.objects.exclude(class_id=class_id).filter(Q(class_no=data.get('class_no')) & Q(org_id=org_instance)).exists()
                checkclass_name = in_class.objects.exclude(class_id=class_id).filter(class_name=data.get('class_name'), org_id=org_instance).exists()

                if checkclass_no:
                    return JsonResponse({'success': False, 'errmsg': 'Type No. Already Exists'})
                elif checkclass_name:
                    return JsonResponse({'success': False, 'errmsg': 'Type Name Already Exists'})
            
            else:
                # This is an add operation
                # Check if the provided class_no or class_name already exists for other items
                checkclass_no = in_class.objects.filter(class_no=data.get('class_no'), org_id=org_instance).exists()
                checkclass_name = in_class.objects.filter(class_name=data.get('class_name'), org_id=org_instance).exists()

                if checkclass_no:
                    return JsonResponse({'success': False, 'errmsg': 'Type No. Already Exists'})
                elif checkclass_name:
                    return JsonResponse({'success': False, 'errmsg': 'Type Name Already Exists'})
                
                # This is an add operation
                class_data = in_class()

            # Update or set the fields based on request data
            class_data.class_no = data.get('class_no')
            class_data.class_name = data.get('class_name')
            class_data.org_id = org_instance
            class_data.allow_groups = data.get('allow_groups', 0)
            class_data.is_active = data.get('is_active', 0)
            class_data.ss_creator = request.user
            class_data.ss_modifier = request.user
            class_data.save()
            
            resp['success'] = True
            resp['msg'] = 'Saved successfully'
    except Exception as e:
        resp['errmsg'] = str(e)

    return JsonResponse(resp)


@login_required()
def getClassListDataManagerAPI(request):
    classoption = request.GET.get('classoption')
    class_search_query = request.GET.get('class_search_query', '')
    org_filter = request.GET.get('org_filter', '')

    filter_kwargs = Q()  # Initialize an empty Q object

    # Add search conditions only if class_search_query is not empty
    if class_search_query:
        filter_kwargs |= Q(class_name__icontains=class_search_query) | Q(class_no__icontains=class_search_query)

    # Add org_id filter condition only if org_filter is not empty
    if org_filter:
        filter_kwargs &= Q(org_id=org_filter)

    # Add is_active filter condition based on classoption
    if classoption == 'true':
        filter_kwargs &= Q(is_active=True)
    elif classoption == 'false':
        filter_kwargs &= Q(is_active=False)

    type_data = in_class.objects.filter(filter_kwargs)

    data = []
    for class_item in type_data:
        org_name = class_item.org_id.org_name if class_item.org_id else None
        data.append({
            'class_id': class_item.class_id,
            'class_no': class_item.class_no,
            'class_name': class_item.class_name,
            'org_name': org_name,
            'is_active': class_item.is_active
        })

    return JsonResponse({'data': data})


@login_required()
def getClassListManagerAPI(request, class_id):

    try:
        class_list = get_object_or_404(in_class, class_id=class_id)

        class_Dtls = []

        class_Dtls.append({
            'class_id': class_list.class_id,
            'class_no': class_list.class_no,
            'class_name': class_list.class_name,
            'org_name': class_list.org_id.org_name,
            'allow_groups': class_list.allow_groups,
            'is_active': class_list.is_active,
        })

        context = {
            'class_Dtls': class_Dtls,
        }

        return JsonResponse(context)
    except Exception as e:
        return JsonResponse({'error': str(e)})