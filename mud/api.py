from django.http				import JsonResponse
from decouple					import config
from django.contrib.auth.models	import User
from .models					import *
from rest_framework.decorators	import api_view
import json

@api_view(['GET'])
def player_info(request):
	# return player info
	player = request.user.player
	player_info = player.get_player_info()
	return JsonResponse(player_info)

@api_view(['GET'])
def players(request):
	# return a list of all the other players
	player = request.user.player
	player_id = player.id
	current_players = player.get_all_players(player_id)
	return JsonResponse({ 'players': current_players }, safe = True)

@api_view(['GET'])
def rooms(request):
	# return a list of all the rooms
	rooms = Room.objects.all().values('name')
	rooms = [ r['name'] for r in rooms ]
	return JsonResponse({ 'rooms': rooms }, safe = True)

@api_view(['POST'])
def walk_in_direction(request, dir):
	# walk in given direction
	player = request.user.player
	current_room = player.get_room()
	if dir == 'N':
		dir = 'north'
		next_room_id = current_room.n_to
	if dir == 'W':
		dir = 'west'
		next_room_id = current_room.w_to
	if dir == 'E':
		dir = 'east'
		next_room_id = current_room.e_to
	if dir == 'S':
		dir = 'south'
		next_room_id = current_room.s_to
	player.current_room_id = next_room_id
	new_room_info = player.get_room_info()
	player.save()
	return JsonResponse({
		'adventureHistory': [ 'You walked %s.' % dir ],
		'currentRoom': new_room_info
	})
