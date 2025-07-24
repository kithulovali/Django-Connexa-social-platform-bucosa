from django.contrib import admin
from . models import user_profile
from . models_push_subscription import PushSubscription
# Register your models here.
admin.site.register(user_profile)
admin.site.register(PushSubscription)