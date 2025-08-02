from django.urls import path
from . import admin_views

app_name = 'user_admin'

urlpatterns = [
    path('', admin_views.admin_dashboard, name='dashboard'),
    path('users/', admin_views.user_list, name='user_list'),
    path('users/create/', admin_views.user_create, name='user_create'),
    path('users/<int:user_id>/', admin_views.user_detail, name='user_detail'),
    path('users/<int:user_id>/edit/', admin_views.user_edit, name='user_edit'),
    path('users/<int:user_id>/delete/',
         admin_views.user_delete, name='user_delete'),
    path('users/<int:user_id>/toggle-status/',
         admin_views.user_toggle_status, name='user_toggle_status'),
    path('users/bulk-actions/', admin_views.bulk_actions, name='bulk_actions'),
]
