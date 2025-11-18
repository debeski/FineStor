# Imports of the required python modules and libraries
######################################################
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'email', 'is_staff', 'is_active', 'phone', 'occupation']
    list_filter = ['is_staff', 'is_active']
    search_fields = ['username', 'email']
    ordering = ['username']

admin.site.register(User, CustomUserAdmin)
admin.site.unregister(Group)
