import json
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.db.models import Q, ExpressionWrapper, F, FloatField, Sum, Count
from django.contrib.auth.decorators import login_required
from . models import login_themes
from django.contrib.auth import get_user_model
User = get_user_model()

# Create your views here.
@login_required
def loginThemeSetupManagerAPI(request):
    # Retrieve the latest login theme, or use a default if none exists
    logintheme = login_themes.objects.all()

    if logintheme.exists():
        latest_theme = logintheme.latest('login_theme_id')
        logintheme_name = latest_theme.login_theme_name
    else:
        logintheme_name = 'default_theme'  # Set a fallback name if no theme exists

    context = {
        'logintheme_name': logintheme_name,
    }
    
    return render(request, 'themes/login_themes/login_themes.html', context)


@login_required
def saveUpdateLoginThemeTemplatesAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}
    data = request.POST

    try:
        # Retrieve login_theme from POST data
        login_themename = data.get('login_theme')
        if not login_themename:
            raise ValueError("The 'Login Theme' field is required.")

        with transaction.atomic():
            # Delete all existing records in the login_themes table
            login_themes.objects.all().delete()

            # Create a new login theme record
            logintheme = login_themes.objects.create(
                login_theme_name=login_themename,
                ss_creator=request.user,
                ss_modifier=request.user,
            )

            # Prepare success response
            resp['success'] = True
            resp['msg'] = 'Login theme created successfully.'

    except ValueError as ve:
        resp['errmsg'] = f"Validation error: {str(ve)}"
    except Exception as e:
        resp['errmsg'] = f"An unexpected error occurred: {str(e)}"

    return JsonResponse(resp)