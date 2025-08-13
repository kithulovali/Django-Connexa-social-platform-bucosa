from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import re_path
from notifications.consumers import NotificationConsumer

application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(
        URLRouter([
            re_path(r"ws/notifications/$", NotificationConsumer.as_asgi()),
            re_path(r"ws/notifications/(?P<user_id>\d+)/", NotificationConsumer.as_asgi()),
        ])
    ),
})