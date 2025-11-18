from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.contrib import admin


urlpatterns = [
    # Index Url
    path('', views.index, name='index'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    # path('clear_login_modal_flag/', views.clear_login_modal_flag, name='clear_login_modal_flag'),
    path('manage/<str:model_name>/', views.manage_sections, name='manage_sections'),
    path('manage/affiliate/subs/<int:affiliate_id>/', views.sub_affiliate_view, name='sub_affiliate_view'),
    path("toggle-sidebar/", views.toggle_sidebar, name="toggle_sidebar"),

]