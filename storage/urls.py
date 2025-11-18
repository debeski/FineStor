from django.urls import path
from . import views
from core import views as users
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('storage/assets/', views.manage_assets, name='manage_assets'),
    # path('storage/assets/<str:category>/', views.manage_assets, name='manage_assets'),
    path('storage/categories/', views.manage_category, name='manage_category'),
    path('storage/categories/<int:category_id>/', views.manage_category, name='edit_category'),
    path('storage/import/', views.import_records, name='import_records'),
    path('storage/import/new/', views.import_create, name='import_create'),
    path("storage/import/new/add/", views.import_item_add, name="import_item_add"),
    path('storage/import/new/<int:asset_id>/', views.import_item_delete, name='import_item_delete'),
    path('storage/import/<int:trans_id>/', views.import_details, name='import_details'),
    path('storage/<str:model>/pdf/<int:trans_id>/', views.gen_pdf, name='gen_pdf'),
    path('storage/export/', views.export_records, name='export_records'),
    path('storage/export/new/<str:export_type>', views.export_create, name='export_create'),
    path("storage/export/new/<str:export_type>/add/", views.export_item_add, name="export_item_add"),
    path('storage/export/new/<str:export_type>/<int:item_id>/', views.export_item_delete, name='export_item_delete'),
    path('storage/export/<int:trans_id>/', views.export_details, name='export_details'),
    
    path('storage/returns/', views.return_records, name='return_records'),
    path('storage/returns/new/<str:return_type>', views.return_create, name='return_create'),

    path('storage/report/', views.report_view, name='storage_report'),
    path('storage/report/pdf/', views.report_pdf, name='report_pdf'),
    # path('storage/report/inventory', views.report_inventory, name='storage_report_inventory'),

    path('get_assets/<int:category_id>/', views.get_assets, name='get_assets'),
    path('get_ex_assets/<int:category_id>/', views.get_ex_assets, name='get_ex_assets'),
    # path('storage/import/edit/<int:trans_id>/', views.import_record_edit, name='import_item_edit'),
    # path('storage/import/record/delete/<int:trans_id>/', views.import_record_delete, name='import_record_delete'),

]