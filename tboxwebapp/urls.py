"""tboxwebapp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib.auth.decorators import login_required
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include, re_path
from django.shortcuts import render

# Define a custom view for handling "page not found" errors
@login_required()
def page_notfound(request):

    return render(request, 'page_notFound/page_not_found.html', status=404)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('django.contrib.auth.urls')),
    path('', include('user_auth.urls')),
    path('', include('user_setup.urls')),
    path('', include('module_setup.urls')),
    path('', include('advertisement_item.urls')),
    path('', include('login_theme.urls')),
    path('', include('packages.urls')),
    path('', include('why_us.urls')),
    path('', include('photo_gallery.urls')),
    path('', include('booking_us.urls')),
    path('', include('order_list.urls')),
    path('', include('inquire_list.urls')),
    path('', include('enroll_us.urls')),
    path('', include('facebook_feed.urls')),
    path('', include('youtube_gallery.urls')),
    path('', include('about_us.urls')),
]



# Add a catch-all URL pattern for "page not found" errors
urlpatterns += [
    re_path(r'^.*/$', page_notfound, name='page_notfound'),
]

# Serve media files only if DEBUG is True
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)