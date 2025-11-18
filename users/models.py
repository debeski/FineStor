# Imports of the required python modules and libraries
######################################################
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings  # Use this to reference the custom user model
from django.contrib.postgres.fields import JSONField

class CustomUser(AbstractUser):
    phone = models.CharField(max_length=15, blank=True, null=True, verbose_name="رقم الهاتف")
    occupation = models.CharField(max_length=100, blank=True, null=True, verbose_name="جهة العمل")
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

class UserActivityLog(models.Model):
    ACTION_TYPES = [
        ('LOGIN', 'تسجيل دخـول'),
        ('LOGOUT', 'تسجيل خـروج'),
        ('CREATE', 'انشـاء'),
        ('UPDATE', 'تعديـل'),
        ('DELETE', 'حــذف'),
        ('VIEW', 'عـرض'),
        ('DOWNLOAD', 'تحميل'),
        ('CONFIRM', 'تأكيـد'),
        ('REJECT', 'رفــض'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, verbose_name="اسم المستخدم", null=True, blank=True)
    action = models.CharField(max_length=10, choices=ACTION_TYPES, verbose_name="العملية")
    model_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="القسم")
    object_id = models.IntegerField(blank=True, null=True, verbose_name="ID")
    number = models.CharField(max_length=50, null=True, blank=True, verbose_name="المستند")
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name="عنوان IP")
    user_agent = models.TextField(blank=True, null=True, verbose_name="agent")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="الوقت")

    def __str__(self):
        return f"{self.user} {self.action} {self.model_name or 'General'} at {self.timestamp}"

