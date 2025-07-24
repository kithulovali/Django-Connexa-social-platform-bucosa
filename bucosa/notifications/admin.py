from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'recipient', 'notification_type', 'is_read', 'timestamp')
    list_filter = ('notification_type', 'is_read', 'timestamp')
    search_fields = ('sender__username', 'recipient__username', 'message')
