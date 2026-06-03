from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import authenticate, login as auth_login, logout
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

@api_view(['GET'])
def get_random_lobby(request):
    the_lobby = lobby_manager.get_random_public_lobby()
    if the_lobby is None:
        return Response({"error": "Could not find any public lobby :(<br/>Try again later or create your own one"}, 200)
    return Response({"lobby_url": f"/lobby/{the_lobby.id}"}, 200)
    
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
    the_lobby = models.Lobby.objects.get(id=lobby_id)
    the_lobby.toggle_visibility()
    if the_lobby.is_private:
        return Response({"status": "Lobby visibility successfully changed to: private"}, 200)
    else:
        return Response({"status": "Lobby visibility successfully changed to: public"}, 200)

@api_view(['POST'])
def change_amount_of_walls_per_player(request, lobby_id=None):
    the_lobby = models.Lobby.objects.get(id=lobby_id)
    if request.user.id != the_lobby.owner.game_user.id:
        raise PermissionError("Only the lobby owner can change the amount of walls per player")
    if the_lobby.game is not None:
        raise PermissionError("You can not change the amount of walls per player when the game is already running")
    new_amount = request.data.get("new_amount")
    the_lobby.change_amount_of_walls_of_players(new_amount)
    return Response({
        "status": "ok",
        "amount_of_walls_per_player": new_amount
    }, 200)

@api_view(['POST'])
def rename_player(request):
    new_user_name = request.data.get("new_user_name")
    if new_user_name == "":
        raise ValueError("User name can not be empty")
    if len(new_user_name) > 64:
        raise ValueError("User name is too long")
    # TODO: XSS Check
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


@user_passes_test(lambda u: u.is_superuser)
def dashboard(request):
    data = []
    for lobby in models.Lobby.objects.order_by('-created_at').iterator():
        data.append({
            "lobby_id": lobby.id,
            "time_created": lobby.created_at,
            "amount_players": lobby.gameplayer_set.count()
        })

    context = {"lobbies": data}
    return render(request, 'dashboard.html', context)