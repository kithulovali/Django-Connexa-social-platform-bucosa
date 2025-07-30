import os
import json
import requests
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.conf import settings
from .models import Notification
from google.oauth2 import service_account
import google.auth.transport.requests

SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), 'service-account.json')

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
    # Real-time WebSocket notification
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

def send_push_notification_v1(token, title, body, data=None):
    PROJECT_ID = 'bucosa-5ccde'  # Your Firebase project ID

    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=['https://www.googleapis.com/auth/firebase.messaging']
    )
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)
    access_token = credentials.token

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json; UTF-8',
    }
    message = {
        "message": {
            "token": token,
            "notification": {
                "title": title,
                "body": body,
            },
            "data": data or {},
        }
    }
    url = f"https://fcm.googleapis.com/v1/projects/{PROJECT_ID}/messages:send"
    response = requests.post(url, headers=headers, data=json.dumps(message))
    return response.json()