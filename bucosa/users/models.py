from django.db import models
from django.contrib.auth.models import User, Group 
from .models_group_message import GroupMessage
from .models_group_reaction import GroupMessageReaction
from .models_private_message import PrivateMessage
from .models_block_report import UserBlock, UserReport
from .models_push_subscription import PushSubscription
from django.apps import AppConfig
from django.utils.encoding import force_str
from django_resized import ResizedImageField
from cloudinary.models import CloudinaryField
# Create your models here.

class user_profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile') 
    email = models.EmailField('email address', unique=True)
    bio = models.TextField(max_length=500, blank=True)
    profile_image = CloudinaryField('profile_pics', blank=True, null=True)
    cover_image =  CloudinaryField('profile_covers', blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    fcm_token = models.CharField(max_length=255, blank=True, null=True, help_text="FCM device token for push notifications")
    
    PRIVACY_CHOICES = [
        ('public', 'Public'),
        ('followers', 'Followers Only'),
        ('private', 'Private'),
    ]
    privacy = models.CharField(max_length=20, choices=PRIVACY_CHOICES, default='public')

    from django.utils.encoding import force_str
    
    def __str__(self):
        # Extra defensive: cast all fields to string, handle None, and ensure only plain strings are returned
        if self.user:
            first_name = str(getattr(self.user, 'first_name', '') or '')
            last_name = str(getattr(self.user, 'last_name', '') or '')
            full_name = f"{first_name} {last_name}".strip()
            if full_name and full_name != '':
                return force_str(full_name)
            username = str(getattr(self.user, 'username', '') or '')
            if username:
                return force_str(username)
        email = str(getattr(self, 'email', '') or '')
        if email:
            return force_str(email)
        return force_str(f"Profile #{self.pk}")
    
class user_following(models.Model):
    user = models.ForeignKey(User, related_name='following', on_delete=models.CASCADE)
    following_user = models.ForeignKey(User, related_name='followers', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'following_user'], name='unique_followers')
        ]
        ordering = ['-created_at']

class GroupProfile(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE, related_name='profile')
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    admins = models.ManyToManyField(User, related_name='admin_groups', blank=True)
    description = models.TextField(blank=True)
    profile_image =  CloudinaryField('group_pics', blank=True, null=True)


    def save(self, *args, **kwargs):
        if not self.creator_id:
            raise ValueError('A group must have a creator!')
        super().save(*args, **kwargs)
       
        if self.creator and self.pk and not self.admins.filter(pk=self.creator.pk).exists():
            self.admins.add(self.creator)

    def __str__(self):
        return self.group.name

class UsersConfig(AppConfig):
    name = 'users'

    def ready(self):
        import bucosa.users.signals