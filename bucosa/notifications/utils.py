from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.conf import settings
from .models import Notification
from users.utils import get_display_name

def create_notification(sender, recipient, notification_type, message='', related_object=None):
    content_type = None
    object_id = None
    if related_object:
        content_type = ContentType.objects.get_for_model(related_object)
        object_id = related_object.pk
    notification = Notification.objects.create(
        sender=sender,
        recipient=recipient,
        notification_type=notification_type,
        message=message,
        content_type=content_type,
        object_id=object_id
    )
    # Only send email for event registration
    if notification_type == 'event_registration' and recipient.email:
        subject = "Event Registration Confirmation"
        email_message = message or f"You have successfully registered for an event."
        send_mail(
            subject,
            email_message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient.email],
            fail_silently=True,
        )
    return notification

def send_custom_notification_email(notification, recipient):
    """
    Send a customized email based on notification type and recipient role.
    """
    subject = ""
    message = ""
    url = settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000/'
    # Example: customize for different notification types and roles
    if notification.notification_type == 'comment':
        subject = f"New Comment on Your Post"
        message = f"Hi {get_display_name(recipient)},\n\nYou have a new comment: {notification.message}\n\nView it here: {url}"
    elif notification.notification_type == 'like':
        subject = f"Your Post Was Liked!"
        message = f"Hi {get_display_name(recipient)},\n\n{get_display_name(notification.sender)} liked your post.\n\nView it here: {url}"
    elif notification.notification_type == 'mention':
        subject = f"You Were Mentioned!"
        message = f"Hi {get_display_name(recipient)},\n\nYou were mentioned: {notification.message}\n\nView it here: {url}"
    elif notification.notification_type == 'group':
        subject = f"Group Update"
        message = f"Hi {get_display_name(recipient)},\n\n{notification.message}\n\nView group: {url}"
    elif notification.notification_type == 'message':
        subject = f"New Private Message"
        message = f"Hi {get_display_name(recipient)},\n\nYou have a new private message from {get_display_name(notification.sender)}.\n\nView it here: {url}"
    else:
        subject = f"Notification from Bucosa"
        message = f"Hi {get_display_name(recipient)},\n\n{notification.message}\n\nView it here: {url}"
    # You can further customize based on recipient roles (e.g., is_superuser, is_staff)
    if hasattr(recipient, 'is_superuser') and recipient.is_superuser:
        subject = "[ADMIN] " + subject
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [recipient.email],
        fail_silently=True,
    )
