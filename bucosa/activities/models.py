from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.contrib.auth.models import User, Group
from django.utils import timezone
from uuid import uuid4
from django.utils.text import slugify
from django_resized import ResizedImageField
from cloudinary.models import CloudinaryField

from django.utils.functional import cached_property
# Generic Like model for any post type
class GenericLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'content_type', 'object_id')
        indexes = [
            models.Index(fields=['content_type', 'object_id', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]

# Generic Comment model for any post type
class GenericComment(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    author = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies', db_index=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id', 'created_at']),
            models.Index(fields=['author', 'created_at']),
        ]

# Generic Share model for any post type
class GenericShare(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'content_type', 'object_id')
        indexes = [
            models.Index(fields=['content_type', 'object_id', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]


# Announcement model for global messages
class Announcement(models.Model):
    ANNOUNCEMENT_TYPES = [
        ('government', 'Government'),
        ('fellowship', 'Fellowship'),
    ]
    title = models.CharField(max_length=255)
    message = models.TextField()
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=ANNOUNCEMENT_TYPES)
    image = CloudinaryField('announcement_images', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.type})"

class Event(models.Model):
    title = models.CharField(max_length=200, db_index=True)
    description = models.TextField()
    location = models.CharField(max_length=200)
    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField()
    creator = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    attendees = models.ManyToManyField(User, related_name='attended_events', blank=True)
    cover_image = CloudinaryField('event_covers', blank=True, null=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True, 
                            related_name='events', db_index=True)
    registered_users = models.ManyToManyField(User, related_name='registered_events', blank=True)
    
    class Meta:
        ordering = ['start_time']
        indexes = [
            models.Index(fields=['start_time', 'end_time']),
            models.Index(fields=['group', 'start_time']),
        ]
    
    def __str__(self):
        return self.title

    def can_edit(self, user):
        return self.creator == user

    def can_delete(self, user):
        return self.creator == user

class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True, 
                            related_name='posts', db_index=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    image = CloudinaryField('post_images', blank=True, null=True)
    video = models.FileField(upload_to='post_videos/', blank=True, null=True)

    PRIVACY_CHOICES = [
        ('PUBLIC', 'Public'),
        ('FRIENDS', 'Friends Only'),
        ('PRIVATE', 'Private'),
    ]
    privacy = models.CharField(max_length=7, choices=PRIVACY_CHOICES, default='PUBLIC', db_index=True)
    repost_of = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, 
                                related_name='repost_children', db_index=True)
    
    is_welcome_post = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['author', 'created_at']),
            models.Index(fields=['group', 'created_at']),
            models.Index(fields=['privacy', 'created_at']),
            models.Index(fields=['is_welcome_post', 'created_at']),
        ]

    def __str__(self):
        return f"Post by {self.author.username}"

    @cached_property
    def get_original(self):
        return self.repost_of if self.repost_of else self

    @property
    def share_count(self):
        if hasattr(self, '_share_count'):
            return self._share_count
        original = self.get_original
        self._share_count = Share.objects.filter(post=original).count()
        return self._share_count

    @property
    def repost_count(self):
        if hasattr(self, '_repost_count'):
            return self._repost_count
        original = self.get_original
        self._repost_count = Post.objects.filter(repost_of=original).count()
        return self._repost_count

    def can_edit(self, user):
        return self.author == user

    def can_delete(self, user):
        return self.author == user

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('activities:post_detail', args=[str(self.id)])

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', db_index=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                             related_name='replies', db_index=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['author', 'created_at']),
        ]

    def __str__(self):
        return f"Comment by {self.author.username}"

    def can_edit(self, user):
        return self.author == user

    def can_delete(self, user):
        return self.author == user

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')
        indexes = [
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]

class Save(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='saves', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')
        indexes = [
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]

class Share(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='shares', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]

class Repost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reposts', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]