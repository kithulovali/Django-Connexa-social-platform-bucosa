from django.contrib import admin
from . models import Event , Post , Comment
# Register your models here.
admin.site.register(Event)
admin.site.register(Post)
admin.site.register(Comment)