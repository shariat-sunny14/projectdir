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
from packages.models import packages_dtls, packages_head_body, packages_items
from packages.models import packages_list
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from booking_us.models import EventSchedule, Slot_Details
from user_auth.models import org_info
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def scheduleListManagerAPI(request):

    context = {
        
    }
    return render(request, 'schedule/schedule_list.html', context)


@login_required()
def addScheduleModalManagerAPI(request):
    
    slot_details = Slot_Details.objects.filter(is_active=True).order_by('slot_id')

    context = {
        'slot_details': slot_details
    }
    return render(request, 'schedule/add_schedule.html', context)



@login_required
def getScheduleListManagerAPI(request):

    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")

    # যদি date খালি থাকে, খালি list return করবে
    if not from_date or not to_date:
        return JsonResponse({"data": []})

    schedules = EventSchedule.objects.filter(is_active=True)

    # Filter by date range (dd-mm-yyyy)
    try:
        start_date = datetime.strptime(from_date, "%d-%m-%Y").date()
        end_date = datetime.strptime(to_date, "%d-%m-%Y").date()
        schedules = schedules.filter(event_date__range=(start_date, end_date))
    except ValueError:
        return JsonResponse({"data": []})

    # ASCENDING ORDER
    schedules = schedules.order_by('event_date')

    data = []
    for index, schedule in enumerate(schedules, start=1):
        data.append({
            "sl": index,
            "event_date": schedule.event_date.strftime("%d-%m-%Y"),
            "name": schedule.slot_id.slot_name if schedule.slot_id else "No Slot",
            "status": schedule.status,
            "schedule_id": schedule.schedule_id
        })

    return JsonResponse({"data": data})



@login_required
@csrf_exempt
def addScheduleManagerAPI(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            slot_id = data.get("slot_id")
            from_date = data.get("from_date")
            to_date = data.get("to_date")

            # ✅ Validation
            if not slot_id or not from_date or not to_date:
                return JsonResponse({
                    "success": False,
                    "message": "All fields are required."
                })

            try:
                slot = Slot_Details.objects.get(pk=slot_id)
            except Slot_Details.DoesNotExist:
                return JsonResponse({
                    "success": False,
                    "message": "Selected slot does not exist."
                })

            # Convert date
            start_date = datetime.strptime(from_date, "%d-%m-%Y").date()
            end_date = datetime.strptime(to_date, "%d-%m-%Y").date()

            if start_date > end_date:
                return JsonResponse({
                    "success": False,
                    "message": "From Date cannot be after To Date."
                })

            created_count = 0
            duplicate_dates = []
            blocked_dates = []

            with transaction.atomic():

                for i in range((end_date - start_date).days + 1):
                    event_date = start_date + timedelta(days=i)

                    # 🔒 RULE:
                    # If trying to create FULL DAY slot
                    if slot.is_full_day:

                        # Check if any non-full-day slot already exists on that date
                        conflict_exists = EventSchedule.objects.filter(
                            event_date=event_date,
                            slot_id__is_full_day=False
                        ).exists()

                        if conflict_exists:
                            blocked_dates.append(event_date.strftime("%d-%m-%Y"))
                            continue

                    # Try create (unique_together handles duplicate)
                    try:
                        EventSchedule.objects.create(
                            slot_id=slot,
                            event_date=event_date,
                            ss_creator=request.user,
                            ss_modifier=request.user
                        )
                        created_count += 1

                    except IntegrityError:
                        duplicate_dates.append(event_date.strftime("%d-%m-%Y"))

            # ❌ যদি full day block হয়ে যায়
            if blocked_dates and created_count == 0:
                return JsonResponse({
                    "success": False,
                    "message": "Full Day slot cannot be created because partial slot exists on selected date(s)."
                })

            # ❌ সব duplicate
            if created_count == 0 and duplicate_dates:
                return JsonResponse({
                    "success": False,
                    "message": "Schedule already exists for selected date(s)."
                })

            # ✅ Partial success
            if blocked_dates or duplicate_dates:
                return JsonResponse({
                    "success": True,
                    "message": f"{created_count} schedule(s) added. "
                               f"{len(duplicate_dates)} duplicate skipped. "
                               f"{len(blocked_dates)} blocked (partial slot exists)."
                })

            # ✅ All success
            return JsonResponse({
                "success": True,
                "message": f"{created_count} schedule(s) added successfully."
            })

        except ValueError:
            return JsonResponse({
                "success": False,
                "message": "Invalid date format. Use dd-mm-yyyy."
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "message": str(e)
            })

    return JsonResponse({
        "success": False,
        "message": "Invalid request."
    })


@csrf_exempt
@login_required
def delete_schedule_listAPI(request):

    """
    API to delete a schedule.
    Only allows deletion if:
      1. Status is 'Free'
      2. Event date is in the future (after today)
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            schedule_id = data.get("schedule_id")

            # Fetch schedule
            schedule = EventSchedule.objects.get(schedule_id=schedule_id)

            # Check status
            if schedule.status != "Free":
                return JsonResponse({
                    "success": False,
                    "message": "Booked schedule cannot be deleted!"
                })

            # Check if event_date is today or in the past
            if schedule.event_date <= date.today():
                return JsonResponse({
                    "success": False,
                    "message": "Cannot delete schedules for today or past dates!"
                })

            # Passed all checks – safe to delete
            schedule.delete()
            return JsonResponse({
                "success": True,
                "message": "Schedule deleted successfully."
            })

        except EventSchedule.DoesNotExist:
            return JsonResponse({
                "success": False,
                "message": "Schedule not found!"
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "message": str(e)
            })

    # If not POST
    return JsonResponse({
        "success": False,
        "message": "Invalid request method!"
    })



# ==================================================================================
# website APIs
# ==================================================================================
def get_schedulesAPI(request):

    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    # ✅ If any date is missing / empty → return empty list
    if not from_date or not to_date:
        return JsonResponse({'schedules': []})

    try:
        # ✅ Convert string to date object (if needed)
        start_date = datetime.strptime(from_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(to_date, "%Y-%m-%d").date()
    except ValueError:
        # ✅ If invalid date format → return empty
        return JsonResponse({'schedules': []})

    schedules = EventSchedule.objects.filter(
        is_active=True,
        event_date__range=[start_date, end_date]
    ).order_by('event_date')[:10]

    data = []

    for item in schedules:
        data.append({
            'id': item.schedule_id,
            'date': item.event_date.strftime("%Y-%m-%d"),
            'title': item.slot_id.slot_name if item.slot_id else 'No Slot',
            'status': item.status,
        })

    return JsonResponse({'schedules': data})


def bookingFromPackageManagerAPI(request):
    org_data = org_info.objects.first()
    package_data = packages_list.objects.all().order_by('package_id')

    context = {
        'org_data': org_data,
        'package_data': package_data,
    }
    return render(request, 'websites/booking_from_package.html', context)