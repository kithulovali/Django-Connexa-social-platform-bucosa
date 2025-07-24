from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.bucosa_main, name='bucosa_main'),
    path('history/', views.government_history, name='government_history'),
    path('past/<int:gov_id>/', views.past_government_detail, name='past_government_detail'),
    path('admin/requests/', views.admin_manage_requests, name='admin_manage_requests'),
    path('admin/create-current/', views.admin_create_current_government, name='admin_create_current_government'),
    path('admin/create-past/', views.admin_create_past_government, name='admin_create_past_government'),
    # --- CRUD for government members ---
    path('add-member/', views.add_member, name='add_member'),
    path('edit-member/<int:member_id>/', views.edit_member, name='edit_member'),
    path('delete-member/<int:member_id>/', views.delete_member, name='delete_member'),
    # --- CRUD for current government ---
    path('edit-current/', views.edit_current_government, name='edit_current_government'),
    path('delete-current/', views.delete_current_government, name='delete_current_government'),
    # --- CRUD for past governments ---
    path('edit-past/<int:gov_id>/', views.edit_past_government, name='edit_past_government'),
    path('delete-past/<int:gov_id>/', views.delete_past_government, name='delete_past_government'),
    # --- CRUD for past government members ---
    path('past/<int:gov_id>/add-member/', views.add_past_member, name='add_past_member'),
    path('past/edit-member/<int:member_id>/', views.edit_past_member, name='edit_past_member'),
    path('past/delete-member/<int:member_id>/', views.delete_past_member, name='delete_past_member'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)