from django.urls import path
from .views import send_notification_view

urlpatterns = [
    path('send/', send_notification_view, name='send_notification'),
]
