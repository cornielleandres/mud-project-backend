from django.http				import JsonResponse
from decouple					import config
from django.contrib.auth.models	import User
from .models					import *
from rest_framework.decorators	import api_view
import json

@api_view(["GET"])
def rooms(request):
	# return a list of all the rooms
	rooms = Room.objects.all().values('name')
	rooms = [ r['name'] for r in rooms ]
	return JsonResponse({ 'rooms': rooms }, safe = True)

@api_view(["GET"])
def players(request):
	# return a list of all the other players
	player = request.user.player
	player_id = player.id
	current_players = player.get_all_players(player_id)
	return JsonResponse({ 'players': current_players }, safe = True)
