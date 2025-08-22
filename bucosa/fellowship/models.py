from django.db import models
from django.contrib.auth.models import User
from django.db import models
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField

class MembershipRequest(models.Model):
    fellowship = models.ForeignKey('fellowship_edit', on_delete=models.CASCADE, related_name='membership_requests')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='membership_requests')
    requested_at = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} requests to join {self.fellowship.name}"

# Create your models here.

class fellowship_edit(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField(max_length=254)
    profile = CloudinaryField('fellowship', null=True, blank=True)
    back_image = CloudinaryField('back_images', null=True, blank=True)
    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='admin_fellowships')
    
    def __str__(self):
        return self.name or "(no name)"

class FellowshipMember(models.Model):
    fellowship = models.ForeignKey(fellowship_edit, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fellowship_memberships')
    joined_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('fellowship', 'user')
    def __str__(self):
        return f"{self.user.username} in {self.fellowship.name}"

class FellowshipPost(models.Model):
    fellowship = models.ForeignKey(fellowship_edit, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    image = CloudinaryField('fellowship_post_images/', blank=True, null=True)
    video = models.FileField(upload_to='fellowship_post_videos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"Post by {self.author.username} in {self.fellowship.name}"

class FellowshipEvent(models.Model):
    fellowship = models.ForeignKey(fellowship_edit, on_delete=models.CASCADE, related_name='events')
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=200)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    cover_image = CloudinaryField('fellowship_event_covers', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.title} in {self.fellowship.name}"

class donation(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField(max_length=254)
    amount = models.DecimalField(max_digits=10, decimal_places=0)
    payment_method = models.CharField(max_length=50)
    mobile_money_number = models.CharField(max_length=13, blank=True, null=True)
    time_send = models.DateField(auto_now_add=True)
    def __str__(self):
        return self.name or "(no name)"


class Profile(models.Model):
#    profile_fellowship = models.CharField(max_length=150)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='fellowship_profile' ,blank =True , null =True)
    fellowship = models.OneToOneField(fellowship_edit, on_delete=models.CASCADE, related_name='fellowship_profile', null=True, blank=True)
    description = models.TextField()
    image = CloudinaryField('profile_image', null=True, blank=True)
    
    def __str__(self):
        return self.fellowship.name if self.fellowship and self.fellowship.name else "(no fellowship)"
