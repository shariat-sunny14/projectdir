import os
import json
import sys
import pytz
import logging
import yagmail
from PIL import Image
from io import BytesIO
from django.db import transaction
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.shortcuts import render, redirect, HttpResponseRedirect
from datetime import date, datetime, timedelta
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.forms import UserCreationForm
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password
from about_us.models import AboutUs, Award, Certificate, LifeAtOur, TeamMember
from enroll_us.models import EnrollDetails, EnrollList
from facebook_feed.models import FacebookPost
from photo_gallery.models import photos_gallery, photos_gallery_dtls
from user_auth.forms import UserLoginForm
from django.contrib import messages
from collections import defaultdict
from decimal import Decimal
from django.utils.timezone import now
from django.contrib.sessions.models import Session
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django_ratelimit.decorators import ratelimit
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.db.models import Q, ExpressionWrapper, F, FloatField, Sum, Count, Prefetch
from user_setup.models import access_list
from django.http import HttpResponseNotFound
from user_auth.decorators import login_required_with_timeout
from advertisement_item.models import banner_list
from packages.models import packages_head_body
from packages.models import packages_list
from user_auth.models import SystemShutdown, org_info, PasswordResetOTP
from login_theme.models import login_themes
from why_us.models import FAQ
from youtube_gallery.models import YouTubeVideo
from django.contrib.auth import get_user_model
User = get_user_model()


def websitesManagerAPI(request):
    banner_data = banner_list.objects.filter(is_publist=True)
    package_hdbd = packages_head_body.objects.all()
    package_data = packages_list.objects.all().order_by('package_id')
    org_data = org_info.objects.first()
    posts = FacebookPost.objects.all().order_by('-created_time')
    yt_videos = YouTubeVideo.objects.all().order_by('-created_at')
    faqs = FAQ.objects.filter(is_active=True).order_by('is_serial')
    about = AboutUs.objects.last()
    team_members = TeamMember.objects.all().order_by('id')
    my_awards = Award.objects.all().order_by('id')
    my_certificates = Certificate.objects.all().order_by('id')
    Life_at = LifeAtOur.objects.last()
    galleries = photos_gallery.objects.all()
    
    # EnrollDetails filtered & ordered queryset
    details_qs = EnrollDetails.objects.filter(is_published=True).order_by('order_no')

    # EnrollList queryset with prefetch
    enroll_data = EnrollList.objects.prefetch_related(
        Prefetch('enroll2enrolldtls', queryset=details_qs, to_attr='published_details')
    ).order_by('enroll_id')

    gallery_data = []

    for gallery in galleries:

        # Cover Photo (is_cover_photo=True)
        cover_photo = photos_gallery_dtls.objects.filter(
            phgallery_id=gallery,
            is_cover_photo=True
        ).first()

        # Random 7 non-cover photos
        other_photos = photos_gallery_dtls.objects.filter(
            phgallery_id=gallery
        ).exclude(is_cover_photo=True).order_by('?')[:7]

        gallery_data.append({
            'gallery': gallery,
            'cover_photo': cover_photo,
            'other_photos': other_photos
        })

    context = {
        'banner_data': banner_data,
        'package_hdbd': package_hdbd,
        'package_data': package_data,
        'org_data': org_data,
        'gallery_data': gallery_data,
        'posts': posts,
        'yt_videos': yt_videos,
        'faqs': faqs,
        'about': about,
        'team_members': team_members,
        'my_awards': my_awards,
        'my_certificates': my_certificates,
        'Life_at': Life_at,
        'enroll_data': enroll_data,
    }

    return render(request, 'websites/websites.html', context)

def ratelimited_view(request, exception):
    return JsonResponse({'success': False, 'errmsg': 'Too many requests. Please try again later.'}, status=429)

# login page render
def user_loginManagerAPI(request):

    # Retrieve the latest login theme, or use a default if none exists
    logintheme = login_themes.objects.all()
    
    if logintheme.exists():
        latest_theme = logintheme.latest('login_theme_id')
        login_template = f'logger/{latest_theme.login_theme_name}.html' if latest_theme.login_theme_name else 'logger/login_theme1.html'
    else:
        login_template = 'logger/login_theme1.html'

    # Set the timezone to Dhaka
    dhaka_tz = pytz.timezone('Asia/Dhaka')
    present_time = timezone.now().astimezone(dhaka_tz).date()  # Convert to date for sys_validity check

    # Retrieve the latest SystemShutdown record for sys_validity check
    sys_expiry = SystemShutdown.objects.order_by('-sys_id').first()
    
    # Check if sys_validity is set and has not expired
    if sys_expiry and sys_expiry.sys_validity and present_time > sys_expiry.sys_validity:
        return render(request, 'sys_shut_down/sys_shut_down.html')

    # Retrieve the first active system shutdown record for is_sys_shut_down=True
    shutdown_data = SystemShutdown.objects.filter(is_sys_shut_down=True).order_by('-sys_id').first()

    # If there is an active shutdown, check if the down-time validity has passed
    if shutdown_data:
        present_time_datetime = timezone.now().astimezone(dhaka_tz)  # Get the current datetime for comparison
        if present_time_datetime > shutdown_data.sys_down_time_validity:
            return render(request, login_template)
        else:
            return render(request, 'sys_shut_down/sys_shut_down.html')

    # Default to the login page if no active shutdown or valid condition is met
    return render(request, login_template)


logger = logging.getLogger(__name__)
@csrf_protect
@ratelimit(key='user', rate='100/m', method='POST', block=True)
def user_loginAPI(request):
    resp = {'success': False, 'errmsg': 'Invalid Username and Password. Please Try Again.'}
    present_date = datetime.now().date()
    
    if request.method == 'POST':
        logout(request)
        username = request.POST.get('username')
        password = request.POST.get('password')
    
        
        # Fetch user based on the username (case-insensitive)
        try:
            user = User.objects.get(username__iexact=username)
        except User.DoesNotExist:
            user = None
        
        # Authenticate user with the provided password
        if user is not None and user.check_password(password):
                
            user.is_login_status = True
            user.save()
                
            login(request, user)
            logger.info(f"User {user.username} logged in success.")
            return JsonResponse({'success': True, 'msg': 'Login Successful.'})
                
        else:
            logger.warning(f"Invalid login attempt for username: {username}")
            return JsonResponse({'success': False, 'errmsg': 'Invalid Username and Password. Please Try Again.'})
    
    return JsonResponse(resp)


@login_required_with_timeout
def main_dashboard(request):
    active_access_list_data = []

    if request.user.is_authenticated:
        access_list_data = access_list.objects.filter(
            user_id=request.user,
            feature_id__is_active=True,
            feature_id__module_id__is_active=True,
            feature_id__module_id__module_id2feature_list__is_active=True,
            feature_id__type_id__is_active=True,  # Check is_active on the related module_type
            feature_id__feature_type="Form",
        ).select_related(
            'feature_id__type_id',  # Select the related module_type
            'feature_id__module_id',  # Select the related module_list
        )

        active_access_list_data = access_list_data.filter(
            feature_id__is_active=True,
            feature_id__module_id__is_active=True,
            feature_id__module_id__module_id2feature_list__is_active=True,
            feature_id__type_id__is_active=True,  # Apply the same is_active filter here
        ).distinct()

    context = {
        'active_access_list_data': active_access_list_data,
    }

    return render(request, 'main_dashboard/main_dashboard.html', context)


@login_required()
def logoutuser(request):
    # Fetch the current user
    current_user = request.user

    # Update the user's login status to False upon logout
    if current_user.is_authenticated:
        current_user.is_login_status = False
        current_user.save()

    logout(request)
    messages.success(request, 'Logout success!')
    return redirect('websites')

@login_required
def logout_all_users(request):
    current_user = request.user

    # Update the user's login status to False upon logout
    if current_user.is_authenticated:
        current_user.is_login_status = False
        current_user.save()

    # Store the current user's session key to avoid deleting it prematurely
    current_session_key = request.session.session_key

    # Fetch all active sessions except the current user's
    sessions = Session.objects.filter(expire_date__gte=timezone.now()).exclude(session_key=current_session_key)

    # Log out all other users by updating their is_login_status and deleting their sessions
    for session in sessions:
        data = session.get_decoded()
        user_id = data.get('_auth_user_id')

        if user_id:
            try:
                # Use 'user_id' instead of 'id'
                user = User.objects.get(user_id=user_id)  # Reference user_id directly
                user.is_login_status = False  # Update login status
                user.save()
            except User.DoesNotExist:
                continue

    # Delete all other sessions
    sessions.delete()
    
    # Create or update the SystemShutdown record
    dhaka_tz = pytz.timezone('Asia/Dhaka')

    # Get the current time in Dhaka timezone
    current_time_dhaka = timezone.now().astimezone(dhaka_tz)

    # Create or update the record
    system_shutdown, created = SystemShutdown.objects.get_or_create(
        sys_id=334455560000,  # Use a predefined ID for the unique record
        defaults={
            'sys_down_time_validity': current_time_dhaka + timezone.timedelta(hours=6),  # Set to 6 hours later
            'is_sys_shut_down': True,
            'ss_creator': current_user
        }
    )

    # If the record already exists, update it
    if not created:
        system_shutdown.sys_down_time_validity = current_time_dhaka + timezone.timedelta(hours=6)  # Update to 6 hours later
        system_shutdown.is_sys_shut_down = True
        system_shutdown.ss_modifier = current_user
        system_shutdown.save()

    # Log out the current user properly
    logout(request)

    # Success message and redirect
    messages.success(request, 'All users, including yourself, have been logged out successfully!')
    return redirect('websites')


# ======================================ORG Info===================================
@login_required
def orgInfoManagerAPI(request):

    return render(request, 'org_info/org_information.html')


@login_required()
def organization_getAPI(request):
    try:
        org_data = org_info.objects.first()   # যদি একটাই org থাকে

        if not org_data:
            return JsonResponse({'success': False, 'errmsg': 'No Organization Found'})

        data = {
            'org_id': org_data.org_id,
            'org_no': org_data.org_no,
            'org_name': org_data.org_name,
            'email': org_data.email,
            'fax': org_data.fax,
            'website': org_data.website,
            'hotline': org_data.hotline,
            'fb_link': org_data.fb_link,
            'twitter_link': org_data.twitter_link,
            'linkedin_link': org_data.linkedin_link,
            'instagram_link': org_data.instagram_link,
            'phone': org_data.phone,
            'address': org_data.address,
            'description': org_data.description,
            'is_active': org_data.is_active,
            'org_logo': org_data.org_logo.url if org_data.org_logo else '',
        }

        return JsonResponse({'success': True, 'data': data})

    except Exception as e:
        return JsonResponse({'success': False, 'errmsg': str(e)})

@login_required()
def organization_addupdateAPI(request):
    resp = {'success': False, 'errmsg': 'Failed'}

    if request.method != "POST":
        resp['errmsg'] = "Invalid request method"
        return JsonResponse(resp)

    try:
        with transaction.atomic():

            data = request.POST
            new_logo_uploaded = 'org_logo' in request.FILES

            # =========================
            # GET OLD ORG
            # =========================
            old_org = org_info.objects.first()
            old_logo_name = None

            if old_org and old_org.org_logo:
                old_logo_name = old_org.org_logo.name

            # =========================
            # DELETE OLD DATA
            # =========================
            org_info.objects.all().delete()

            # =========================
            # CREATE NEW OBJECT
            # =========================
            org_data = org_info()

            org_data.org_no = data.get('org_no')
            org_data.org_name = data.get('org_name')
            org_data.email = data.get('email')
            org_data.fax = data.get('fax')
            org_data.website = data.get('website')
            org_data.hotline = data.get('hotline')
            org_data.phone = data.get('phone')
            org_data.address = data.get('address')
            org_data.description = data.get('description')

            org_data.fb_link = data.get('fb_link')
            org_data.twitter_link = data.get('twitter_link')
            org_data.linkedin_link = data.get('linkedin_link')
            org_data.instagram_link = data.get('instagram_link')

            org_data.is_active = True if data.get(
                'is_active') in ['1', 'true', 'True', 'on'] else False

            org_data.ss_creator = request.user
            org_data.ss_modifier = request.user

            # =========================
            # IMAGE / FILE PROCESS
            # =========================
            if new_logo_uploaded:

                logo_file = request.FILES['org_logo']
                file_ext = os.path.splitext(logo_file.name)[1].lower()

                # delete old logo
                if old_logo_name and default_storage.exists(old_logo_name):
                    default_storage.delete(old_logo_name)

                # ======================
                # GIF → SAVE ORIGINAL
                # ======================
                if file_ext == '.gif':
                    filename = default_storage.save(
                        f'org_logos/{logo_file.name}',
                        logo_file
                    )

                # ======================
                # IMAGE FILE → RESIZE
                # ======================
                elif file_ext in ['.jpg', '.jpeg', '.png', '.webp']:

                    image = Image.open(logo_file)

                    if image.mode in ('RGBA', 'LA'):
                        image = image.convert('RGB')

                    image.thumbnail((500, 500))

                    output = BytesIO()

                    image_format = image.format if image.format else 'JPEG'

                    image.save(output, format=image_format, quality=90)
                    output.seek(0)

                    filename = default_storage.save(
                        f'org_logos/{logo_file.name}',
                        ContentFile(output.read())
                    )

                # ======================
                # OTHER FILE TYPES
                # ======================
                else:
                    filename = default_storage.save(
                        f'org_logos/{logo_file.name}',
                        logo_file
                    )

                org_data.org_logo = filename

            else:
                # keep old logo
                if old_logo_name:
                    org_data.org_logo = old_logo_name

            # =========================
            # SAVE DATA
            # =========================
            org_data.save()

            resp['success'] = True
            resp['msg'] = "Organization Saved Successfully"

    except Exception as e:
        logger.error(str(e))
        resp['errmsg'] = str(e)

    return JsonResponse(resp)


# ======================================testing===================================
def testLogin(request):

    return render(request, 'logger/test.html')



# =========================================================================
# password reset
# =========================================================================
def send_reset_otp(request):
    data = json.loads(request.body)
    email = data.get('email')
    
    try:
        user = User.objects.get(email=email)
        otp = PasswordResetOTP.generate_otp()
        PasswordResetOTP.objects.create(user=user, otp_code=otp)

        yag = yagmail.SMTP('tbox.info.bd@gmail.com', 'hnnasmhrgqxeygur')
        yag.send(
            to=email,
            subject='Password Reset Verification Code',
            contents = f"Arif Raaj Photography 📸 | Secure verification message. Your verification code is {otp}. Please do not share this code with anyone."
        )

        return JsonResponse({'status':'success'})

    except User.DoesNotExist:
        return JsonResponse({'status':'error','message':'Email not found'})
    

def verify_reset_otp(request):

    data = json.loads(request.body)
    email = data.get('email')
    otp = data.get('otp')

    try:

        user = User.objects.get(email=email)

        otp_obj = PasswordResetOTP.objects.filter(
            user=user,
            otp_code=otp
        ).last()

        if otp_obj:
            return JsonResponse({'status':'success'})
        else:
            return JsonResponse({'status':'error','message':'Invalid OTP'})

    except:
        return JsonResponse({'status':'error'})
    

def change_password(request):

    data = json.loads(request.body)

    email = data.get('email')
    password = data.get('password')

    try:

        user = User.objects.get(email=email)
        user.password = make_password(password)
        user.save()

        return JsonResponse({'status':'success'})

    except:
        return JsonResponse({'status':'error'})
    
    
# =========================================================================
# registration API
# =========================================================================    
@csrf_exempt  # Because we're using AJAX POST (or you can use CSRF token in JS)
def register_user_managerAPI(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        phone_no = request.POST.get('phone')
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Basic validation
        if User.objects.filter(username=username).exists():
            return JsonResponse({'status': 'error', 'message': 'Username already exists'})
        if User.objects.filter(email=email).exists():
            return JsonResponse({'status': 'error', 'message': 'Email already exists'})
        if User.objects.filter(phone_no=phone_no).exists():
            return JsonResponse({'status': 'error', 'message': 'Phone number already exists'})

        # Save user
        user = User(
            first_name=first_name,
            last_name=last_name,
            username=username,
            phone_no=phone_no,
            email=email,
            is_active = True,
            is_customer = True,
            password=make_password(password)  # Hash password
        )
        user.save()

        return JsonResponse({'status': 'success', 'message': 'User registered successfully'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})