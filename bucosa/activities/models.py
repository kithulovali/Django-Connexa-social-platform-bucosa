from django.db import models
from django.contrib.auth.models import User, Group
from django.utils import timezone
from uuid import uuid4
from django.utils.text import slugify
from django_resized import ResizedImageField
from cloudinary.models import CloudinaryField
# Create your models here.

class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=200)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    attendees = models.ManyToManyField(User, related_name='attended_events', blank=True)
    cover_image =  CloudinaryField('event_covers', blank=True, null=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True, related_name='events')
    registered_users = models.ManyToManyField(User, related_name='registered_events', blank=True)
    
    class Meta:
        ordering = ['start_time']
    
    def __str__(self):
        return self.title

    def can_edit(self, user):
        return self.creator == user

    def can_delete(self, user):
        return self.creator == user

class Post(models.Model):
    def get_original(self):
        return self.repost_of if self.repost_of else self

    @property
    def share_count(self):
        from .models import Share
        original = self.get_original()
        return Share.objects.filter(post=original).count()

    @property
    def repost_count(self):
        original = self.get_original()
        return Post.objects.filter(repost_of=original).count()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True, related_name='posts')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    image =  CloudinaryField('post_images', blank=True, null=True)
    video = models.FileField(upload_to='post_videos/', blank=True, null=True)

    PRIVACY_CHOICES = [
        ('PUBLIC', 'Public'),
        ('FRIENDS', 'Friends Only'),
        ('PRIVATE', 'Private'),
    ]
    privacy = models.CharField(max_length=7, choices=PRIVACY_CHOICES, default='PUBLIC')
    repost_of = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='repost_children')
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Post by {self.author.username}"

    def can_edit(self, user):
        return self.author == user

    def can_delete(self, user):
        return self.author == user

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('activities:post_detail', args=[str(self.id)])

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.username}"

    def can_edit(self, user):
        return self.author == user

    def can_delete(self, user):
        return self.author == user

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')

class Save(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='saves')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')

class Share(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='shares')
    created_at = models.DateTimeField(auto_now_add=True)

class Repost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reposts')
    created_at = models.DateTimeField(auto_now_add=True)