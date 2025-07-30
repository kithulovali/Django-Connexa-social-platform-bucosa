import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

from channels.auth import AuthMiddlewareStack
import notifications.routing
import users.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bucosa.settings')

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            notifications.routing.websocket_urlpatterns +
            users.routing.websocket_urlpatterns
        )
    ),
})
