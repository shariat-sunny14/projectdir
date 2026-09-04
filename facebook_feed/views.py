from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from .models import FacebookPost, FacebookSettings
from .forms import FacebookSettingsForm
from .tasks import sync_facebook_posts
from django.contrib.auth.decorators import login_required


def facebook_posts(request):

    fb_posts = FacebookPost.objects.all().order_by('-created_time')

    return render(request, 'facebook_feed/facebook_posts.html', {'fb_posts': fb_posts})

@login_required()
def facebook_posts_sync(request):
    posts = FacebookPost.objects.all().order_by('-created_time')
    settings_obj = FacebookSettings.objects.first()
    return render(request, 'facebook_feed/facebook_post_sync.html', {
        'posts': posts,
        'settings': settings_obj
    })

@login_required()
def facebook_settings(request):
    settings_obj = FacebookSettings.objects.first()
    if request.method == "POST":
        form = FacebookSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Settings saved successfully.")
            return redirect('facebook_settings')
    else:
        form = FacebookSettingsForm(instance=settings_obj)

    return render(request, 'facebook_feed/facebook_settings.html', {'form': form})

@login_required()
def sync_facebook(request):
    if request.method == "POST":
        result = sync_facebook_posts()
        return JsonResponse({'message': result})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)