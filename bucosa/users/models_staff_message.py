from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from cloudinary.models import CloudinaryField
class staff_messages(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE , related_name = 'send_messages')
    recipients = models.ManyToManyField(User,related_name = 'receive_messages')
    image = CloudinaryField('staff_message_images/')
    message = models.TextField()
    created_at = models.DateTimeField(default =timezone.now)
    
    def __str__(self):
        return self.sender