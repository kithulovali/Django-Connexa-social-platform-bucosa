from django.urls import path 
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', views.fellowship_detail, kwargs={'fellowship_id': 1}, name='fellowship'),  # Root page is fellowship_detail for id=1 (or change as needed)
    path('edit/<int:fellowship_id>/', views.edit_fellowship, name='edit_fellowship'),
    path('donate/',views.donate_view , name ='donate'),
    path("fellowship_history/", views.fellowship_history, name="fellowship_history"),
    path('edit_fellowship_model/<int:fellowship_id>/', views.edit_fellowship_model , name='edit_fellowship_model'),
    path('<int:fellowship_id>/', views.fellowship_detail, name='fellowship_detail'),
    path('<int:fellowship_id>/join/', views.join_fellowship, name='join_fellowship'),
    path('<int:fellowship_id>/post/', views.create_fellowship_post, name='create_fellowship_post'),
    path('<int:fellowship_id>/event/', views.create_fellowship_event, name='create_fellowship_event'),
    path('<int:fellowship_id>/admin/', views.fellowship_admin_dashboard, name='fellowship_admin'),
    path('<int:fellowship_id>/admin/my-content/', views.admin_my_posts_events, name='admin_my_posts_events'),
    path('<int:fellowship_id>/post/<int:post_id>/edit/', views.edit_fellowship_post, name='edit_fellowship_post'),
    path('<int:fellowship_id>/post/<int:post_id>/delete/', views.delete_fellowship_post, name='delete_fellowship_post'),
    path('<int:fellowship_id>/event/<int:event_id>/edit/', views.edit_fellowship_event, name='edit_fellowship_event'),
    path('<int:fellowship_id>/event/<int:event_id>/delete/', views.delete_fellowship_event, name='delete_fellowship_event'),
    path('donations/', views.donation_list_view, name='donation_list'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
