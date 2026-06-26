from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Count
from django.db.models.functions import TruncDate
from datetime import datetime, timedelta

from web import models
from dashboard import serialize


@user_passes_test(lambda u: u.is_superuser)
def dashboard(request):
    lobbies = []
    for lobby in models.Lobby.objects.order_by('-created_at').iterator():
        lobbies.append({
            "lobby_id": lobby.id,
            "time_created": lobby.created_at,
            "amount_players": lobby.gameplayer_set.count(),
            "amount_of_walls_per_player": lobby.amount_of_walls_per_player
        })
    
    first_lobby = models.Lobby.objects.order_by('created_at').first()
    last_lobby = models.Lobby.objects.order_by('-created_at').first()
    
    first_lobby_date = first_lobby.created_at if first_lobby else None
    last_lobby_date = last_lobby.created_at if last_lobby else None
    
    # Lobbies pro Tag zählen
    lobbies_per_day_query = models.Lobby.objects.annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    # Dict mit Counts erstellen
    lobbies_count_dict = {
        item['date']: item['count']
        for item in lobbies_per_day_query
    }
    
    # Alle Tage zwischen erstem und letztem Lobby generieren
    lobbies_count_per_day = {
        "labels": [],
        "data": []
    }
    if first_lobby_date:
        current_date = first_lobby_date.date()
        end_date = datetime.today().date()
        
        while current_date <= end_date:
            count = lobbies_count_dict.get(current_date, 0)
            lobbies_count_per_day["labels"].append(current_date.strftime('%Y-%m-%d'))
            lobbies_count_per_day["data"].append(count)
            current_date += timedelta(days=1)

    context = {
        "lobbies": lobbies,
        "lobbies_count_per_day": lobbies_count_per_day
    }
    return render(request, 'dashboard.html', context)

@user_passes_test(lambda u: u.is_superuser) # TODO !!
@api_view(['GET'])
def get_lobby(request, lobby_id=None):
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
