  
from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', views.fellowship_detail, kwargs={'fellowship_id': 1}, name='fellowship'), 
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
    path('<int:fellowship_id>/create-verse/', views.create_verse, name='create_daily_verse'),
    path("fellowship/verse-history/", views.verse_history, name="verse_history"),
    path("verses/history/", views.verse_history, name="verse_history"),
    path("verse/<int:verse_id>/edit/", views.edit_verse, name="edit_verse"),
    path("verse/<int:verse_id>/delete/", views.delete_verse, name="delete_verse"),
    path('fellowship/<int:fellowship_id>/livestream/create/', views.create_livestream, name='create_livestream'),
    path('livestream/<int:livestream_id>/', views.livestream_detail, name='livestream_detail'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
