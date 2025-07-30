from django.urls import path
from . import views
from .views import send_notification_view

urlpatterns = [
    path('send/', send_notification_view, name='send_notification'),
    path('mark_read/', views.mark_notifications_read, name='mark_notifications_read'),
    
]


