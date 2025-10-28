from django.contrib import admin
from .models import User, SystemShutdown

# Register your models here.
admin.site.register(User)
admin.site.register(SystemShutdown)