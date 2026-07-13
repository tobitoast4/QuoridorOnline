from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import authenticate, login as auth_login, logout
from django.http import HttpResponse, FileResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib import messages

import json

from web import models
from web import serialize
from web import utils, lobby_manager
from web.quoridor import game as quoridor_game
from web.quoridor import deserialize as quoridor_deserialize
from web.quoridor.artificial_player import move as ai_move
import dashboard.views
import logging

logger = logging.getLogger(__name__)


def login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('/')
        messages.error(request, 'Username or password wrong.')
        return render(request, 'login.html', {'username': username})
    return render(request, 'login.html')

def register(request):
    username = ""
    email = ""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        repeat_password = request.POST.get('repeat_password', '')
        current_user_pk = getattr(request.user, 'pk', None)

        if username == "":
            messages.error(request, 'Username cannot be empty.')
        elif email == "":
            messages.error(request, 'Email cannot be empty.')
        elif password == "":
            messages.error(request, 'Password cannot be empty.')
        elif password != repeat_password:
            messages.error(request, 'Passwords do not match.')
        elif models.GameUser.objects.filter(username=username).exclude(pk=current_user_pk).exists():
            messages.error(request, 'Username is already taken.')
        elif models.GameUser.objects.filter(email=email).exclude(pk=current_user_pk).exists():
            messages.error(request, 'Email is already taken.')
        else:
            user = request.user
            if getattr(user, 'is_guest', False):
                user.username = username
                user.email = email
                user.set_password(password)
                user.is_guest = False
                user.save()
                auth_login(request, user)
                messages.success(request, 'Registration successful.')
                return redirect('/')
            messages.error(request, 'Registration can only be completed for guest users.')

    return render(request, 'register.html', {'username': username})

def logout_user(request):
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect("/")

def home(request):
    return render(request, 'home.html')

def account(request):
    if not request.user.is_authenticated:
        return redirect('login')

    # Calculate games played and won (all time)
    try:
        games_played_count = models.GamePlayer.objects.filter(game_user=request.user, lobby__game__isnull=False).count()
        games_won_count = models.Lobby.objects.filter(game__isnull=False, winner__game_user=request.user).count()
    except Exception:
        games_played_count = 0
        games_won_count = 0

    # Collect recent games where the user participated (lobbies with a game)
    recent_games = []
    try:
        games_played = models.GamePlayer.objects.filter(game_user=request.user, lobby__game__isnull=False) \
                                       .select_related('lobby').order_by('-lobby__created_at')[:10]
        for gp in games_played:
            lobby = gp.lobby
            if lobby is None:
                continue
            recent_games.append({
                'name': f"Match {lobby.id}",
                'played_at': lobby.created_at,
                'winner': lobby.winner.game_user if lobby.winner else None,
                'url': f"/game/{lobby.id}"
            })
    except Exception:
        recent_games = []

    context = {
        'user': request.user,
        'recent_games': recent_games,
        'games_played': games_played_count,
        'games_won': games_won_count
    }
    return render(request, 'account.html', context)


def local(request):
    amount_players = int(request.GET.get("amount_players", 2))
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
        utils.send_email(f"New lobby created by {request.user.username}\n\nLobby ID: \nhttps://quoridoronline.com/lobby/{new_lobby.id}")
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
def get_random_lobby(request):
    the_lobby = lobby_manager.get_random_public_lobby()
    if the_lobby is None:
        # create new lobby with an AI player if no public lobby is available
        game_player = models.GamePlayer.objects.create(game_user=request.user, color=request.user.color)
        new_lobby = models.Lobby.objects.create(created_by=request.user, owner=game_player)
        utils.send_email(f"New lobby created by {request.user.username}\n\nLobby ID: \nhttps://quoridoronline.com/lobby/{new_lobby.id}")
        game_player.lobby = new_lobby
        game_player.save()
        lobby_manager.add_ai_player_to_lobby(new_lobby)
        lobby_manager.add_ai_player_to_lobby(new_lobby)
        return redirect(f"/lobby/{new_lobby.id}")
    return Response({"lobby_url": f"/lobby/{the_lobby.id}"}, 200)

def game(request, lobby_id=None):
    the_lobby = models.Lobby.objects.get(pk=lobby_id)
    context = {"user": request.user, "lobby": the_lobby}
    return render(request, "game_online.html", context)

@api_view(['GET'])
def get_game_data(request, lobby_id=None):
    if lobby_id is None:
        return Response({"error": "No lobby ID provided"}, 400)
    else:
        try:
            the_lobby = models.Lobby.objects.get(id=lobby_id)
        except models.Lobby.DoesNotExist:
            return Response({"error": "Lobby not found"}, 404)
        serializer = serialize.LobbySerializer(the_lobby)
        json_data = serializer.data
        return Response({"lobby": json_data}, 200)

@api_view(['POST'])
def rename_player(request):
    new_user_name = request.data.get("new_user_name")
    if new_user_name == "":
        raise ValueError("User name can not be empty")
    if len(new_user_name) > 64:
        raise ValueError("User name is too long")
    # TODO: XSS Check  # TODO player name unique
    request.user.username = new_user_name
    request.user.save()
    return Response({"status": f"Player name successfully changed to {new_user_name}"}, 200)

@api_view(['POST'])
def change_color(request):
    lobby_id = request.data.get("lobby_id")
    new_color = request.data.get("new_color")
    gameplayer = request.user.gameplayer_set.filter(lobby__id=lobby_id).first()
    # TODO: XSS Check
    gameplayer.color = new_color
    gameplayer.save()
    request.user.color = new_color
    request.user.save()
    return Response({
        "status": f"Color successfully updated",
        "color": new_color
    }, 200)


def ads_txt(request):
    return FileResponse(
        open("web/static/ads.txt", "rb"),
        content_type="text/plain"
    )


# @api_view(['POST'])
# def calculate_ai(request):
#     lobby_id = request.data.get("lobby_id")
#     the_lobby = models.Lobby.objects.get(id=lobby_id)
#     the_game_json = json.loads(the_lobby.game)
#     the_game = quoridor_deserialize.create_game_from_json(the_game_json)
#     move_generator = ai_move.MoveSimulator(the_lobby, the_game, depth=2, wall_range=5)
#     logger.info("START")
#     new_game = move_generator.play()
#     logger.info("END")
#     the_lobby.game = json.dumps(new_game.game_data, cls=utils.UUIDEncoder)
#     the_lobby.save()
    
#     return Response({"status": "done"}, 200)
