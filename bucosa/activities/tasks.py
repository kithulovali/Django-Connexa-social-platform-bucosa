# tasks.py
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from activities.models import Announcement

def send_announcement_notifications(announcement_id):
    try:
        announcement = Announcement.objects.get(id=announcement_id)
    except Announcement.DoesNotExist:
        return

    users = User.objects.exclude(id=announcement.sender.id)

    for user in users:
        if user.email:
            send_mail(
                "Hello from Django 🎉",
                "This is a test email sent using Gmail SMTP.",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
