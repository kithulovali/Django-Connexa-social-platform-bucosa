from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve as static_serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('users.urls')),
    path('fellowship/', include('fellowship.urls')),
    path('government/', include('government.urls')),
    path('activities/', include(('activities.urls', 'activities'), namespace='activities')),
    path('accounts/', include('allauth.urls')),
    path('pwa/', include('pwa.urls')),
    path('notifications/', include(('notifications.urls', 'notifications'), namespace='notifications')),

]

urlpatterns += [
    path('firebase-messaging-sw.js', static_serve, {
        'path': 'firebase-messaging-sw.js',
        'document_root': settings.STATIC_ROOT,
    }),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
