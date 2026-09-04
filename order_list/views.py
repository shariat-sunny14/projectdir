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
from order_list.models import OrderList, OrderPackagePrice
from packages.models import packages_dtls, packages_head_body, packages_items
from packages.models import packages_list
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from booking_us.models import EventSchedule, Slot_Details
from user_auth.models import org_info
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required
def orderListViewManagerAPI(request):
    
    return render(request, 'order_list/order_list.html')


@login_required
def orderListViewFromWebsiteManagerAPI(request):
    
    org_data = org_info.objects.first()
    
    context= {
        'org_data': org_data,
    }
    
    return render(request, 'order_list/order_views_website.html', context)

@login_required
def getOrderListManagerAPI(request):

    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    queryset = OrderList.objects.all().prefetch_related('schedule_id', 'package_id')

    # Date filter
    if from_date and to_date:
        try:
            from_date = datetime.strptime(from_date, "%d-%m-%Y").date()
            to_date = datetime.strptime(to_date, "%d-%m-%Y").date()
            queryset = queryset.filter(order_date__range=[from_date, to_date])
        except:
            pass

    data = []
    sl = 1

    for order in queryset:

        # Schedule names
        schedule_names = ", ".join(
            [sch.slot_id.slot_name for sch in order.schedule_id.all() if sch.slot_id]
        )

        # Package names (FIXED)
        package_names = ", ".join(
            [pkg.package_title for pkg in order.package_id.all()]
        )

        data.append({
            "sl": sl,
            "order_date": order.order_date.strftime("%d-%m-%Y") if order.order_date else "",
            "full_name": order.full_name,
            "email": order.email,
            "phone": order.phone_number,
            "schedule_name": schedule_names,
            "package_name": package_names,
            "order_id": order.order_id
        })

        sl += 1

    return JsonResponse({
        "data": data
    })
    
    
@login_required
def getOrderListByUserIdManagerAPI(request):

    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    user = request.user

    queryset = OrderList.objects.all().select_related(
        'ss_creator'
    ).prefetch_related(
        'schedule_id',
        'package_id'
    ).order_by('-order_date')

    # =========================
    # User Filter
    # =========================
    if not user.is_admin:
        queryset = queryset.filter(ss_creator=user)

    # =========================
    # Date Filter
    # =========================
    if from_date and to_date:
        try:
            from_date = datetime.strptime(from_date, "%d-%m-%Y").date()
            to_date = datetime.strptime(to_date, "%d-%m-%Y").date()
            queryset = queryset.filter(order_date__range=(from_date, to_date))
        except ValueError:
            pass

    data = []
    sl = 1

    for order in queryset:

        # Schedule Names
        schedule_names = ", ".join(
            sch.slot_id.slot_name
            for sch in order.schedule_id.all()
            if sch.slot_id
        )

        # Package Names
        package_names = ", ".join(
            pkg.package_title
            for pkg in order.package_id.all()
        )

        data.append({
            "sl": sl,
            "order_date": order.order_date.strftime("%d-%m-%Y") if order.order_date else "",
            "full_name": order.full_name,
            "email": order.email,
            "phone": order.phone_number,
            "schedule_name": schedule_names,
            "package_name": package_names,
            "order_id": order.order_id
        })

        sl += 1

    return JsonResponse({"data": data})
    
    
@login_required    
def viewOrderModalManagerAPI(request):

    order_id = request.GET.get('order_id')

    order = get_object_or_404(
        OrderList.objects.prefetch_related('schedule_id', 'package_id'),
        order_id=order_id
    )

    # Get packages with price from through table
    order_packages = OrderPackagePrice.objects.filter(order_id=order).select_related('package_id')

    context = {
        'order': order,
        'schedules': order.schedule_id.all(),
        'order_packages': order_packages,  # Pass through model objects
    }

    return render(request, 'order_list/order_viewers.html', context)

# ==================================submit order API from website ==================================
@csrf_exempt
def orderSubmitManagerAPI(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            # 1️⃣ Create Order
            order = OrderList.objects.create(
                shoot_type=data.get("shoot_type", []),
                venue_name=data.get("venue_name", ""),
                guest_number=data.get("guest_number", ""),
                about_you=data.get("about_you", ""),
                full_name=data.get("full_name", ""),
                email=data.get("email", ""),
                phone_number=data.get("phone_number", ""),
                your_planned=data.get("your_planned", ""),
                is_other_photographer=data.get("is_other_photographer", False),
                discover_type=data.get("discover_type", []),
                comments=data.get("comments", ""),
                ss_creator=request.user if request.user.is_authenticated else None,
                ss_modifier=request.user if request.user.is_authenticated else None,
            )

            # 2️⃣ Set ManyToMany: Schedules
            schedule_ids = data.get("selected_schedule_ids", [])
            if schedule_ids:
                schedules = EventSchedule.objects.filter(schedule_id__in=schedule_ids)

                # Attach schedules to order
                order.schedule_id.set(schedules)

                # ✅ Update status of selected schedules to "Booked"
                schedules.update(status="Booked")

            # 3️⃣ Set ManyToMany: Packages
            package_ids = data.get("package_ids", [])
            total_price = Decimal("0.00")

            if package_ids:
                packages = packages_list.objects.filter(package_id__in=package_ids)

                for p in packages:
                    if p.is_offer_price and p.offer_price is not None:
                        price = p.offer_price
                    elif p.is_package_price and p.package_price is not None:
                        price = p.package_price
                    else:
                        price = Decimal("0.00")

                    # Add to total
                    total_price += price

                    # Create through model record (this sets the M2M relation too)
                    OrderPackagePrice.objects.create(
                        order_id=order,
                        package_id=p,
                        package_price=price
                    )

            # =====================
            # 4️⃣ Return response
            # =====================
            return JsonResponse({
                "status": "success",
                "message": "Order submitted successfully!",
                "order_id": order.order_id,
                "total_price": str(total_price)
            })

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})


