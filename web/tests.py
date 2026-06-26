from django.test import SimpleTestCase
from django.urls import resolve

from web.views import lobby


class UrlRoutingTests(SimpleTestCase):
    def test_lobby_route_matches_with_trailing_slash(self):
        match = resolve("/lobby/")
        self.assertEqual(match.func, lobby)
