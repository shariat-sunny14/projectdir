import json
import sys
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.db import transaction
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.contrib.auth.decorators import login_required
from enroll_us.models import EnrollBookingDtls, EnrollDetails, EnrollList
import packages
from packages.models import packages_dtls, packages_head_body, packages_items
from packages.models import packages_list
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from photo_gallery.models import photos_gallery_dtls
from user_auth.models import org_info
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def enrollSetupListManagerAPI(request):
    enroll_data = EnrollList.objects.all()

    context = {
        'enroll_data': enroll_data,
    }
    return render(request, 'enroll_us/enroll_us_list.html', context)


@login_required()
def addNewEnrollModalManageAPI(request):
    

    context = {
        
    }
    return render(request, 'enroll_us/add_enroll_us.html', context)


@login_required()
@csrf_exempt
@transaction.atomic
def saveEnrollSetupManagerAPI(request):

    if request.method == "POST":

        try:
            enroll_id = request.POST.get('enroll_id')

            enroll_title = request.POST.get('enroll_title')
            enroll_price = request.POST.get('enroll_price')
            offer_price = request.POST.get('offer_price')
            enroll_caption = request.POST.get('enroll_caption')
            price_type = request.POST.get('price_type')

            # RADIO VALUE
            is_price = True if price_type == "price" else False
            is_offer = True if price_type == "offer" else False

            is_most_popular = True if request.POST.get('is_most_popular') else False

            # =========================
            # CREATE OR UPDATE PARENT
            # =========================
            if enroll_id:
                # UPDATE
                enroll = EnrollList.objects.get(enroll_id=enroll_id)

                enroll.enroll_title = enroll_title
                enroll.enroll_price = enroll_price
                enroll.offer_price = offer_price
                enroll.enroll_caption = enroll_caption
                enroll.is_enroll_price = is_price
                enroll.is_offer_price = is_offer
                enroll.is_most_popular = is_most_popular
                enroll.ss_modifier = request.user

                enroll.save()

                # OLD DETAILS DELETE (clean update)
                EnrollDetails.objects.filter(enroll_id=enroll).delete()

                msg = "Enroll updated successfully"

            else:
                # CREATE
                enroll = EnrollList.objects.create(
                    enroll_title=enroll_title,
                    enroll_price=enroll_price,
                    offer_price=offer_price,
                    enroll_caption=enroll_caption,
                    is_enroll_price=is_price,
                    is_offer_price=is_offer,
                    is_most_popular=is_most_popular,
                    ss_creator=request.user
                )

                msg = "Enroll created successfully"

            # =========================
            # DETAILS SAVE
            # =========================
            order_list = request.POST.getlist('enroll_order_no_list[]')
            details_list = request.POST.getlist('enroll_dtls_list[]')
            publish_list = request.POST.getlist('is_published[]')

            for i in range(len(order_list)):

                order_no = order_list[i]
                details = details_list[i]

                # checkbox match (important)
                is_published = True if str(i + 1) in publish_list else False

                EnrollDetails.objects.create(
                    enroll_id=enroll,
                    order_no=order_no,
                    enroll_dtls=details,
                    is_published=is_published,
                    ss_creator=request.user
                )

            return JsonResponse({
                "success": True,
                "msg": msg
            })

        except EnrollList.DoesNotExist:
            return JsonResponse({
                "success": False,
                "errmsg": "Enroll not found"
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "errmsg": str(e)
            })
            
            

@login_required()
def editEnrollUsModalManageAPI(request):
    
    enroll_id = request.GET.get('enroll_id')

    # Get main enroll data
    enroll = get_object_or_404(
        EnrollList,
        enroll_id=enroll_id
    )

    # Get enroll details
    enroll_details = EnrollDetails.objects.filter(
        enroll_id=enroll   # FK relation
    ).order_by('order_no')

    # Get elements/items (assuming this model exists)
    elements_data = packages_items.objects.filter(
        is_active=True
    ).order_by('pitem_id')

    context = {
        'enroll': enroll,
        'enroll_details': enroll_details,
        'elements_data': elements_data,
    }

    return render(
        request,
        'enroll_us/edit_enroll_us.html',
        context
    )
    


@login_required
@csrf_exempt
def deleteEnrollListManagerAPI(request):

    if request.method == "POST":

        enroll_id = request.POST.get("enroll_id")

        if not enroll_id:
            return JsonResponse({"success": False, "msg": "Enroll ID not provided."})

        try:
            deleted_count, _ = EnrollList.objects.filter(enroll_id=enroll_id).delete()

            if deleted_count:
                return JsonResponse({
                    "success": True,
                    "msg": "Enroll and its details deleted successfully."
                })
            else:
                return JsonResponse({
                    "success": False,
                    "msg": "Enroll not found."
                })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "msg": str(e)
            })

    return JsonResponse({
        "success": False,
        "msg": "Invalid request method."
    })
    

@csrf_exempt
def delete_EnrollDetails_edit_modeAPI(request):
    if request.method == "POST":
        enrolldtls_id = request.POST.get('enrolldtls_id')
        try:
            enrolldtls_obj = EnrollDetails.objects.get(enrolldtls_id=enrolldtls_id)
            enrolldtls_obj.delete()  # This deletes the DB record and the file
            return JsonResponse({'status': 'success', 'message': 'Enroll Details deleted successfully.'})
        except EnrollDetails.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Enroll Details not found.'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})
    
    

def showEnrollDetailsModalManageAPI(request, enroll_id):
    org_data = org_info.objects.filter(is_active=True).first()

    # FIX: Use EnrollList instead of packages_list
    enroll = get_object_or_404(EnrollList, enroll_id=enroll_id)

    # FIX: Use EnrollDetails instead of packages_dtls
    enroll_details = EnrollDetails.objects.filter(
        enroll_id=enroll,
    ).order_by('order_no')

    context = {
        'org_data': org_data,
        'enroll': enroll,
        'enroll_details': enroll_details,
    }

    return render(request, 'enroll_us/enroll_details.html', context)

# ======================================================================
# Enroll Booking APIs
# ======================================================================
def enroll_from_booking(request):
    org_data = org_info.objects.first()
    enroll_id = request.GET.get('enroll_id')
    enroll = None

    if enroll_id:
        enroll = get_object_or_404(EnrollList, enroll_id=enroll_id)

    return render(request, 'enroll_us/enroll_booking.html', {
        'org_data': org_data,
        'enroll': enroll
    })


@login_required
def save_enroll_booking(request):
    if request.method == "POST":
        enroll_id = request.POST.get('enroll_id')
        name = request.POST.get('full_name')
        mobile = request.POST.get('mobile_no')
        email = request.POST.get('email')
        address = request.POST.get('address')
        enroll_amount = request.POST.get('enroll_amount')

        enroll = get_object_or_404(EnrollList, enroll_id=enroll_id)

        # 🔥 current user
        user = request.user if request.user.is_authenticated else None

        # 🔥 session generate (simple logic)
        last = EnrollBookingDtls.objects.order_by('-ss_created_session').first()
        next_session = (last.ss_created_session + 1) if last and last.ss_created_session else 1678000900001

        EnrollBookingDtls.objects.create(
            enroll=enroll,
            full_name=name,
            mobile_no=mobile,
            email=email,
            address=address,
            course_amt=enroll_amount,
            is_paid=False,

            ss_creator=user,
            ss_created_session=next_session,
            ss_modifier=user
        )

        return JsonResponse({'status': 'success', 'message': 'Booking Saved!'})

    return JsonResponse({'status': 'error'})


@login_required
def enrollListViewFromWebsiteManagerAPI(request):
    
    org_data = org_info.objects.first()
    
    context= {
        'org_data': org_data,
    }
    
    return render(request, 'enroll_us/enroll_views_website.html', context)

@login_required
def get_enroll_booking_list(request):

    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    user = request.user

    # 🔥 CONDITION
    if user.is_admin:
        queryset = EnrollBookingDtls.objects.all()
    elif user.is_customer:
        queryset = EnrollBookingDtls.objects.filter(ss_creator=user)
    else:
        queryset = EnrollBookingDtls.objects.none()

    # 🔥 Date filter (optional)
    if from_date and to_date:
        from datetime import datetime
        from_date = datetime.strptime(from_date, "%d-%m-%Y")
        to_date = datetime.strptime(to_date, "%d-%m-%Y")

        queryset = queryset.filter(created_at__date__range=[from_date, to_date])

    queryset = queryset.select_related('enroll').order_by('-created_at')

    data = []
    for i, obj in enumerate(queryset, start=1):
        data.append({
            "sl": i,
            "order_id": obj.booking_id,
            "order_date": obj.created_at.strftime("%d-%m-%Y"),
            "full_name": obj.full_name,
            "email": obj.email or "",
            "phone": obj.mobile_no,
            "course_amt": obj.course_amt,
            "course_name": obj.enroll.enroll_title if obj.enroll else ""
        })

    return JsonResponse({"data": data})