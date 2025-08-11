from celery import shared_task
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from activities.models import Announcement
from notifications.utils import create_notification

@shared_task
def send_announcement_notifications(announcement_id):
    try:
        announcement = Announcement.objects.get(id=announcement_id)
    except Announcement.DoesNotExist:
        return
    users = User.objects.exclude(id=announcement.sender.id)
    for user in users:
        # In-app notification
        create_notification(
            sender=announcement.sender,
            recipient=user,
            notification_type='other',
            message=f"{announcement.title}: {announcement.message}",
            related_object=announcement
        )
        # Email notification
        if user.email:
            send_mail(
                f"New Announcement: {announcement.title}",
                announcement.message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=True,
            )
