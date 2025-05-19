from django.shortcuts import render, redirect
from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib import messages
from web import models
from web import serialize
from web import utils, lobby_manager


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
        new_lobby = models.Lobby.objects.create(created_by=game_player, owner=game_player)
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
            return Response({"game": f"{request.url_root}game/{lobby_id}"}, 200)
    else:
        messages.add_message(request, messages.ERROR, f"The lobby with id {lobby_id} does not exist.")
        return redirect("/")