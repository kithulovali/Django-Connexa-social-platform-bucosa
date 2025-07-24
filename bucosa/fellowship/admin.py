from django.contrib import admin
from .models import fellowship_edit, donation, FellowshipMember, FellowshipPost, FellowshipEvent

admin.site.register(fellowship_edit)
admin.site.register(donation)
admin.site.register(FellowshipMember)
admin.site.register(FellowshipPost)
admin.site.register(FellowshipEvent)
