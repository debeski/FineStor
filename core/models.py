from django.db import models
from storage.models import ExportRecord
from django.contrib.contenttypes.fields import GenericRelation


# Entity Models:
class Company(models.Model):
    name = models.CharField(max_length=255, verbose_name="اسم الشركة")
    address = models.CharField(max_length=255, verbose_name="العنوان", blank=True)
    phone = models.CharField(max_length=15, verbose_name="رقم الهاتف", blank=True)

    class Meta:
        verbose_name = "شركة"
        verbose_name_plural = "الشركات"
        ordering = ['name']

    def __str__(self):
        return self.name


class Department(models.Model):
    type = models.CharField(max_length=50, choices=[
        ('Department', 'ادارة'),
        ('Office', 'مكتب'),
        ('Section', 'قسم'),
        ('Unit', 'وحدة'),
    ], verbose_name="التقسيم الاداري")
    name = models.CharField(max_length=255, verbose_name="اسم التقسيم")
    selections = GenericRelation(ExportRecord)

    class Meta:
        verbose_name = "تقسيم اداري"
        verbose_name_plural = "التقسيمات الادارية"
        ordering = ['name']

    def __str__(self):
        return self.name


class Affiliate(models.Model):
    type = models.CharField(max_length=50, choices=[
        ('Ministry', 'وزارة'),
        ('Authority', 'هيئة'),
        ('Center', 'مركز'),
        ('Monitor', 'مراقبة'),
        ('Project', 'مشروع'),

    ], verbose_name="نوع الجهة")
    name = models.CharField(max_length=255, verbose_name="اسم الجهة")
    address = models.CharField(max_length=255, verbose_name="العنوان", blank=True)

    class Meta:
        verbose_name = "جهة"
        verbose_name_plural = "الجهات الاخرى"
        ordering = ['-name']

    def __str__(self):
        return self.name


class SubAffiliate(models.Model):
    affiliate = models.ForeignKey('Affiliate', related_name='subaffiliates', on_delete=models.CASCADE)
    subname = models.CharField(max_length=255, verbose_name="اسم التقسيم")
    subtype = models.CharField(max_length=50, choices=[
        ('Department', 'ادارة'),
        ('Office', 'مكتب'),
        ('Section', 'قسم'),
    ], verbose_name="التقسيم الاداري")
    selections = GenericRelation(ExportRecord)

    class Meta:
        verbose_name = "تقسيم فرعي"
        verbose_name_plural = "التقسيمات الفرعية"
        ordering = ['-subtype']

    def __str__(self):
        return self.subname + ' ب' + self.affiliate.name


class Employee(models.Model):
    name = models.CharField(max_length=255, verbose_name="اسم الموظف")
    job_title = models.CharField(max_length=50, choices=[
        ('GM', 'المدير العام'),
        ('manager', 'مدير'),
        ('chief', 'رئيس'),
        ('employee', 'موظف'),
        ('financer', 'مراقب مالي'),
    ], verbose_name="الوظيفة")
    department = models.ForeignKey('Department', related_name='deptemployees', on_delete=models.PROTECT, verbose_name="الادارة/المكتب")
    email = models.EmailField(verbose_name="البريد الالكتروني")
    phone = models.CharField(max_length=15, verbose_name="رقم الهاتف")
    date_employed = models.DateField(verbose_name="تاريخ التعيين")
    selections = GenericRelation(ExportRecord)

    class Meta:
        verbose_name = "موظف"
        verbose_name_plural = "الموظفين"
        ordering = ['date_employed']

    def __str__(self):
        return self.name

