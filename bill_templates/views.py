import json
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.db.models import Q, ExpressionWrapper, F, FloatField, Sum, Count
from django.contrib.auth.decorators import login_required
from django.forms.models import model_to_dict
from organizations.models import organizationlst
from django.shortcuts import render
from . models import in_apps_templates
from django.contrib.auth import get_user_model
User = get_user_model()

# Create your views here.
@login_required
def billTemplateManagerAPI(request):
    user = request.user

    # Retrieve organization list based on user privileges
    if user.is_superuser:
        org_list = organizationlst.objects.filter(is_active=True)
    elif user.org_id is not None:
        org_list = organizationlst.objects.filter(is_active=True, org_id=user.org_id)
    else:
        org_list = []

    context = {
        'org_list': org_list,
    }

    return render(request, 'bill_templates/bill_templates.html', context)


@login_required
def getBillTempOptionManagerAPI(request):
    org_id = request.GET.get('org_filter')
    
    if org_id:
        try:
            # Fetch the organization to get the org_name
            organization = organizationlst.objects.get(org_id=org_id)
            # Retrieve appstemplate related to this organization
            appstemplate = in_apps_templates.objects.filter(org_id=org_id)
            
            data = [
                {
                    'temp_id': appstemp.temp_id,
                    'org_name': organization.org_name,  # Use organization instance to get org_name
                    'billing_temp': appstemp.billing_temp,
                    'inv_can_temp': appstemp.inv_can_temp,
                    'item_can_temp': appstemp.item_can_temp,
                    'refund_coll_temp': appstemp.refund_coll_temp,
                    'due_coll_temp': appstemp.due_coll_temp,
                    'ss_creator': appstemp.ss_creator.username,
                }
                for appstemp in appstemplate
            ]
        except organizationlst.DoesNotExist:
            # If the organization does not exist, return an empty list
            data = []
    else:
        data = []

    return JsonResponse(data, safe=False)


@login_required
def saveAppsTemplateManagerAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST

    try:
        # Get the form data
        org_id = data.get('org')
        bill_template = data.get('bill_template')  # This corresponds to receipt_name
        inv_cancel_temps = data.get('inv_cancel_temps')
        item_cancel_temps = data.get('item_cancel_temps')
        refund_coll_temps = data.get('refund_coll_temps')
        due_coll_temps = data.get('due_coll_temps')

        # Fetch the organization instance
        org_instance = get_object_or_404(organizationlst, org_id=org_id)

        with transaction.atomic():
            # Use get_or_create to find the existing record or create a new one
            orgTemp_data, created = in_apps_templates.objects.get_or_create(
                org_id=org_instance,
                defaults={
                    'billing_temp': bill_template,  # Use correct field name from the model
                    'inv_can_temp': inv_cancel_temps,
                    'item_can_temp': item_cancel_temps,
                    'refund_coll_temp': refund_coll_temps,
                    'due_coll_temp': due_coll_temps,
                    'ss_creator': request.user,
                    'ss_modifier': request.user,
                }
            )

            if not created:
                # Update fields if the record already exists
                orgTemp_data.billing_temp = bill_template  # Use correct field name
                orgTemp_data.inv_can_temp = inv_cancel_temps
                orgTemp_data.item_can_temp = item_cancel_temps
                orgTemp_data.refund_coll_temp = refund_coll_temps
                orgTemp_data.due_coll_temp = due_coll_temps
                orgTemp_data.ss_modifier = request.user
                orgTemp_data.save()

            resp['success'] = True
            resp['msg'] = 'Saved successfully' if not created else 'Created successfully'

    except ValueError as ve:
        resp['errmsg'] = str(ve)
    except Exception as e:
        resp['errmsg'] = f"An error occurred: {str(e)}"

    return JsonResponse(resp)