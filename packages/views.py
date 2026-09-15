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
from packages.models import packages_dtls, packages_head_body, packages_items
from packages.models import packages_list
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from photo_gallery.models import photos_gallery_dtls
from user_auth.models import org_info
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def packagesHeadBodyManagerAPI(request):

    packages_data = packages_head_body.objects.all()

    context = {
        'packages_data': packages_data,
    }
    return render(request, 'packages/packages_head_body.html', context)


def showPackageDetailsModalManageAPI(request, package_id):
    org_data = org_info.objects.filter(is_active=True).first()
    package = get_object_or_404(packages_list, package_id=package_id)

    package_details = packages_dtls.objects.filter(
        package_id=package
    ).select_related('pitem_id').order_by('pitem_id__pitem_id', 'order_no')

    grouped_data = {}
    for item in package_details:
        header = item.pitem_id.pitem_name if item.pitem_id else "Others"

        if header not in grouped_data:
            grouped_data[header] = []

        grouped_data[header].append(item)

    context = {
        'org_data': org_data,
        'package': package,
        'grouped_data': grouped_data,
    }

    return render(request, 'packages/package_details.html', context)


@login_required()
def addNewPackageModalManageAPI(request):
    
    elements_data = packages_items.objects.filter(is_active=True).order_by('pitem_id').all()

    context = {
        'elements_data': elements_data,
    }
    return render(request, 'packages/add_packages.html', context)


@login_required()
def editPackageModalManageAPI(request):
    
    package_id = request.GET.get('package_id')

    packages = get_object_or_404(
        packages_list,
        package_id=package_id
    )

    packagesdtls = packages_dtls.objects.filter(
        package_id=packages
    ).order_by('order_no')

    elements_data = packages_items.objects.filter(
        is_active=True
    ).order_by('pitem_id')

    context = {
        'packages': packages,
        'packagesdtls': packagesdtls,
        'elements_data': elements_data,
    }

    return render(
        request,
        'packages/edit_packages.html',
        context
    )


@login_required
@csrf_exempt
def saveUpdatePackagesHeadBodyManager(request):
    if request.method == "POST":
        try:
            head_name = request.POST.get("head_name")
            body_text = request.POST.get("body_text")

            if not head_name or not body_text:
                return JsonResponse({
                    "success": False,
                    "errmsg": "Title and Body Text are required."
                })

            with transaction.atomic():
                # 🔥 1. DELETE ALL OLD DATA FIRST
                packages_head_body.objects.all().delete()

                # 🔥 2. CREATE NEW DATA
                obj = packages_head_body.objects.create(
                    head_name=head_name,
                    body_text=body_text,
                    ss_creator=request.user,
                    ss_modifier=request.user
                )

            return JsonResponse({
                "success": True,
                "msg": "Package data saved successfully."
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "errmsg": str(e)
            })

    return JsonResponse({
        "success": False,
        "errmsg": "Invalid request method"
    })
    

# ===============================================================
# packages/title name, body image manager APIs
# ===============================================================
@login_required()
def packagesSetupManagerAPI(request):
    package_data = packages_list.objects.all()

    context = {
        'package_data': package_data,
    }
    return render(request, 'packages/packages_setup.html', context)


@login_required()
@csrf_exempt
def addPackageSetupmanagerAPI(request):
    if request.method == "POST":
        try:
            with transaction.atomic():

                package_id = request.POST.get("package_id")  # hidden field from form

                # =========================
                # Boolean Radio Handling
                # =========================
                is_package_price = True if request.POST.get("is_package_price") == "on" else False
                is_offer_price = True if request.POST.get("is_offer_price") == "on" else False

                # =========================
                # Price Handling (Always Save If Provided)
                # =========================
                package_price = request.POST.get("package_price")
                offer_price = request.POST.get("offer_price")

                package_price = Decimal(package_price) if package_price else None
                offer_price = Decimal(offer_price) if offer_price else None

                # =========================
                # Create or Update Package
                # =========================
                if package_id:  # Update existing
                    package_obj = packages_list.objects.get(pk=package_id)
                    package_obj.package_title = request.POST.get("package_title")
                    package_obj.package_price = package_price
                    package_obj.offer_price = offer_price
                    package_obj.is_package_price = is_package_price
                    package_obj.is_offer_price = is_offer_price
                    package_obj.title_caption = request.POST.get("title_caption")
                    package_obj.ss_modifier = request.user if request.user.is_authenticated else None

                    # Handle title image
                    new_image = request.FILES.get("profile_img")
                    if new_image:
                        if package_obj.title_img:  # delete old image
                            package_obj.title_img.delete(save=False)
                        package_obj.title_img = new_image
                    # else: keep existing image

                    package_obj.save()

                    # Delete existing package details
                    packages_dtls.objects.filter(package_id=package_obj).delete()

                else:  # Create new package
                    package_obj = packages_list.objects.create(
                        package_title=request.POST.get("package_title"),
                        package_price=package_price,
                        offer_price=offer_price,
                        is_package_price=is_package_price,
                        is_offer_price=is_offer_price,
                        title_caption=request.POST.get("title_caption"),
                        title_img=request.FILES.get("profile_img"),
                        ss_creator=request.user if request.user.is_authenticated else None,
                        ss_modifier=request.user if request.user.is_authenticated else None,
                    )

                # =========================
                # Save Package Details
                # =========================
                element_list = request.POST.getlist("package_elements_list[]")
                order_list = request.POST.getlist("package_order_no_list[]")
                description_list = request.POST.getlist("elements_drescription_list[]")

                for element_id, order, description in zip(element_list, order_list, description_list):
                    packages_dtls.objects.create(
                        package_id=package_obj,
                        pitem_id=packages_items.objects.get(pk=element_id),
                        order_no=int(order) if order else None,
                        elements_drescription=description,
                        ss_creator=request.user if request.user.is_authenticated else None,
                        ss_modifier=request.user if request.user.is_authenticated else None,
                    )

            return JsonResponse({
                "success": True,
                "msg": "Package saved successfully!"
            })

        except packages_list.DoesNotExist:
            return JsonResponse({
                "success": False,
                "errmsg": "Package not found for update."
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "errmsg": str(e)
            })

    return JsonResponse({
        "success": False,
        "errmsg": "Invalid request"
    })


@login_required
def deletePackageListManagerAPI(request):
    if request.method == "POST":
        package_id = request.POST.get("package_id")

        if not package_id:
            return JsonResponse({"success": False, "msg": "Package ID not provided."})

        try:
            # Check if any package details exist
            details_exist = packages_dtls.objects.filter(package_id=package_id).exists()

            if details_exist:
                return JsonResponse({
                    "success": False,
                    "msg": "Cannot delete! Package has details in 'packages_dtls'."
                })

            # No details exist → safe to delete
            deleted_count, _ = packages_list.objects.filter(package_id=package_id).delete()

            if deleted_count:
                return JsonResponse({
                    "success": True,
                    "msg": "Package successfully deleted."
                })
            else:
                return JsonResponse({
                    "success": False,
                    "msg": "Package not found or already deleted."
                })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "msg": f"Error occurred: {str(e)}"
            })

    return JsonResponse({
        "success": False,
        "msg": "Invalid request method."
    })



@csrf_exempt
def delete_packages_dtls_edit_modeAPI(request):
    if request.method == "POST":
        packagedtls_id = request.POST.get('packagedtls_id')
        try:
            packagedlt_obj = packages_dtls.objects.get(packagedtls_id=packagedtls_id)
            packagedlt_obj.delete()  # This deletes the DB record and the file
            return JsonResponse({'status': 'success', 'message': 'Package detail deleted successfully.'})
        except packages_dtls.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Package detail not found.'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})



# ================================================================================
# packages details
# ================================================================================
def packagesDetailsManagerAPI(request):


    context = {
    }
    return render(request, 'websites/packages_details.html', context)