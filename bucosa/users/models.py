from django.db import models
from django.contrib.auth.models import User, Group 
from django.utils.encoding import force_str
from django_resized import ResizedImageField
from cloudinary.models import CloudinaryField

class user_profile(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='profile',
        db_index=True  # Added index
    ) 
    email = models.EmailField('email address', db_index=True ,blank=True, null=True)  
    bio = models.TextField(max_length=500, blank=True)
    profile_image = CloudinaryField('profile_pics', blank=True, null=True)
    cover_image = CloudinaryField('profile_covers', blank=True, null=True)
    website = models.URLField(blank=True, null=True, db_index=True)  
    location = models.CharField(max_length=100, blank=True, db_index=True)
    date_joined = models.DateTimeField(auto_now_add=True, db_index=True)  
    last_login = models.DateTimeField(auto_now=True)
    fcm_token = models.CharField(max_length=255, blank=True, null=True, db_index=True) 
    
    PRIVACY_CHOICES = [
        ('public', 'Public'),
        ('followers', 'Followers Only'),
        ('private', 'Private'),
    ]
    privacy = models.CharField(max_length=20, choices=PRIVACY_CHOICES, default='public', db_index=True)  

    class Meta:
        indexes = [
            models.Index(fields=['privacy']),
            models.Index(fields=['date_joined']),
        ]
    
    def __str__(self):
        if self.user:
            name = f"{self.user.first_name or ''} {self.user.last_name or ''}".strip()
            if name:
                return force_str(name)
            if self.user.username:
                return force_str(self.user.username)
        return force_str(self.email or f"Profile #{self.pk}")

class user_following(models.Model):
    user = models.ForeignKey(
        User, 
        related_name='following', 
        on_delete=models.CASCADE,
        db_index=True  
    )
    following_user = models.ForeignKey(
        User, 
        related_name='followers', 
        on_delete=models.CASCADE,
        db_index=True  
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True) 
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'following_user'], name='unique_followers')
        ]
        indexes = [
            models.Index(fields=['-created_at']),  
            models.Index(fields=['user', 'following_user']), 
        ]
        ordering = ['-created_at']

class GroupProfile(models.Model):
    group = models.OneToOneField(
        Group, 
        on_delete=models.CASCADE, 
        related_name='profile',
        db_index=True 
    )
    creator = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='created_groups',
        db_index=True 
    )
    admins = models.ManyToManyField(
        User, 
        related_name='admin_groups', 
        blank=True,
        db_index=True 
    )
    description = models.TextField(blank=True)
    profile_image = CloudinaryField('group_pics', blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['creator']),
        ]

    def save(self, *args, **kwargs):
        if not self.creator_id:
            raise ValueError('A group must have a creator!')
        super().save(*args, **kwargs)
       
        if self.creator and self.pk and not self.admins.filter(pk=self.creator.pk).exists():
            self.admins.add(self.creator)

    def __str__(self):
        return self.group.name