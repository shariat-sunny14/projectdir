import json
import sys
from django.shortcuts import render, redirect
from django.db.models import Q
from django.db import transaction
from django.contrib import messages
from django.core.files.storage import default_storage
from django.contrib.auth.decorators import login_required
from advertisement_item.models import banner_list
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def advertisementItemAPI(request):

    banner_data = banner_list.objects.all()

    context = {
        'banner_data': banner_data,
    }
    return render(request, 'advertisement_item/advertisement_item.html', context)


@login_required()
def newAddAdvertItemModalAPI(request):

    context = {
        # 'org_list': org_list,
    }
    return render(request, 'advertisement_item/add_adv.html', context)


@login_required()
def editAdvertItemModalAPI(request):
    banner_data = {}
    if request.method == 'GET':
        data = request.GET
        banner_id = ''
        if 'banner_id' in data:
            banner_id = data['banner_id']
        if banner_id.isnumeric() and int(banner_id) > 0:
            banner_data = banner_list.objects.filter(banner_id=banner_id).first()

    context = {
        'banner_data': banner_data,
    }
    return render(request, 'advertisement_item/edit_adv.html', context)


@login_required()
def saveAdvertItemAPI(request):
    if request.method == 'POST':
        try:
            title_name = request.POST.get('title_name')
            is_publist = request.POST.get('is_publist') == 'on'  # Checkbox value
            banner_img = request.FILES.get('profile_img')  # File input

            # Create the object
            banner_obj = banner_list.objects.create(
                title_name=title_name,
                banner_img=banner_img,
                is_publist=is_publist,
                ss_creator=request.user,
                ss_modifier=request.user
            )

            return JsonResponse({
                'success': True,
                'msg': f'Banner {banner_obj.banner_id} created successfully.'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'errmsg': f"Error saving banner: {str(e)}"
            })

    return JsonResponse({
        'success': False,
        'errmsg': 'Invalid request method.'
    })



@login_required()
def editSaveAdvertItemAPI(request):
    if request.method == 'POST':
        try:
            banner_id = request.POST.get('banner_id')
            title_name = request.POST.get('title_name')
            is_publist = request.POST.get('is_publist') == 'on'
            banner_img = request.FILES.get('profile_img')  # may be None

            # ================= GET EXISTING BANNER =================
            banner_obj = None
            if banner_id and banner_id.isnumeric():
                banner_obj = banner_list.objects.filter(banner_id=banner_id).first()

            if not banner_obj:
                return JsonResponse({
                    'success': False,
                    'errmsg': 'Banner not found'
                })

            # ================= UPDATE FIELDS =================
            banner_obj.title_name = title_name
            banner_obj.is_publist = is_publist
            banner_obj.ss_modifier = request.user

            # ================= IMAGE LOGIC =================
            if banner_img:
                # delete old image ONLY if new image is provided
                if banner_obj.banner_img and default_storage.exists(banner_obj.banner_img.name):
                    default_storage.delete(banner_obj.banner_img.name)

                banner_obj.banner_img = banner_img
            # else: do nothing → keep old image

            banner_obj.save()

            return JsonResponse({
                'success': True,
                'msg': f'Banner {banner_obj.banner_id} updated successfully.'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'errmsg': f"Error updating banner: {str(e)}"
            })

    return JsonResponse({
        'success': False,
        'errmsg': 'Invalid request method.'
    })


@login_required
def deleteAdvertItemAPI(request):
    data = request.POST
    resp = {'status': ''}
    try:
        banner_id = data.get('banner_id')
        banners = banner_list.objects.filter(banner_id=banner_id)

        # Delete banner images from storage
        for banner in banners:
            if banner.banner_img:
                banner.banner_img.delete(save=False)  # Delete file from storage

        # Delete records from database
        banners.delete()

        return JsonResponse({'success': True, 'msg': 'Data Deleted.'})

    except Exception as e:
        resp['status'] = 'failed'
        resp['errmsg'] = str(e)

    return HttpResponse(json.dumps(resp), content_type="application/json")