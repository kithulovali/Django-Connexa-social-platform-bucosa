# models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from cloudinary.models import CloudinaryField

class staff_messages(models.Model): 
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_staff_messages')
    recipients = models.ManyToManyField(User, related_name='received_staff_messages')
    subject = models.CharField(max_length=200)  
    message = models.TextField()
    image = CloudinaryField('staff_message_images/', blank=True, null=True)  
    is_read = models.BooleanField(default=False)  
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')  
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.subject} - {self.sender.username}"