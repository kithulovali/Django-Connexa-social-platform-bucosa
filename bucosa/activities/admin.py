from django.contrib import admin
from . models import Event , Post , Comment , Announcement
from .models_feedback import Feedback
# Register your models here.
admin.site.register(Event)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Announcement)

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
	list_display = ("user", "created_at", "message")