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
from section_setup.models import in_section
logger = logging.getLogger(__name__)
from django.contrib.auth import get_user_model
User = get_user_model()



@login_required()
def sectionSaveandUpdateManagerAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST
    section_id = data.get('section_id')
    is_english = bool(int(data.get('is_english', 0)))
    is_bangla = bool(int(data.get('is_bangla', 0)))

    try:
        with transaction.atomic():

            org_instance = organizationlst.objects.filter(org_id=data.get('section_org')).first()
            
            if is_english == is_bangla:
                return JsonResponse({'success': False, 'errmsg': 'Exactly one of English or Bangla must be selected.'})

            # Check if supplier_id is provided for an update or add operation
            if section_id and section_id.isnumeric() and int(section_id) > 0:
                # This is an update operation
                section_data = in_section.objects.get(section_id=section_id)

                # Check if the provided section_no or section_name already exists for other items
                checksection_no = in_section.objects.exclude(section_id=section_id).filter(Q(section_no=data.get('section_no')) & Q(org_id=org_instance)).exists()
                checksection_name = in_section.objects.exclude(section_id=section_id).filter(Q(section_name=data.get('section_name')) & Q(org_id=org_instance)).exists()

                if checksection_no:
                    return JsonResponse({'success': False, 'errmsg': 'Section No Already Exists'})
                elif checksection_name:
                    return JsonResponse({'success': False, 'errmsg': 'Section Name Already Exists'})
            
            else:
                # This is an add operation
                # Check if the provided section_no or section_name already exists for other items
                checksection_no = in_section.objects.filter(Q(section_no=data.get('section_no')) & Q(org_id=org_instance)).exists()
                checksection_name = in_section.objects.filter(Q(section_name=data.get('section_name')) & Q(org_id=org_instance)).exists()

                if checksection_no:
                    return JsonResponse({'success': False, 'errmsg': 'Section No Already Exists'})
                elif checksection_name:
                    return JsonResponse({'success': False, 'errmsg': 'Section Name Already Exists'})
                
                # This is an add operation
                section_data = in_section()

            # Update or set the fields based on request data
            section_data.section_no = data.get('section_no')
            section_data.section_name = data.get('section_name')
            section_data.org_id = org_instance
            section_data.is_english = is_english
            section_data.is_bangla = is_bangla
            section_data.is_active = data.get('is_active', 0)
            section_data.ss_creator = request.user
            section_data.ss_modifier = request.user
            section_data.save()
            
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
def getSectionDataManagerAPI(request):
    sectionoption = request.GET.get('sectionoption')
    is_version = request.GET.get('versionSecoption')
    section_search_query = request.GET.get('section_search_query', '')
    section_org_filter = request.GET.get('section_org_filter', '')

    filter_kwargs = Q()  # Initialize an empty Q object

    # Add search conditions only if section_search_query is not empty
    if section_search_query:
        filter_kwargs |= Q(section_name__icontains=section_search_query) | Q(section_no__icontains=section_search_query)

    # Add org_id filter condition only if org_id_wise_filter is not empty
    if section_org_filter:
        filter_kwargs &= Q(org_id=section_org_filter)

    # Add is_active filter condition based on typeoption
    if sectionoption == 'true':
        filter_kwargs &= Q(is_active=True)
    elif sectionoption == 'false':
        filter_kwargs &= Q(is_active=False)
        
    if is_version == 'english':
        filter_kwargs &= Q(is_english=True)
    if is_version == 'bangla':
        filter_kwargs &= Q(is_bangla=True)

    section_data = in_section.objects.filter(filter_kwargs)

    data = []
    for sec_item in section_data:
        org_name = sec_item.org_id.org_name if sec_item.org_id else None
        data.append({
            'section_id': sec_item.section_id,
            'section_no': sec_item.section_no,
            'section_name': sec_item.section_name,
            'org_name': org_name,
            'is_active': sec_item.is_active
        })

    return JsonResponse({'data': data})


@login_required()
def selectSectionDataManagerAPI(request, section_id):

    try:
        section_list = get_object_or_404(in_section, section_id=section_id)

        section_Dtls = []

        section_Dtls.append({
            'section_id': section_list.section_id,
            'section_no': section_list.section_no,
            'section_name': section_list.section_name,
            'org_name': section_list.org_id.org_name,
            'is_english': section_list.is_english,
            'is_bangla': section_list.is_bangla,
            'is_active': section_list.is_active,
        })

        context = {
            'section_Dtls': section_Dtls,
        }

        return JsonResponse(context)
    except Exception as e:
        return JsonResponse({'error': str(e)})