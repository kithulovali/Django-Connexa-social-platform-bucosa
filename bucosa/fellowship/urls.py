  
from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', views.fellowship_detail, kwargs={'fellowship_id': 1}, name='fellowship'),  # Root page is fellowship_detail for id=1 (or change as needed)
    path('edit/<int:fellowship_id>/', views.edit_fellowship, name='edit_fellowship'),
    path('donate/', views.donate_view, name='donate'),
    path('<int:fellowship_id>/post/<int:post_id>/like/', views.like_fellowship_post, name='like_fellowship_post'),
    path('<int:fellowship_id>/post/<int:post_id>/comment/', views.comment_fellowship_post, name='comment_fellowship_post'),
    path('<int:fellowship_id>/post/<int:post_id>/share/', views.share_fellowship_post, name='share_fellowship_post'),
    path("fellowship_history/", views.fellowship_history, name="fellowship_history"),
    path('edit_fellowship_model/<int:fellowship_id>/', views.edit_fellowship_model, name='edit_fellowship_model'),
    path('<int:fellowship_id>/', views.fellowship_detail, name='fellowship_detail'),
    path('<int:fellowship_id>/join/', views.join_fellowship, name='join_fellowship'),
    path('<int:fellowship_id>/post/', views.create_fellowship_post, name='create_fellowship_post'),
    path('<int:fellowship_id>/event/', views.create_fellowship_event, name='create_fellowship_event'),
    path('<int:fellowship_id>/events/', views.fellowship_events, name='fellowship_events'),
    path('<int:fellowship_id>/admin/', views.fellowship_admin_dashboard, name='fellowship_admin'),
    path('membership_request/<int:request_id>/accept/', views.accept_membership_request, name='accept_membership_request'),
    path('membership_request/<int:request_id>/refuse/', views.refuse_membership_request, name='refuse_membership_request'),
    path('<int:fellowship_id>/membership_requests/', views.membership_requests_page, name='membership_requests_page'),
    path('<int:fellowship_id>/admin/my-content/', views.admin_my_posts_events, name='admin_my_posts_events'),
    path('<int:fellowship_id>/post/<int:post_id>/edit/', views.edit_fellowship_post, name='edit_fellowship_post'),
    path('<int:fellowship_id>/post/<int:post_id>/delete/', views.delete_fellowship_post, name='delete_fellowship_post'),
    path('<int:fellowship_id>/event/<int:event_id>/edit/', views.edit_fellowship_event, name='edit_fellowship_event'),
    path('<int:fellowship_id>/event/<int:event_id>/delete/', views.delete_fellowship_event, name='delete_fellowship_event'),
    path('donations/', views.donation_list_view, name='donation_list'),
    path('<int:fellowship_id>/post/<int:post_id>/like/', views.like_fellowship_post, name='like_fellowship_post'),
    path('<int:fellowship_id>/post/<int:post_id>/comment/', views.comment_fellowship_post, name='comment_fellowship_post'),
    path('<int:fellowship_id>/post/<int:post_id>/share/', views.share_fellowship_post, name='share_fellowship_post'),
    path('profile/', views.create_fellowship_profile, name='fellowship_profile_detail'),
    path('edit/', views.edit_fellowship_profile, name='edit_fellowship_profile'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
