from django.db import models
from django.contrib.auth.models import User

class PrivateMessage(models.Model):
    def get_absolute_url(self):
        # Always redirect to the chat with the other user (for the recipient)
        return f"/users/messages/{self.sender.id}/" if self.recipient_id == self._get_request_user_id() else f"/users/messages/{self.recipient.id}/"

    def _get_request_user_id(self):
        # This is a workaround for Django context, will work for notification links
        try:
            from threading import local
            return getattr(local(), 'request_user_id', self.recipient_id)
        except Exception:
            return self.recipient_id
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField(blank=True)
    image = models.ImageField(upload_to='private_message_images/', blank=True, null=True)
    video = models.FileField(upload_to='private_message_videos/', blank=True, null=True)
    file = models.FileField(upload_to='private_message_files/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"From {self.sender.username} to {self.recipient.username} at {self.created_at}"
