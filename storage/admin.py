from django.contrib import admin
from .models import Asset, AssetCategory, ImportRecord, ExportRecord, Committee

@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'discription')
    search_fields = ('name', 'discription')

# Admin Configuration for Asset
@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'brand', 'stock', 'unit', 'price_history', 'pic')
    list_filter = ('category',)
    search_fields = ('name', 'brand', 'brand_en')
    ordering = ('category', 'name')

# Admin Configuration for ImportRecord
@admin.register(ImportRecord)
class ImportRecordAdmin(admin.ModelAdmin):
    list_display = ('company', 'date', 'assign_number', 'assign_date', 'created_at', 'updated_at')
    list_filter = ('trans_id', 'company', 'date', 'assign_date')
    search_fields = ('items', 'trans_id')
    ordering = ('trans_id', 'company', 'date', 'assign_date')

# Admin Configuration for ExportRecord
@admin.register(ExportRecord)
class ExportRecordAdmin(admin.ModelAdmin):
    list_display = ('trans_id', 'date', 'export_type', 'entity_type', 'entity_id', 'created_at', 'updated_at')
    list_filter = ('entity_type', 'date', 'export_type')
    search = ('items', 'trans_id')
    ordering = ('trans_id', 'date', 'export_type')


@admin.register(Committee)
class CommitteeAdmin(admin.ModelAdmin):
    list_display = ('year', 'president')
    list_filter = ('year', 'president')
    search = ('members', 'president')
    ordering = ('year',)