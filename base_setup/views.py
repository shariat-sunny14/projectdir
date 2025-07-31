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
    
    return render(request, 'base_setup/base_setup.html')