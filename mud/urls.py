from django.conf.urls	import url
from django.urls		import path
from .					import views, api

urlpatterns = [
	path('', views.index, name = 'index'),
	url('player-info', api.player_info),
	url('players', api.players),
	url('rooms', api.rooms),
	url('send-command', api.send_command),
	path('walk-in-direction/<str:dir>/', api.walk_in_direction),
]
