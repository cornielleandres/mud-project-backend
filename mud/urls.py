from django.conf.urls	import url
from django.urls		import path
from .					import views, api

urlpatterns = [
	path('', views.index, name = 'index'),
	url('player-info', api.player_info),
	url('players', api.players),
	url('rooms', api.rooms),
]
