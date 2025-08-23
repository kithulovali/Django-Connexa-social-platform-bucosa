import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        
        # Log connection attempt with more details
        session_key = self.scope.get('session', {}).get('session_key', 'unknown') if self.scope.get('session') else 'no-session'
        logger.info(f"WebSocket connection attempt for user: {user.id if not user.is_anonymous else 'anonymous'}, session: {session_key}")
        
        if user.is_anonymous:
            # Log rejection of anonymous user with more details
            logger.warning(f"WebSocket connection rejected for anonymous user. Session key: {session_key}")
            await self.close(code=4001)  # Custom close code for anonymous user
        else:
            self.user_id = user.id
            self.group_name = f"notifications_{self.user_id}"
            
            # Add to group
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            
            # Accept connection
            await self.accept()
            
            logger.info(f"WebSocket connection accepted for user {self.user_id}")

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.info(f"WebSocket disconnected for user {getattr(self, 'user_id', 'unknown')} with close code {close_code}")

    async def receive(self, text_data):
        # Not expecting to receive data from client, but log any unexpected messages
        logger.warning(f"Unexpected message received from user {getattr(self, 'user_id', 'unknown')}: {text_data}")
        pass

    async def send_notification(self, event):
        try:
            await self.send(text_data=json.dumps(event["notification"]))
        except Exception as e:
            logger.error(f"Error sending notification to user {getattr(self, 'user_id', 'unknown')}: {str(e)}")
            # Don't re-raise the exception to avoid breaking the channel layer
