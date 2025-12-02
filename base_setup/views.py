from django.db.models import Q
from audioop import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, Http404
from django.contrib import messages
from django.db import transaction, IntegrityError
from defaults_exam_mode.models import defaults_exam_modes, in_letter_grade_mode
from exam_type.models import in_exam_type
from organizations.models import organizationlst
from class_setup.models import in_class
from groups_setup.models import in_groups
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def baseSetupManagerAPI(request):
    
    exam_type = in_exam_type.objects.filter(is_active=True).all()
    exam_mode = defaults_exam_modes.objects.filter(is_active=True).all()
    letter_grade = in_letter_grade_mode.objects.filter(is_active=True).all()
    
    context = {
        'exam_type': exam_type,
        'exam_mode': exam_mode,
        'letter_grade': letter_grade,
    }
    
    return render(request, 'base_setup/base_setup.html', context)