import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from apps.audit.services import log_event
from apps.live.models import LiveScreenSession, LiveScreenAccessEvent


class LiveScreenConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope["url_route"]["kwargs"]["session_id"]
        self.group_name = f"live_{self.session_id}"
        user = self.scope.get("user")
        allowed = await self._is_allowed(user)
        if not allowed:
            await self.close(code=4403)
            return
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self._log_event(user, "viewer_connected", {"session_id": self.session_id})

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        user = self.scope.get("user")
        await self._log_event(user, "viewer_disconnected", {"close_code": close_code})

    async def receive(self, text_data=None, bytes_data=None):
        payload = json.loads(text_data or "{}")
        await self.channel_layer.group_send(self.group_name, {"type": "live.signal", "payload": payload})

    async def live_signal(self, event):
        await self.send(text_data=json.dumps(event["payload"]))

    @database_sync_to_async
    def _is_allowed(self, user):
        if not user or not user.is_authenticated:
            return False
        return user.is_superuser or user.groups.filter(name="super_admin").exists()

    @database_sync_to_async
    def _log_event(self, user, event_type: str, payload: dict):
        session = LiveScreenSession.objects.filter(pk=self.session_id).first()
        if session:
            LiveScreenAccessEvent.objects.create(session=session, actor=user if user and user.is_authenticated else None, event_type=event_type, payload=payload)
            log_event(user=user if user and user.is_authenticated else None, action_type=f"live_screen_{event_type}", target_object=str(session.id), metadata=payload)
