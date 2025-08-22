import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

class PrivateMessageConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        
        # Log connection attempt
        logger.info(f"Private message WebSocket connection attempt for user: {user.id if not user.is_anonymous else 'anonymous'}")
        
        if user.is_anonymous:
            # Log rejection of anonymous user
            logger.warning("Private message WebSocket connection rejected for anonymous user")
            await self.close()
        else:
            self.user_id = user.id
            self.room_name = f"private_{self.user_id}"
            await self.channel_layer.group_add(self.room_name, self.channel_name)
            await self.accept()
            logger.info(f"Private message WebSocket connection accepted for user {self.user_id}")

    async def disconnect(self, close_code):
        if hasattr(self, 'room_name'):
            await self.channel_layer.group_discard(self.room_name, self.channel_name)
        logger.info(f"Private message WebSocket disconnected for user {getattr(self, 'user_id', 'unknown')}")

    async def receive(self, text_data):
        # Not expecting to receive data from client, but log any unexpected messages
        logger.warning(f"Unexpected message received from user {getattr(self, 'user_id', 'unknown')} in private messages: {text_data}")
        pass

    async def send_private_message(self, event):
        try:
            await self.send(text_data=json.dumps(event["message"]))
        except Exception as e:
            logger.error(f"Error sending private message to user {getattr(self, 'user_id', 'unknown')}: {str(e)}")
            # Don't re-raise the exception to avoid breaking the channel layer

class GroupMessageConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        group_id = self.scope['url_route']['kwargs']['group_id']
        
        # Log connection attempt
        logger.info(f"Group message WebSocket connection attempt for user: {user.id if not user.is_anonymous else 'anonymous'} in group {group_id}")
        
        self.room_group_name = f"group_{group_id}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        
        if user.is_anonymous:
            logger.warning(f"Group message WebSocket connected anonymously to group {group_id}")
        else:
            logger.info(f"Group message WebSocket connection accepted for user {user.id} in group {group_id}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        logger.info(f"Group message WebSocket disconnected for room {self.room_group_name}")

    async def receive(self, text_data):
        # Not expecting to receive data from client, but log any unexpected messages
        user = self.scope["user"]
        logger.warning(f"Unexpected message received in group {self.room_group_name} from user: {user.id if not user.is_anonymous else 'anonymous'}: {text_data}")
        pass

    async def send_group_message(self, event):
        try:
            await self.send(text_data=json.dumps(event["message"]))
        except Exception as e:
            logger.error(f"Error sending group message to room {self.room_group_name}: {str(e)}")
            # Don't re-raise the exception to avoid breaking the channel layer
