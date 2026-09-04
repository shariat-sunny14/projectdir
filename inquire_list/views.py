import json
import sys
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.contrib import messages
from datetime import datetime, timedelta, date
from django.db import IntegrityError, transaction
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.contrib.auth.decorators import login_required
from inquire_list.models import InquiresList
from order_list.models import OrderList
from packages.models import packages_dtls, packages_head_body, packages_items
from packages.models import packages_list
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from booking_us.models import EventSchedule, Slot_Details
from user_auth.models import org_info
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def inquireListViewManagerAPI(request):
    
    return render(request, 'inquire_list/inquire_list.html')


@login_required()
def inquireListViewFromWebsiteManagerAPI(request):
    
    org_data = org_info.objects.first()
    
    context= {
        'org_data': org_data,
    }
    
    return render(request, 'inquire_list/inquire_views_website.html', context)


@csrf_exempt
@login_required()
def getInquireListManagerAPI(request):
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    # Convert dd-mm-yyyy to date objects
    try:
        from_date_obj = datetime.strptime(from_date, "%d-%m-%Y").date() if from_date else None
        to_date_obj = datetime.strptime(to_date, "%d-%m-%Y").date() if to_date else None
    except ValueError:
        from_date_obj = to_date_obj = None

    inquiries = InquiresList.objects.all()

    if from_date_obj:
        inquiries = inquiries.filter(inquire_date__gte=from_date_obj)
    if to_date_obj:
        inquiries = inquiries.filter(inquire_date__lte=to_date_obj)

    data = []
    for i, inquiry in enumerate(inquiries, start=1):
        data.append({
            'sl': i,
            'inquire_date': inquiry.inquire_date.strftime("%d-%m-%Y"),
            'full_name': inquiry.full_name,
            'email': inquiry.email,
            'phone': inquiry.phone_number,
            'inquire_id': inquiry.inquire_id,
        })

    return JsonResponse({'data': data})


@login_required    
def viewInquireModalManagerAPI(request):
    inquire_id = request.GET.get('inquire_id')
    inquiry = get_object_or_404(InquiresList, inquire_id=inquire_id)
    return render(request, 'inquire_list/inquire_viewers.html', {'inquiry': inquiry})
    
    

# ==================================submit inquire API from website ==================================
@csrf_exempt
def saveInquireManagerAPI(request):

    if request.method == "POST":

        try:

            data = json.loads(request.body)

            inquire_type = data.get("inquire_type", [])
            discover_type = data.get("discover_type", [])

            inquiry = InquiresList.objects.create(

                inquire_type = inquire_type,
                your_questions = data.get("your_questions"),
                your_planned = data.get("your_planned"),

                full_name = data.get("full_name"),
                email = data.get("email"),
                phone_number = data.get("phone_number"),

                discover_type = discover_type,
                comments = data.get("inquire_comments", ""),

                ss_creator = request.user if request.user.is_authenticated else None,
                ss_modifier = request.user if request.user.is_authenticated else None,
            )

            return JsonResponse({
                "status": "success",
                "message": "Inquiry Submitted Successfully"
            })

        except Exception as e:

            return JsonResponse({
                "status": "error",
                "message": str(e)
            })