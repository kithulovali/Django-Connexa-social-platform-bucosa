app_name = 'activities'

from django.urls import path 
from . import views
from django.conf.urls.static import static
from django.conf import settings
from users.views import analytics_dashboard

urlpatterns = [

    path('home/' , views.home_activities , name='home'),
    path('home/fellowship/', views.home_fellowship, name='home_fellowship'),
    # path('event/', views.event_activity , name ='event'),  # Removed: view does not exist
    path('group/' , views.group_activities , name='group'),
    # --- Added for full CRUD functionality ---
    path('post/create/', views.create_post, name='create_post'),
    path('post/create/group/<int:group_id>/', views.create_post, name='create_post_in_group'),
    path('event/create/', views.create_event, name='create_event'),
    path('event/create/group/<int:group_id>/', views.create_event, name='create_event_in_group'),
    path('post/<int:pk>/edit/', views.edit_post, name='edit_post'),
    path('post/<int:pk>/delete/', views.delete_post, name='delete_post'),
    path('event/<int:pk>/edit/', views.edit_event, name='edit_event'),
    path('event/<int:pk>/delete/', views.edit_event, name='delete_event'),
    path('event/<int:pk>/', views.event_detail, name='event_detail'),
    path('group_admin/<int:group_id>/', views.group_admin, name='group_admin'),
    path('remove_user_from_group/<int:group_id>/<int:user_id>/', views.remove_user_from_group, name='remove_user_from_group'),
    path('add_user_to_group/<int:group_id>/', views.add_user_to_group, name='add_user_to_group'),
    path('dashboard/', analytics_dashboard, name='analytics_dashboard'),
    path('event/<int:event_id>/attend/', views.attend_event, name='attend_event'),
    path('search_feed/', views.search_and_filter_feed, name='search_and_filter_feed'),
    path('post/<int:post_id>/add_comment/', views.add_comment, name='add_comment'),
    path('post/<int:post_id>/like/', views.like_post, name='like_post'),
    path('post/<int:post_id>/save/', views.save_post, name='save_post'),
    path('post/<int:post_id>/share/', views.share_post, name='share_post'),
    path('post/<int:post_id>/repost/', views.repost_post, name='repost_post'),
    path('saved/', views.saved_posts, name='saved_posts'),
    path('reposts/', views.user_reposts, name='my_reposts'),
    path('user/<int:user_id>/reposts/', views.user_reposts, name='user_reposts'),
    path('post/<int:pk>/', views.post_detail, name='post_detail'),
    path('share_to_user/', views.share_to_user, name='share_to_user'),
    path('share/<int:post_id>/', views.share_page, name='share_page'),
    path('event/<int:event_id>/register/', views.register_event, name='register_event'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
