import json
import sys
import pytz
import logging
from PIL import Image
from io import BytesIO
from django.db import transaction
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.shortcuts import render, redirect, HttpResponseRedirect, get_object_or_404
from datetime import date, datetime, timedelta
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib import messages
from collections import defaultdict
from decimal import Decimal
from django.utils.timezone import now
from django.contrib.sessions.models import Session
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django_ratelimit.decorators import ratelimit
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.db.models import Q, ExpressionWrapper, F, FloatField, Sum, Count
from photo_gallery.models import photos_gallery, photos_gallery_dtls
from user_auth.models import org_info
from django.http import HttpResponseNotFound
from django.contrib.auth import get_user_model
User = get_user_model()

# ======================================featured_gallery_dtls===================================
def featuredGalleryDtlsManagerAPI(request, phgallery_id):
    org_data = org_info.objects.first()

    # Selected gallery
    gallery = get_object_or_404(
        photos_gallery,
        phgallery_id=phgallery_id
    )

    # Thumbnail image (Hero Section)
    hero_image = photos_gallery_dtls.objects.filter(
        phgallery_id=gallery,
        is_thumbnail_photo=True
    ).first()

    # All gallery photos (grid)
    photos = photos_gallery_dtls.objects.filter(
        phgallery_id=gallery
    ).order_by('-is_cover_photo', '-ss_created_on')

    context = {
        'org_data': org_data,
        'gallery': gallery,
        'hero_image': hero_image,
        'photos': photos,
    }

    return render(
        request,
        'websites/featured_gallery_dtls.html',
        context
    )

@login_required()
def addNewPhotoGalleryListManagerAPI(request):

    return render(request, 'photo_gallery/new_photo_gallery/photo_gallery_list.html')


@login_required()
def addNewPhotoGalleryModalManageAPI(request):

    return render(request, 'photo_gallery/new_photo_gallery/add_new_photo_gallery.html')


@login_required()
def editNewPhotoGalleryModalManageAPI(request):

    phgallery_id = request.GET.get('phgallery_id')

    gallery = get_object_or_404(
        photos_gallery,
        phgallery_id=phgallery_id
    )

    gallery_dtls = photos_gallery_dtls.objects.filter(
        phgallery_id=gallery
    )

    context = {
        'gallery': gallery,
        'gallery_dtls': gallery_dtls
    }

    return render(
        request,
        'photo_gallery/new_photo_gallery/edit_new_photo_gallery.html',
        context
    )


@login_required()
def addNewPhotoGalleryDetailsManagerAPI(request):

    if request.method == "POST":

        gallery_id = request.POST.get("phgallery_id")

        gallery_name = request.POST.get("gallery_name")
        thumbnail_title = request.POST.get("thumbnail_title")
        descriptions = request.POST.get("descriptions")

        cover_index = request.POST.get("cover_photo_index")
        thumbnail_index = request.POST.get("thumbnail_photo_index")

        photo_files = request.FILES.getlist("photo_file_list")
        photo_titles = request.POST.getlist("photo_title_list")
        photo_descriptions = request.POST.getlist("photo_description_list")
        existing_ids = request.POST.getlist("existing_phgdtls_id_list")

        try:
            with transaction.atomic():

                # ============================
                # CREATE MODE
                # ============================
                if not gallery_id:

                    gallery = photos_gallery.objects.create(
                        gallery_name=gallery_name,
                        thumbnail_title=thumbnail_title,
                        descriptions=descriptions,
                        ss_creator=request.user
                    )

                # ============================
                # UPDATE MODE
                # ============================
                else:

                    gallery = get_object_or_404(
                        photos_gallery,
                        phgallery_id=gallery_id
                    )

                    gallery.gallery_name = gallery_name
                    gallery.thumbnail_title = thumbnail_title
                    gallery.descriptions = descriptions
                    gallery.ss_modifier = request.user
                    gallery.save()

                    # Delete removed rows
                    photos_gallery_dtls.objects.filter(
                        phgallery_id=gallery
                    ).exclude(
                        phgdtls_id__in=existing_ids
                    ).delete()

                # =======================================
                # 🔥 IMPORTANT FIX: RESET ALL FLAGS FIRST
                # =======================================
                photos_gallery_dtls.objects.filter(
                    phgallery_id=gallery
                ).update(
                    is_cover_photo=False,
                    is_thumbnail_photo=False
                )

                total_rows = len(photo_titles)
                file_counter = 0

                for i in range(total_rows):

                    is_cover = str(i) == str(cover_index)
                    is_thumbnail = str(i) == str(thumbnail_index)

                    # ===============================
                    # EXISTING UPDATE
                    # ===============================
                    if i < len(existing_ids):

                        dtls = photos_gallery_dtls.objects.get(
                            phgdtls_id=existing_ids[i]
                        )

                        dtls.photos_title = photo_titles[i]
                        dtls.photo_description = photo_descriptions[i]
                        dtls.is_cover_photo = is_cover
                        dtls.is_thumbnail_photo = is_thumbnail
                        dtls.ss_modifier = request.user
                        dtls.save()

                    # ===============================
                    # NEW INSERT
                    # ===============================
                    else:

                        if file_counter < len(photo_files):

                            photos_gallery_dtls.objects.create(
                                phgallery_id=gallery,
                                photos=photo_files[file_counter],
                                photos_title=photo_titles[i],
                                photo_description=photo_descriptions[i],
                                is_cover_photo=is_cover,
                                is_thumbnail_photo=is_thumbnail,
                                ss_creator=request.user
                            )

                            file_counter += 1

            return JsonResponse({
                "success": True,
                "msg": "Gallery Saved Successfully"
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "msg": str(e)
            })

    return JsonResponse({"success": False})


@login_required()
def get_photo_gallery_listAPI(request):

    gallery_list = photos_gallery.objects.all().order_by('-phgallery_id')

    data = []

    for g in gallery_list:
        data.append({
            "phgallery_id": g.phgallery_id,
            "gallery_name": g.gallery_name,
            "thumbnail_title": g.thumbnail_title,
            "descriptions": g.descriptions,
        })

    return JsonResponse({"data": data})



@csrf_exempt
def delete_dtls_photo_edit_modeAPI(request):
    if request.method == "POST":
        phgdtls_id = request.POST.get('phgdtls_id')
        try:
            photo_obj = photos_gallery_dtls.objects.get(phgdtls_id=phgdtls_id)
            photo_obj.delete()  # This deletes the DB record and the file
            return JsonResponse({'status': 'success', 'message': 'Photo deleted successfully.'})
        except photos_gallery_dtls.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Photo not found.'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})


@csrf_exempt
def delete_galleryAPI(request):
    if request.method == "POST":
        gallery_id = request.POST.get('gallery_id')
        try:
            gallery = photos_gallery.objects.get(phgallery_id=gallery_id)
            
            # Check if there are any related dtls
            related_photos = photos_gallery_dtls.objects.filter(phgallery_id=gallery)
            if related_photos.exists():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Cannot delete gallery. It has associated photos.'
                })
            
            # Safe to delete
            gallery.delete()
            return JsonResponse({'status': 'success', 'message': 'Gallery deleted successfully.'})
        
        except photos_gallery.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Gallery not found.'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})