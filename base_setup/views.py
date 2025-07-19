from django.db.models import Q
from audioop import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, Http404
from django.contrib import messages
from django.db import transaction, IntegrityError
from organizations.models import organizationlst
from class_setup.models import in_class
from groups_setup.models import in_groups
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def baseSetupManagerAPI(request):
    user = request.user

    if user.is_superuser:
        # If the user is a superuser, retrieve all organizations
        org_list = organizationlst.objects.filter(is_active=True).all()
    elif user.org_id is not None:
        # If the user has an associated organization, retrieve only that organization
        org_list = organizationlst.objects.filter(is_active=True, org_id=user.org_id).all()
    else:
        # If neither a superuser nor associated with an organization, set organizations to an empty list or handle as needed
        org_list = []
    
    class_list = in_class.objects.filter(is_active=True).all()
    groups_list = in_groups.objects.filter(is_active=True).all()
    
    context = {
        'class_list': class_list,
        'groups_list': groups_list,
        'org_list': org_list,
    }
    
    return render(request, 'base_setup/base_setup.html', context)