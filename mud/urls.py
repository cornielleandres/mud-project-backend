from django.conf				import settings
from django.conf.urls			import url
from django.conf.urls.static	import static
from django.urls				import path
from .							import views, api

urlpatterns = [
	path('', views.index, name = 'index'),
	url('attack-monster/', api.attack_monster),
	path('battle-info/<str:monster_name>/', api.battle_info),
	url('monster-attacks', api.monster_attacks),
	url('player-info', api.player_info),
	url('players', api.players),
	url('restart-game', api.restart_game),
	url('rooms', api.rooms),
	url('send-command', api.send_command),
	path('walk-in-direction/<str:dir>/', api.walk_in_direction),
] + static(settings.STATIC_URL, document_root = settings.STATIC_ROOT)
