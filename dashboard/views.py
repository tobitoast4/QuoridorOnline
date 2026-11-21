from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Case, Count, IntegerField, Q, Value, When
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.views.decorators.http import require_GET
from datetime import datetime, timedelta

from web import models
from web import utils


def parse_date_filter(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return None


def filtered_lobbies(request):
    queryset = models.Lobby.objects.all()
    date_from = parse_date_filter(request.GET.get('date_from'))
    date_to = parse_date_filter(request.GET.get('date_to'))

    if date_from:
        queryset = queryset.filter(created_at__date__gte=date_from)
    if date_to:
        queryset = queryset.filter(created_at__date__lte=date_to)

    return queryset, date_from, date_to


@user_passes_test(lambda u: u.is_superuser)
def dashboard(request):
    lobbies_queryset, date_from, date_to = filtered_lobbies(request)

    lobbies_per_day = list(lobbies_queryset.annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('id'),
        started=Count('id', filter=Q(game__isnull=False) & ~Q(game="")),
        empty=Count('id', filter=Q(game__isnull=True) | Q(game="")),
    ).order_by('date'))

    start_date = date_from or (lobbies_per_day[0]['date'] if lobbies_per_day else None)
    end_date = date_to or timezone.localdate()

    lobbies_count_dict = {
        item['date']: item
        for item in lobbies_per_day
    }

    lobbies_count_per_day = {
        "labels": [],
        "data": [],
        "started": [],
        "empty": [],
    }
    if start_date and start_date <= end_date:
        current_date = start_date
        while current_date <= end_date:
            daily_counts = lobbies_count_dict.get(current_date, {})
            lobbies_count_per_day["labels"].append(current_date.strftime('%Y-%m-%d'))
            lobbies_count_per_day["data"].append(daily_counts.get('count', 0))
            lobbies_count_per_day["started"].append(daily_counts.get('started', 0))
            lobbies_count_per_day["empty"].append(daily_counts.get('empty', 0))
            current_date += timedelta(days=1)

    metrics = lobbies_queryset.aggregate(
        total=Count('id'),
        games=Count('id', filter=Q(game__isnull=False) & ~Q(game="")),
        empty=Count('id', filter=Q(game__isnull=True) | Q(game="")),
    )

    context = {
        "lobbies_count_per_day": lobbies_count_per_day,
        "date_from": date_from,
        "date_to": date_to,
        "online_user_count": utils.get_online_user_count(),
        "lobbies_count": metrics['total'],
        "games_count": metrics['games'],
        "empty_lobbies_count": metrics['empty'],
    }
    return render(request, 'dashboard.html', context)


@user_passes_test(lambda u: u.is_superuser)
@require_GET
def lobbies(request):
    queryset, _, _ = filtered_lobbies(request)
    queryset = queryset.annotate(
        player_count=Count('gameplayer', distinct=True),
        ai_count=Count('gameplayer', filter=Q(gameplayer__is_artificial=True), distinct=True),
        has_game=Case(
            When(Q(game__isnull=True) | Q(game=""), then=Value(0)),
            default=Value(1),
            output_field=IntegerField(),
        ),
    )

    status = request.GET.get('status')
    if status == 'started':
        queryset = queryset.filter(has_game=1)
    elif status == 'empty':
        queryset = queryset.filter(has_game=0)

    sort_fields = {
        'lobby_id': 'id',
        'created_at': 'created_at',
        'players': 'player_count',
        'ai_players': 'ai_count',
        'status': 'has_game',
    }
    sort = request.GET.get('sort', 'created_at')
    direction = request.GET.get('direction', 'desc')
    order_field = sort_fields.get(sort, 'created_at')
    if direction == 'desc':
        order_field = f'-{order_field}'
    queryset = queryset.order_by(order_field, '-created_at')

    try:
        page = max(int(request.GET.get('page', 1)), 1)
        page_size = min(max(int(request.GET.get('page_size', 30)), 10), 100)
    except (TypeError, ValueError):
        page, page_size = 1, 30

    total = queryset.count()
    start = (page - 1) * page_size
    page_items = queryset[start:start + page_size]
    results = [{
        'lobby_id': str(lobby.id),
        'time_created': lobby.created_at.isoformat(),
        'amount_players': lobby.player_count if lobby.has_game else None,
        'amount_ai_players': lobby.ai_count if lobby.has_game else None,
        'game': bool(lobby.has_game),
    } for lobby in page_items]

    return JsonResponse({
        'results': results,
        'page': page,
        'page_size': page_size,
        'total': total,
        'has_more': start + len(results) < total,
    })


@user_passes_test(lambda u: u.is_superuser)
@api_view(['DELETE'])
def delete_empty_lobbies(request):
    lobbies_to_delete = models.Lobby.objects.filter(Q(game__isnull=True) | Q(game=""))
    deleted_count = lobbies_to_delete.count()
    lobbies_to_delete.delete()
    return Response({"deleted": deleted_count}, 200)

