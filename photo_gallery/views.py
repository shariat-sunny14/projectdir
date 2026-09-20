import os
import random
from django.db import transaction
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from photo_gallery.models import photos_gallery, photos_gallery_dtls, PHOTOS_TYPE_CHOICES
from user_auth.models import org_info
from django.http import JsonResponse, Http404
from .utils import compress_image
from django.views.decorators.http import require_GET
from django.contrib.auth import get_user_model
User = get_user_model()

# ======================================featured_gallery_dtls===================================
def featuredGalleryDtlsManagerAPI(request, phgallery_id):
    org_data = org_info.objects.first()

    gallery = get_object_or_404(photos_gallery, phgallery_id=phgallery_id)

    hero_image = photos_gallery_dtls.objects.filter(
        phgallery_id=gallery,
        is_thumbnail_photo=True
    ).first()

    photos = photos_gallery_dtls.objects.filter(
        phgallery_id=gallery
    ).order_by('-is_cover_photo', '-ss_created_on')

    context = {
        'org_data': org_data,
        'gallery': gallery,
        'hero_image': hero_image,
        'photos': photos,
    }

    return render(request, 'websites/featured_gallery_dtls.html', context)


@login_required()
def addNewPhotoGalleryListManagerAPI(request):
    context = {
        'photo_type_choices': PHOTOS_TYPE_CHOICES,
    }
    return render(request, 'photo_gallery/new_photo_gallery/photo_gallery_list.html', context)


@login_required()
def addNewPhotoGalleryModalManageAPI(request):
    context = {
        'photo_type_choices': PHOTOS_TYPE_CHOICES,
    }
    return render(request, 'photo_gallery/new_photo_gallery/add_new_photo_gallery.html', context)


@login_required()
def editNewPhotoGalleryModalManageAPI(request):

    phgallery_id = request.GET.get('phgallery_id')

    gallery = get_object_or_404(photos_gallery, phgallery_id=phgallery_id)

    gallery_dtls = photos_gallery_dtls.objects.filter(phgallery_id=gallery)

    context = {
        'gallery': gallery,
        'gallery_dtls': gallery_dtls,
        'photo_type_choices': PHOTOS_TYPE_CHOICES,
    }

    return render(request, 'photo_gallery/new_photo_gallery/edit_new_photo_gallery.html', context)


@login_required()
def addNewPhotoGalleryDetailsManagerAPI(request):

    if request.method == "POST":

        gallery_id = request.POST.get("phgallery_id")

        photo_type = request.POST.get("photo_type")
        title = request.POST.get("title")
        description = request.POST.get("description", "")

        # Checkboxes: present + "on" when checked, absent when unchecked
        is_service = request.POST.get("is_service") == "on"
        is_recent_work = request.POST.get("is_recent_work") == "on"
        is_album = request.POST.get("is_album") == "on"

        cover_index = request.POST.get("cover_photo_index")
        thumbnail_index = request.POST.get("thumbnail_photo_index")

        photo_files = request.FILES.getlist("photo_file_list")
        photo_titles = request.POST.getlist("photo_title_list")
        photo_descriptions = request.POST.getlist("photo_description_list")
        existing_ids = request.POST.getlist("existing_phgdtls_id_list")

        if not photo_type or not title:
            return JsonResponse({
                "success": False,
                "msg": "Photo Type and Title are required."
            })

        try:
            with transaction.atomic():

                # ============================
                # CREATE MODE
                # ============================
                if not gallery_id:

                    gallery = photos_gallery.objects.create(
                        photo_type=photo_type,
                        title=title,
                        description=description,
                        is_service=is_service,
                        is_recent_work=is_recent_work,
                        is_album=is_album,
                        ss_creator=request.user
                    )

                # ============================
                # UPDATE MODE
                # ============================
                else:

                    gallery = get_object_or_404(photos_gallery, phgallery_id=gallery_id)

                    gallery.photo_type = photo_type
                    gallery.title = title
                    gallery.description = description
                    gallery.is_service = is_service
                    gallery.is_recent_work = is_recent_work
                    gallery.is_album = is_album
                    gallery.ss_modifier = request.user
                    gallery.save()

                    photos_gallery_dtls.objects.filter(
                        phgallery_id=gallery
                    ).exclude(
                        phgdtls_id__in=existing_ids
                    ).delete()

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

                    if i < len(existing_ids):

                        dtls = photos_gallery_dtls.objects.get(phgdtls_id=existing_ids[i])

                        dtls.photos_title = photo_titles[i]
                        dtls.photo_description = photo_descriptions[i]
                        dtls.is_cover_photo = is_cover
                        dtls.is_thumbnail_photo = is_thumbnail
                        dtls.ss_modifier = request.user
                        dtls.save()

                    else:

                        if file_counter < len(photo_files):

                            compressed_file = compress_image(photo_files[file_counter])

                            photos_gallery_dtls.objects.create(
                                phgallery_id=gallery,
                                photos=compressed_file,
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
    """
    GET /get_photo_gallery_list/
    Supports optional filters:
        ?photo_type=wedding
        ?is_service=true|false
        ?is_recent_work=true|false
        ?is_album=true|false
        ?title=<search text>
    """

    gallery_list = photos_gallery.objects.all().order_by('-phgallery_id')

    photo_type = request.GET.get('photo_type')
    is_service = request.GET.get('is_service')
    is_recent_work = request.GET.get('is_recent_work')
    is_album = request.GET.get('is_album')
    search_title = request.GET.get('title')

    if photo_type:
        gallery_list = gallery_list.filter(photo_type=photo_type)

    if is_service in ('true', 'false'):
        gallery_list = gallery_list.filter(is_service=(is_service == 'true'))

    if is_recent_work in ('true', 'false'):
        gallery_list = gallery_list.filter(is_recent_work=(is_recent_work == 'true'))

    if is_album in ('true', 'false'):
        gallery_list = gallery_list.filter(is_album=(is_album == 'true'))

    if search_title:
        gallery_list = gallery_list.filter(title__icontains=search_title)

    data = []

    for g in gallery_list:
        data.append({
            "phgallery_id": g.phgallery_id,
            "photo_type": g.get_photo_type_display(),
            "title": g.title,
            "description": g.description,
            "is_service": g.is_service,
            "is_recent_work": g.is_recent_work,
            "is_album": g.is_album,
        })

    return JsonResponse({"data": data})


@login_required()
@csrf_exempt
def delete_dtls_photo_edit_modeAPI(request):
    if request.method == "POST":
        phgdtls_id = request.POST.get('phgdtls_id')
        try:
            photo_obj = photos_gallery_dtls.objects.get(phgdtls_id=phgdtls_id)
            photo_obj.delete()
            return JsonResponse({'status': 'success', 'message': 'Photo deleted successfully.'})
        except photos_gallery_dtls.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Photo not found.'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})


@login_required()
@csrf_exempt
def delete_galleryAPI(request):
    if request.method == "POST":
        gallery_id = request.POST.get('gallery_id')
        try:
            gallery = photos_gallery.objects.get(phgallery_id=gallery_id)

            related_photos = photos_gallery_dtls.objects.filter(phgallery_id=gallery)
            if related_photos.exists():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Cannot delete gallery. It has associated photos.'
                })

            gallery.delete()
            return JsonResponse({'status': 'success', 'message': 'Gallery deleted successfully.'})

        except photos_gallery.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Gallery not found.'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})


# /////////////////////////////////////////////////////////////////////////
def _label_for(photo_type: str) -> str:
    return dict(photos_gallery._meta.get_field('photo_type').choices).get(photo_type, photo_type)


@require_GET
def photo_types_ajax(request):
    choices = [{'value': value, 'label': label} for value, label in PHOTOS_TYPE_CHOICES]
    return JsonResponse({'results': choices})


@require_GET
def recent_work_photo_types_ajax(request):
    """
    GET /api/recent-work-photo-types/
    Every distinct photo_type present among is_recent_work=True galleries
    — the full site-wide PHOTOS_TYPE_CHOICES list (photo_types_ajax above)
    would include categories with zero recent-work items, so #filterRow
    (Portfolio) uses this scoped list instead, same idea as
    services_photo_types_ajax for #servicesFilterRow.
    """
    types = (
        photos_gallery.objects
        .filter(is_recent_work=True)
        .exclude(photo_type='')
        .exclude(photo_type__isnull=True)
        .values_list('photo_type', flat=True)
        .distinct()
    )
    results = [{'value': t, 'label': _label_for(t)} for t in types]
    return JsonResponse({'results': results})


@require_GET
def gallery_list_ajax(request):
    thumbs = (
        photos_gallery_dtls.objects
        .filter(is_thumbnail_photo=True, photos__isnull=False, phgallery_id__is_recent_work=True,)
        .exclude(photos='')
        .select_related('phgallery_id')
        .order_by('-ss_created_on')
    )

    results = []
    seen_gallery_ids = set()

    for dtl in thumbs:
        gallery = dtl.phgallery_id
        if not gallery:
            continue
        if gallery.phgallery_id in seen_gallery_ids:
            continue
        seen_gallery_ids.add(gallery.phgallery_id)

        results.append({
            'phgallery_id': gallery.phgallery_id,
            'photo_type': gallery.photo_type,
            'photo_type_label': _label_for(gallery.photo_type),
            'title': gallery.title or dtl.photos_title or '',
            'thumbnail': dtl.photos.url,
        })

    return JsonResponse({'results': results})


@require_GET
def gallery_detail_ajax(request, phgallery_id):
    gallery = photos_gallery.objects.filter(phgallery_id=phgallery_id).first()
    if not gallery:
        raise Http404('Gallery not found')

    dtls = (
        photos_gallery_dtls.objects
        .filter(phgallery_id__phgallery_id=phgallery_id, photos__isnull=False)
        .exclude(photos='')
        .order_by('-is_cover_photo', 'phgdtls_id')
    )

    photos = [{
        'phgdtls_id': d.phgdtls_id,
        'title': d.photos_title or gallery.title or '',
        'description': d.photo_description or '',
        'src': d.photos.url,
    } for d in dtls]

    return JsonResponse({
        'phgallery_id': gallery.phgallery_id,
        'title': gallery.title or '',
        'photo_type': gallery.photo_type,
        'photo_type_label': _label_for(gallery.photo_type),
        'photos': photos,
    })
    
    
# ======================================================
#
# ======================================================
@require_GET
def services_photo_types_ajax(request):
    """
    GET /api/services-photo-types/
    Every distinct photo_type present among is_service=True galleries —
    ALL of them, regardless of how many services-gallery-ajax itself
    returns for the default (random-3) view. This is what populates the
    #servicesFilterRow buttons, so a category button never depends on
    whether that category happened to land in the random sample.
    """
    types = (
        photos_gallery.objects
        .filter(is_service=True)
        .exclude(photo_type='')
        .exclude(photo_type__isnull=True)
        .values_list('photo_type', flat=True)
        .distinct()
    )
    results = [{'value': t, 'label': _label_for(t)} for t in types]
    return JsonResponse({'results': results})


@require_GET
def services_gallery_ajax(request):
    """
    GET /api/services-gallery/
    No ?photo_type= -> the default homepage view: a random sample of 3.
    ?photo_type=<value> -> every is_service=True gallery in that one
    category (not sliced) — used when a #servicesFilterRow button is
    clicked, so filtering shows the category's full set, not just
    whichever of it happened to be in the random 3.
    """
    photo_type = request.GET.get('photo_type')

    galleries = photos_gallery.objects.filter(is_service=True)

    if photo_type:
        galleries = galleries.filter(photo_type=photo_type)
    else:
        galleries = galleries.order_by('?')[:3]

    results = []

    for gallery in galleries:
        photo = (
            photos_gallery_dtls.objects
            .filter(phgallery_id=gallery, is_cover_photo=True, photos__isnull=False)
            .exclude(photos='')
            .first()
            or
            photos_gallery_dtls.objects
            .filter(phgallery_id=gallery, is_thumbnail_photo=True, photos__isnull=False)
            .exclude(photos='')
            .first()
            or
            photos_gallery_dtls.objects
            .filter(phgallery_id=gallery, photos__isnull=False)
            .exclude(photos='')
            .first()
        )

        if not photo:
            continue

        results.append({
            'phgallery_id': gallery.phgallery_id,
            'title': gallery.title or '',
            'photo_type': gallery.photo_type,
            'photo_type_label': _label_for(gallery.photo_type),
            'image': photo.photos.url,
        })

    return JsonResponse({'results': results})



def _dtls_photo_url(dtls):
    try:
        return dtls.photos.url if dtls and dtls.photos else ''
    except (ValueError, AttributeError):
        return ''


@require_GET
def albums_list(request):
    galleries = list(
        photos_gallery.objects
        .filter(is_album=True)
        .prefetch_related('phgallery2phgdtls')
        .order_by('-ss_created_on')
    )

    # maximum 10 ta data, randomly
    if len(galleries) > 10:
        galleries = random.sample(galleries, 10)

    results = []
    for gallery in galleries:
        dtls_qs = gallery.phgallery2phgdtls.all()
        cover_dtls = (
            dtls_qs.filter(is_thumbnail_photo=True).first()
            or dtls_qs.filter(is_cover_photo=True).first()
            or dtls_qs.first()
        )
        results.append({
            'phgallery_id': gallery.phgallery_id,
            'title': gallery.title or '',
            'photo_type': gallery.photo_type,
            'photo_type_label': gallery.get_photo_type_display(),
            'cover': _dtls_photo_url(cover_dtls),
        })

    return JsonResponse({'results': results})


# ✅ NOTUN — album-er shob image (lightbox-er jonno)
@require_GET
def albums_detail(request, phgallery_id):
    gallery = get_object_or_404(photos_gallery, phgallery_id=phgallery_id, is_album=True)

    dtls_qs = (
        gallery.phgallery2phgdtls
        .exclude(photos='')
        .exclude(photos__isnull=True)
        .order_by('phgdtls_id')
    )

    photos = [
        {
            'phgdtls_id': d.phgdtls_id,
            'title': d.photos_title or gallery.title or '',
            'src': _dtls_photo_url(d),
        }
        for d in dtls_qs
    ]

    return JsonResponse({
        'phgallery_id': gallery.phgallery_id,
        'title': gallery.title or '',
        'photo_type_label': gallery.get_photo_type_display(),
        'photos': photos,
    })


@require_GET
def photogallery_list(request):
    dtls_qs = (
        photos_gallery_dtls.objects
        .exclude(photos='')
        .exclude(photos__isnull=True)
        .order_by('-ss_created_on')[:20]
    )

    results = [
        {
            'phgdtls_id': dtls.phgdtls_id,
            'title': dtls.photos_title or '',
            'description': dtls.photo_description or '',
            'src': _dtls_photo_url(dtls),
        }
        for dtls in dtls_qs
    ]

    return JsonResponse({'results': results})