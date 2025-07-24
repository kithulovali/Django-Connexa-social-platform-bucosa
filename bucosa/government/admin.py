from django.contrib import admin
from .models import CurrentGovernment, GovernmentMember, PastGovernment

@admin.register(CurrentGovernment)
class CurrentGovernmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)

@admin.register(GovernmentMember)
class GovernmentMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'government', 'ministry', 'contact')
    search_fields = ('user__username', 'ministry', 'contact')
    list_filter = ('government',)

@admin.register(PastGovernment)
class PastGovernmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'started_at', 'ended_at')
    search_fields = ('name',)
    list_filter = ('started_at', 'ended_at')

# Register your models here.
