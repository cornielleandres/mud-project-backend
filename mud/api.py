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
def send_command(request):
	# process a command given by a player
	body_unicode = request.body.decode('utf-8')
	body = json.loads(body_unicode)
	command = body['command']
	player = request.user.player
	command_response = player.process_command(command)
	return JsonResponse(command_response)

@api_view(['POST'])
def walk_in_direction(request, dir):
	# walk in given direction
	player = request.user.player
	walk_response = player.walk_in_direction(dir)
	return JsonResponse(walk_response)
