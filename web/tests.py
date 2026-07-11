import uuid

from django.test import SimpleTestCase, TestCase
from django.urls import resolve

from web import models
from web.quoridor.game import Game
from web.quoridor.wall import is_wall_within_board
from web.views import lobby


class UrlRoutingTests(SimpleTestCase):
    def test_lobby_route_matches_with_trailing_slash(self):
        match = resolve("/lobby/")
        self.assertEqual(match.func, lobby)


class GameWallHelperTests(SimpleTestCase):
    def test_wall_outside_board_is_rejected(self):
        # col_start, row_start, col_end, row_end
        self.assertTrue(is_wall_within_board(0, 0.5, 1, 0.5, 9))
        self.assertTrue(is_wall_within_board(5, 0.5, 6, 0.5, 9))
        self.assertFalse(is_wall_within_board(-1, 0.5, 0, 0.5, 9))


# class LobbyCreationTests(TestCase):
#     def test_create_lobby_from_json(self):
#         payload = {
#             "amount_of_walls_per_player": 10,
#             "game": {"state": "new"},
#             "is_private": True,
#             "lobby_id": "b44542f6-5699-44cb-bf6b-5d00acad2e2b",
#             "lobby_owner": {
#                 "color": "#FFE600",
#                 "id": "e0d7ec11-2e18-44ff-97ec-2baf7ebb18c4",
#                 "name": "Guest-4df0cc"
#             },
#             "players": [],
#             "players_last_seen": [],
#             "time_created": 1782452233.0766542,
#         }

#         lobby = create_lobby_from_json(payload)

#         self.assertEqual(lobby.id, uuid.UUID(payload["lobby_id"]))
#         self.assertEqual(lobby.amount_of_walls_per_player, 10)
#         self.assertTrue(lobby.is_private)
#         self.assertEqual(lobby.owner.game_user.username, "Guest-4df0cc")
#         self.assertEqual(lobby.owner.color, "#FFE600")
#         self.assertEqual(lobby.created_by, lobby.owner.game_user)
#         self.assertEqual(lobby.game, '{"state": "new"}')
#         self.assertTrue(models.GamePlayer.objects.filter(lobby=lobby).exists())

#     def test_create_lobby_from_json_with_players(self):
#         payload = {
#             "amount_of_walls_per_player": 10,
#             "game": {"state": "new"},
#             "is_private": True,
#             "lobby_id": "a34fea34-8ce1-47d8-9103-bb99b5e48f4d",
#             "lobby_owner": {
#                 "color": "#199A19",
#                 "id": "619c4a4d-fe2f-4268-bcaf-4c396660ef46",
#                 "name": "Guest-7ac5d9"
#             },
#             "players": [
#                 {"color": "#199A19", "id": "619c4a4d-fe2f-4268-bcaf-4c396660ef46", "name": "Angira"},
#                 {"color": "#FFE600", "id": "e0d7ec11-2e18-44ff-97ec-2baf7ebb18c4", "name": "Guest-4df0cc"}
#             ],
#             "players_last_seen": [1782453616.00272, 1782453615.9104764],
#             "time_created": 1782452885.6549802,
#         }

#         lobby = create_lobby_from_json(payload)

#         self.assertEqual(lobby.id, uuid.UUID(payload["lobby_id"]))
#         self.assertEqual(lobby.amount_of_walls_per_player, 10)
#         self.assertTrue(lobby.is_private)
#         self.assertEqual(lobby.owner.game_user.id, uuid.UUID(payload["lobby_owner"]["id"]))
#         self.assertEqual(lobby.owner.game_user.username, "Angira")
#         self.assertEqual(lobby.owner.color, "#199A19")
#         self.assertEqual(models.GamePlayer.objects.filter(lobby=lobby).count(), 2)
#         self.assertEqual(lobby.created_by.id, uuid.UUID(payload["lobby_owner"]["id"]))
#         self.assertEqual(lobby.game, '{"state": "new"}')
