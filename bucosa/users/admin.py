from django.contrib import admin
from . models import user_profile ,GroupProfile
from . models_push_subscription import PushSubscription
from .models_staff_message import staff_messages
# Register your models here.
admin.site.register(user_profile)
admin.site.register(GroupProfile)
admin.site.register(PushSubscription)
admin.site.register(staff_messages)