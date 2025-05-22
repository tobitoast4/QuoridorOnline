from django.shortcuts import render, redirect
from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib import messages
from web import models
from web import serialize
from web import utils, lobby_manager
from web.quoridor import game as quoridor_game
from web.quoridor import deserialize as quoridor_deserialize
import json


def home(request):
    return render(request, 'home.html')

def local(request):
    amount_players = request.args.get('amount_players', default=2, type=int)
    context = {"amount_players": amount_players}
    return render(request, 'game_local.html', context)

def how_to_play(request):
    return render(request, 'how_to_play.html')

def about(request):
    return render(request, 'about.html')

def privacy_policy(request):
    return render(request, 'privacy_policy.html')

def lobby(request, lobby_id=None):
    if lobby_id is None:
        # create new lobby
        game_player = models.GamePlayer.objects.create(game_user=request.user, color=request.user.color)
        new_lobby = models.Lobby.objects.create(created_by=request.user, owner=game_player)
        game_player.lobby = new_lobby
        game_player.save()
        return redirect(f"/lobby/{new_lobby.id}")
    else:
        # join lobby
        the_lobby = models.Lobby.objects.get(pk=lobby_id)
        if the_lobby is None:
            messages.add_message(request, messages.ERROR, f"The lobby with id {lobby_id} does not exist.")
            return redirect("/")
        context = {"lobby": the_lobby, "colors": utils.COLORS}
        return render(request, "lobby.html", context)

@api_view(['GET'])
def get_lobby(request, lobby_id=None):
    if lobby_id is None:
        messages.add_message(request, messages.ERROR, f"The lobby with id {lobby_id} does not exist.")
        return redirect("/")
    the_lobbys = models.Lobby.objects.filter(pk=lobby_id)
    if the_lobbys.count() == 1:
        the_lobby = the_lobbys.first()
        if the_lobby.game is None:  # game not started yet
            lobby_manager.add_player_to_lobby(the_lobby, request.user)
            lobby_manager.check_players_last_seen_time(the_lobby)
            serializer = serialize.LobbySerializer(the_lobby)
            return Response({"lobby": serializer.data}, 200)
        else:  # game started
            return Response({"lobby": {"game": f"game/{lobby_id}"}}, 200)  #  TODO: use redirect here
    else:
        messages.add_message(request, messages.ERROR, f"The lobby with id {lobby_id} does not exist.")
        return redirect("/")
    
@api_view(['POST'])
def start_game(request, lobby_id=None):
    the_lobby = models.Lobby.objects.get(pk=lobby_id)
    if request.user != the_lobby.owner.game_user:
        return Response({"error": "Only the lobby owner can start the game"}, 200)
    # TODO: Shuffle players
    next_lobby = models.Lobby.objects.create(created_by=the_lobby.created_by, owner=the_lobby.owner)
    new_game = quoridor_game.Game(the_lobby.gameplayer_set, the_lobby.amount_of_walls_per_player, next_lobby.id)
    the_lobby.game = json.dumps(new_game.game_data, cls=utils.UUIDEncoder)
    the_lobby.save()
    return Response({"status": "game started"}, 200)

def game(request, lobby_id=None):
    the_lobby = models.Lobby.objects.get(pk=lobby_id)
    context = {"user": request.user, "lobby": the_lobby}
    return render(request, "game_online.html", context)

@api_view(['GET'])
def get_game_data(request, lobby_id=None):
    the_lobby = models.Lobby.objects.get(pk=lobby_id)
    # if the_lobby is None:
    #     return {"error": f"The lobby with id {lobby_id} does not exist."}, 502
    return Response(json.loads(the_lobby.game), 200)

@api_view(['POST'])
def game_move_player(request, lobby_id=None):
    the_lobby = models.Lobby.objects.get(pk=lobby_id)
    the_game_json = json.loads(the_lobby.game)
    the_game = quoridor_deserialize.create_game_from_json(the_game_json)
    the_game.move_player(request.user.id,
                         request.data.get("new_field_col_num"),
                         request.data.get("new_field_row_num"))
    the_lobby.game = json.dumps(the_game.game_data, cls=utils.UUIDEncoder)
    the_lobby.save()
    return Response({"status": "player moved"}, 200)

@api_view(['POST'])
def game_place_wall(request, lobby_id=None):
    the_lobby = models.Lobby.objects.get(pk=lobby_id)
    the_game_json = json.loads(the_lobby.game)
    the_game = quoridor_deserialize.create_game_from_json(the_game_json)
    the_game.place_wall(request.user.id,
                        request.data.get("col_start"),
                        request.data.get("row_start"),
                        request.data.get("col_end"),
                        request.data.get("row_end"))
    the_lobby.game = json.dumps(the_game.game_data, cls=utils.UUIDEncoder)
    the_lobby.save()
    return Response({"status": "wall placed"}, 200)

@api_view(['POST'])
def change_lobby_visibility(request, lobby_id=None):
    the_lobby = lobby_manager.get_lobby(lobby_id)
    if session['user_id'] != the_lobby.lobby_owner.id:
        return {"error": "Only the lobby owner can change the visibility"}
    the_lobby.change_visibility()
    the_lobby.write_lobby()
    if the_lobby.is_private:
        return {"status": "Lobby visibility successfully changed to: private"}, 200
    else:
        return {"status": "Lobby visibility successfully changed to: public"}, 200
