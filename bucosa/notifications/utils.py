from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.conf import settings
from .models import Notification

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
    # Send real-time notification
    channel_layer = get_channel_layer()
    group_name = f"notifications_{recipient.id}"
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "send_notification",
            "notification": {
                "id": notification.id,
                "sender": str(notification.sender),
                "notification_type": notification.notification_type,
                "message": notification.message,
                "timestamp": notification.timestamp.isoformat(),
                "is_read": notification.is_read,
            },
        },
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
