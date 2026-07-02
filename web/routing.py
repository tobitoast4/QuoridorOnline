"""
URL routing for WebSocket connections.
"""

from django.urls import path, re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/lobby/(?P<lobby_id>[^/]+)/?$', consumers.LobbyConsumer.as_asgi()),
    re_path(r'ws/game/(?P<lobby_id>[^/]+)/?$', consumers.GameConsumer.as_asgi()),
]
