from django.db import models
from django.contrib.auth.models import User

class CurrentGovernment(models.Model):
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='government_images/')
    mission = models.TextField()
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.name

class GovernmentMember(models.Model):
    government = models.ForeignKey(CurrentGovernment, related_name='members', on_delete=models.CASCADE)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    ministry = models.CharField(max_length=255)
    contact = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.ministry}"

class PastGovernment(models.Model):
    name = models.CharField(max_length=255)
    mission = models.TextField()
    started_at = models.DateField()
    ended_at = models.DateField()
    image = models.ImageField(upload_to='government_images/', null=True, blank=True)

    def __str__(self):
        return self.name

class BucosaJoinRequest(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.status}"

class PastGovernmentMember(models.Model):
    government = models.ForeignKey(PastGovernment, related_name='members', on_delete=models.CASCADE)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    ministry = models.CharField(max_length=255)
    contact = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.ministry} (Past)"

