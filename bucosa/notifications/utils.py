# utils.py
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from activities.models import Announcement
import logging

logger = logging.getLogger(__name__)

def send_announcement_notifications(announcement_id):
    try:
        announcement = Announcement.objects.get(id=announcement_id)
    except Announcement.DoesNotExist:
        logger.error(f"Announcement {announcement_id} not found.")
        return

    users = User.objects.exclude(id=announcement.sender.id)

    for user in users:
        if not user.email:
            continue

        try:
            validate_email(user.email)
            send_mail(
                subject=f"📢 {announcement.title}",
                message=announcement.content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            logger.info(f"Email sent to {user.email}")
        except ValidationError:
            logger.warning(f"Invalid email: {user.email}")
        except Exception as e:
            logger.error(f"Failed to send email to {user.email}: {e}")
