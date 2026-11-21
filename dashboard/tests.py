from django.test import TestCase
from django.urls import reverse

from web import models


class DashboardLobbyApiTests(TestCase):
    def setUp(self):
        self.admin = models.GameUser.objects.create_superuser(
            username="dashboard-admin",
            email="admin@example.com",
            password="secret",
        )
        self.client.force_login(self.admin)

    def create_lobby(self, game='{"state": "started"}', players=0, ai_players=0):
        lobby = models.Lobby.objects.create(game=game)
        for index in range(players):
            models.GamePlayer.objects.create(
                lobby=lobby,
                is_artificial=index < ai_players,
            )
        return lobby

    def test_dashboard_renders_new_lazy_loading_interface(self):
        self.create_lobby()
        self.create_lobby(game=None)
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="lobbyTableBody"')
        self.assertContains(response, 'id="lineChart"')
        self.assertContains(response, 'id="statusChart"')
        self.assertNotContains(response, 'id="lobbies"')
        chart_data = response.context["lobbies_count_per_day"]
        self.assertEqual(sum(chart_data["started"]), 1)
        self.assertEqual(sum(chart_data["empty"]), 1)

    def test_lobbies_are_paginated(self):
        for _ in range(12):
            self.create_lobby()

        response = self.client.get(reverse("lobbies"), {"page_size": 10})
        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(payload["results"]), 10)
        self.assertEqual(payload["total"], 12)
        self.assertTrue(payload["has_more"])

    def test_lobbies_can_be_sorted_by_player_count(self):
        small = self.create_lobby(players=1)
        large = self.create_lobby(players=3, ai_players=2)

        response = self.client.get(reverse("lobbies"), {
            "sort": "players",
            "direction": "desc",
        })

        self.assertEqual(response.json()["results"][0]["lobby_id"], str(large.id))
        self.assertEqual(response.json()["results"][0]["amount_ai_players"], 2)
        self.assertNotEqual(small.id, large.id)

    def test_status_filter_returns_only_started_games(self):
        started = self.create_lobby()
        self.create_lobby(game=None)
        self.create_lobby(game="")

        response = self.client.get(reverse("lobbies"), {"status": "started"})
        payload = response.json()

        self.assertEqual(payload["total"], 1)
        self.assertEqual(payload["results"][0]["lobby_id"], str(started.id))

    def test_lobby_api_requires_superuser(self):
        self.client.logout()
        response = self.client.get(reverse("lobbies"))
        self.assertEqual(response.status_code, 302)

    def test_clear_empty_lobbies_keeps_started_games(self):
        started = self.create_lobby()
        self.create_lobby(game=None)
        self.create_lobby(game="")

        response = self.client.delete(reverse("delete_empty_lobbies"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["deleted"], 2)
        self.assertEqual(list(models.Lobby.objects.values_list("id", flat=True)), [started.id])
