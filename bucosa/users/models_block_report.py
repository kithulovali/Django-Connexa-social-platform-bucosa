from django.db import models
from django.contrib.auth.models import User

class UserBlock(models.Model):
    blocker = models.ForeignKey(User, related_name='blocks_initiated', on_delete=models.CASCADE)
    blocked = models.ForeignKey(User, related_name='blocks_received', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('blocker', 'blocked')
    def __str__(self):
        return f"{self.blocker.username} blocked {self.blocked.username}"

class UserReport(models.Model):
    reporter = models.ForeignKey(User, related_name='reports_made', on_delete=models.CASCADE)
    reported = models.ForeignKey(User, related_name='reports_received', on_delete=models.CASCADE)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.reporter.username} reported {self.reported.username}"
