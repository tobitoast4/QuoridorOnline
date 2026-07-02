"""
URL routing for WebSocket connections.
"""

from django.urls import path, re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/game/(?P<lobby_id>[^/]+)/?$', consumers.GameConsumer.as_asgi()),
]
