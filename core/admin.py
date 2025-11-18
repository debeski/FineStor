from django.contrib import admin

from .models import Company, Department, Affiliate, SubAffiliate, Employee

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'phone')
    search_fields = ('name',)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('type', 'name')
    search_fields = ('name',)

@admin.register(Affiliate)
class AffiliateAdmin(admin.ModelAdmin):
    list_display = ('type', 'name', 'address')
    search_fields = ('name',)

@admin.register(SubAffiliate)
class SubAffiliateAdmin(admin.ModelAdmin):
    list_display = ('affiliate', 'subname', 'subtype')
    search_fields = ('subname',)

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'job_title', 'department', 'email', 'date_employed')
    search_fields = ('name', 'email')
    list_filter = ('job_title', 'department')
