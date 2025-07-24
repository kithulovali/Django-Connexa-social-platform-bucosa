from django.contrib import admin
from django.urls import path , include
from django.conf import settings
from django.conf.urls.static import static
import os
from django.conf import settings
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('users.urls')),
    path('fellowship/',include('fellowship.urls')),
    path('government/', include('government.urls')),
    path('activities/', include(('activities.urls', 'activities'), namespace='activities')),
    path('accounts/', include('allauth.urls')),  # Add allauth URLs for social login
    path('pwa/', include('pwa.urls')),  # Enable django-pwa URLs for manifest and service worker
    path('notifications/', include('notifications.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
