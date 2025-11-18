# Imports of the required python modules and libraries
######################################################
from django.apps import AppConfig

def custom_permission_str(self):
    """Custom Arabic translations for Django permissions"""
    model_name = str(self.content_type)
    permission_name = str(self.name)

    # Translate default permissions
    if "Can add" in permission_name:
        permission_name = permission_name.replace("Can add", " إضافة ")
    elif "Can change" in permission_name:
        permission_name = permission_name.replace("Can change", " تعديل ")
    elif "Can delete" in permission_name:
        permission_name = permission_name.replace("Can delete", " حذف ")
    elif "Can view" in permission_name:
        permission_name = permission_name.replace("Can view", " عرض ")

    return f"{permission_name}"

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    verbose_name = "المستخدمين"

    def ready(self):
        from django.contrib.auth.models import Permission
        Permission.add_to_class('__str__', custom_permission_str)