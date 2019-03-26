from django.conf				import settings
from django.conf.urls			import url
from django.conf.urls.static	import static
from django.urls				import path
from .							import views, api

urlpatterns = [
	path('', views.index, name = 'index'),
	path('battle-info/<str:monster>/', api.battle_info),
	url('player-info', api.player_info),
	url('players', api.players),
	url('rooms', api.rooms),
	url('send-command', api.send_command),
	path('walk-in-direction/<str:dir>/', api.walk_in_direction),
] + static(settings.STATIC_URL, document_root = settings.STATIC_ROOT)
