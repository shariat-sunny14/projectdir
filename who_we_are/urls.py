# urls.py
from django.urls import path
from . import views

app_name = "who_we_are"

urlpatterns = [
    path("who-we-are/", views.who_we_are_view, name="who_we_are"),
    path("who-we-are/edit/", views.who_we_are_edit_view, name="who_we_are_edit"),
]