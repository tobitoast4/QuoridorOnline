import logging

from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Count
from django.db.models.functions import TruncDate
from datetime import datetime, timedelta

from web import models, serialize
from web import utils

logger = logging.getLogger(__name__)

def parse_date_filter(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return None


@user_passes_test(lambda u: u.is_superuser)
def dashboard(request):
    date_from = parse_date_filter(request.GET.get('date_from'))
    date_to = parse_date_filter(request.GET.get('date_to'))

    lobbies_queryset = models.Lobby.objects.all()
    if date_from:
        lobbies_queryset = lobbies_queryset.filter(created_at__date__gte=date_from)
    if date_to:
        lobbies_queryset = lobbies_queryset.filter(created_at__date__lte=date_to)

    lobbies = []
    for lobby in lobbies_queryset.order_by('-created_at').iterator():
        lobbies.append({
            "lobby_id": lobby.id,
            "time_created": lobby.created_at,
            "amount_players": lobby.gameplayer_set.count() if lobby.game != None else "NaN",
            "game": True if lobby.game else None
        })

    first_lobby = lobbies_queryset.order_by('created_at').first()
    first_lobby_date = first_lobby.created_at if first_lobby else None

    lobbies_per_day_query = lobbies_queryset.annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')

    lobbies_count_dict = {
        item['date']: item['count']
        for item in lobbies_per_day_query
    }

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
        "lobbies_count_per_day": lobbies_count_per_day,
        "date_from": date_from,
        "date_to": date_to,
        "online_user_count": utils.get_online_user_count(),
    }
    return render(request, 'dashboard.html', context)


@user_passes_test(lambda u: u.is_superuser)
@api_view(['DELETE'])
def delete_empty_lobbies(request):
    lobbies_to_delete = models.Lobby.objects.filter(game__isnull=True).exclude(game="")
    deleted_count = lobbies_to_delete.count()
    lobbies_to_delete.delete()
    logger.info(f"Deleted {deleted_count} empty lobbies.")
    return Response({"deleted": deleted_count}, 200)

