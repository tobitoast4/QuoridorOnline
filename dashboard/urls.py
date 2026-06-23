from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path("get_lobby/<lobby_id>", views.get_lobby),
]
