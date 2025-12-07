import logging
from django.db.models import Q
from audioop import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, Http404
from user_auth.utils.save_othersaccess_context import save_othersaccess_json_for_user
from django.contrib import messages
from django.db import transaction, IntegrityError
from organizations.models import organizationlst
from groups_setup.models import in_groups
logger = logging.getLogger(__name__)
from django.contrib.auth import get_user_model
User = get_user_model()



@login_required()
def groupsSaveandUpdateManagerAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST
    groups_id = data.get('groups_id')

    try:
        with transaction.atomic():

            org_instance = organizationlst.objects.filter(org_id=data.get('groups_org')).first()

            # Check if supplier_id is provided for an update or add operation
            if groups_id and groups_id.isnumeric() and int(groups_id) > 0:
                # This is an update operation
                groups_data = in_groups.objects.get(groups_id=groups_id)

                # Check if the provided groups_no or groups_name already exists for other items
                checkgroups_no = in_groups.objects.exclude(groups_id=groups_id).filter(Q(groups_no=data.get('groups_no')) & Q(org_id=org_instance)).exists()
                checkgroups_name = in_groups.objects.exclude(groups_id=groups_id).filter(Q(groups_name=data.get('groups_name')) & Q(org_id=org_instance)).exists()

                if checkgroups_no:
                    return JsonResponse({'success': False, 'errmsg': 'Groups No Already Exists'})
                elif checkgroups_name:
                    return JsonResponse({'success': False, 'errmsg': 'Groups Name Already Exists'})
            
            else:
                # This is an add operation
                # Check if the provided groups_no or groups_name already exists for other items
                checkgroups_no = in_groups.objects.filter(Q(groups_no=data.get('groups_no')) & Q(org_id=org_instance)).exists()
                checkgroups_name = in_groups.objects.filter(Q(groups_name=data.get('groups_name')) & Q(org_id=org_instance)).exists()

                if checkgroups_no:
                    return JsonResponse({'success': False, 'errmsg': 'Groups No Already Exists'})
                elif checkgroups_name:
                    return JsonResponse({'success': False, 'errmsg': 'Groups Name Already Exists'})
                
                # This is an add operation
                groups_data = in_groups()

            # Update or set the fields based on request data
            groups_data.groups_no = data.get('groups_no')
            groups_data.groups_name = data.get('groups_name')
            groups_data.org_id = org_instance
            groups_data.is_active = data.get('is_active', 0)
            groups_data.ss_creator = request.user
            groups_data.ss_modifier = request.user
            groups_data.save()
            
            # Refresh context JSON for ALL users in this organization
            try:
                all_users = User.objects.all()
                for user in all_users:
                    save_othersaccess_json_for_user(user)
            except Exception as context_err:
                logger.warning(f"Bulk context update failed: {str(context_err)}")
            
            resp['success'] = True
            resp['msg'] = 'Saved successfully'
    except Exception as e:
        resp['errmsg'] = str(e)

    return JsonResponse(resp)


@login_required()
def getGroupsDataManagerAPI(request):
    groupsoption = request.GET.get('groupsoption')
    groups_search_query = request.GET.get('groups_search_query', '')
    groups_org_filter = request.GET.get('groups_org_filter', '')

    filter_kwargs = Q()  # Initialize an empty Q object

    # Add search conditions only if groups_search_query is not empty
    if groups_search_query:
        filter_kwargs |= Q(groups_name__icontains=groups_search_query) | Q(groups_no__icontains=groups_search_query)

    # Add org_id filter condition only if org_id_wise_filter is not empty
    if groups_org_filter:
        filter_kwargs &= Q(org_id=groups_org_filter)

    # Add is_active filter condition based on typeoption
    if groupsoption == 'true':
        filter_kwargs &= Q(is_active=True)
    elif groupsoption == 'false':
        filter_kwargs &= Q(is_active=False)

    groups_data = in_groups.objects.filter(filter_kwargs)

    data = []
    for groups_item in groups_data:
        org_name = groups_item.org_id.org_name if groups_item.org_id else None
        data.append({
            'groups_id': groups_item.groups_id,
            'groups_no': groups_item.groups_no,
            'groups_name': groups_item.groups_name,
            'org_name': org_name,
            'is_active': groups_item.is_active
        })

    return JsonResponse({'data': data})


@login_required()
def selectGroupsDataManagerAPI(request, groups_id):

    try:
        section_list = get_object_or_404(in_groups, groups_id=groups_id)

        groups_Dtls = []

        groups_Dtls.append({
            'groups_id': section_list.groups_id,
            'groups_no': section_list.groups_no,
            'groups_name': section_list.groups_name,
            'org_name': section_list.org_id.org_name,
            'is_active': section_list.is_active,
        })

        context = {
            'groups_Dtls': groups_Dtls,
        }

        return JsonResponse(context)
    except Exception as e:
        return JsonResponse({'error': str(e)})