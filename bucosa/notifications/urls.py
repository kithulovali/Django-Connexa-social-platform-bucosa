from django.urls import path
from . import views


urlpatterns = [
    path('send/', views.send_notification_view, name='send_notification'),
    path('', views.notifications_list, name='notifications_list'),
    path('mark_read/', views.mark_notifications_read, name='mark_notifications_read'),
    path('api/unread_count/', views.api_unread_notifications_count, name='api_unread_notifications_count'),
    
]


