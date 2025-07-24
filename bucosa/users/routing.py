from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/messages/private/$', consumers.PrivateMessageConsumer.as_asgi()),
    re_path(r'ws/messages/group/(?P<group_id>\d+)/$', consumers.GroupMessageConsumer.as_asgi()),
]
