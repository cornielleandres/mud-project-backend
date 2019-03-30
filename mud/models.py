from decouple							import config
from django.db							import models
from django.contrib.auth.models			import User
from django.db.models.signals			import post_save
from django.dispatch					import receiver
from rest_framework.authtoken.models	import Token
from rest_framework.exceptions			import NotFound, ParseError
import pusher
import uuid

pusher_client = pusher.Pusher(
	app_id = config('PUSHER_APP_ID'),
	key = config('PUSHER_KEY'),
	secret = config('PUSHER_SECRET'),
	cluster = config('PUSHER_CLUSTER'),
	ssl = True
)

class Room(models.Model):
	name = models.CharField(max_length = 32, default = 'default room name')
	description = models.CharField(max_length = 512, default = 'default room description')
	n_to = models.IntegerField(default = 0)
	s_to = models.IntegerField(default = 0)
	e_to = models.IntegerField(default = 0)
	w_to = models.IntegerField(default = 0)
	def get_all_rooms(self):
		return Room.objects.all()
	def get_valid_directions(self):
		valid_directions = {}
		if self.n_to != 0:
			valid_directions.update({ 'N': self.n_to })
		if self.w_to != 0:
			valid_directions.update({ 'W': self.w_to })
		if self.e_to != 0:
			valid_directions.update({ 'E': self.e_to })
		if self.s_to != 0:
			valid_directions.update({ 'S': self.s_to })
		return valid_directions
	def get_room_info(self, inventory_item_ids):
		# if lantern is not in inventory and player is past room 2, limit room info shown
		if 1 not in inventory_item_ids and self.id > 2: # lantern item id is 1
			current_room_info = {
				'name': self.name,
				'description': 'This room is pitch black. Is there something that can be used to illuminate it?',
				'items': [],
			}
		else:
			item_objects = Item.objects.filter(room = self.id).exclude(id__in = inventory_item_ids)
			items = [ { 'name': item.name, 'description': item.description } for item in item_objects ]
			current_room_info = {
				'id': self.id,
				'name': self.name,
				'description': self.description,
				'items': items,
			}
		return current_room_info
	def __str__(self):
		return self.name

class Player(models.Model):
	user = models.OneToOneField(User, on_delete = models.CASCADE)
	uuid = models.UUIDField(default = uuid.uuid4, unique = True)
	current_room_id = models.IntegerField(default = 1)
	max_hp = models.IntegerField(default = 100)
	def get_all_player_uuids(self):
		return [ p.uuid for p in Player.objects.all() ]
	def get_battle_info(self, monster_name):
		try:
			monster = Monster.objects.get(name = monster_name)
		except Monster.DoesNotExist:
			raise NotFound(detail = 'That monster does not exist.')
		else:
			try:
				battle = Battle.objects.get(player = self.id, monster = monster.id)
			except Battle.DoesNotExist:
				battle = Battle.objects.create(
					player = self,
					monster = monster,
					player_hp = self.max_hp,
					monster_hp = monster.max_hp
				)
			monster_battle_info = {
				'name': monster.name,
				'maxHp': monster.max_hp,
				'hp': battle.monster_hp,
				'imgExtension': monster.img_extension
			}
			player_battle_info = {
				'maxHp': self.max_hp,
				'hp': battle.player_hp
			}
			if battle.player_hp == 0:
				game_over = monster.name
			elif battle.monster_hp == 0:
				game_over = True
			else:
				game_over = False
			return {
				'gameOver': game_over,
				'player': player_battle_info,
				'monster': monster_battle_info
			}
	def get_players_in_current_room(self):
		players = Player.objects.filter(current_room_id = self.current_room_id).exclude(id = self.id)
		players = [ p.user.username for p in players ]
		return players
	def get_player_info(self):
		inventory = self.get_inventory()
		current_room = self.get_room()
		current_room_info = current_room.get_room_info(inventory['item_ids'])
		return {
			'currentRoom': current_room_info,
			'inventory': inventory['info'],
			'username': self.user.username,
			'uuid': self.uuid,
			'validDirections': current_room.get_valid_directions()
		}
	def get_inventory(self):
		inventory_objects = Inventory.objects.filter(player = self.id)
		info = []
		item_ids = []
		for i in inventory_objects:
			info.append({ 'name': i.item.name, 'description': i.item.description })
			item_ids.append(i.item.id)
		return { 'info': info, 'item_ids': item_ids }
	def get_player_by_name(self, player_name):
		return [ p for p in Player.objects.all() if p.user.username == player_name ]
	def get_player_uuids_in_room(self):
		return [ p.uuid for p in Player.objects.filter(current_room_id = self.current_room_id) ]
	def get_room(self):
		try:
			room = Room.objects.get(id = self.current_room_id)
		except Room.DoesNotExist:
			raise NotFound(detail = 'That room does not exist. Did you provide an invalid direction?')
		else:
			return room
	def is_item_in_inventory(self, item_id):
		try:
			item = Inventory.objects.get(player = self.id, item = item_id)
		except Inventory.DoesNotExist:
			return False
		else:
			return True
	def pick_up_item(self, item_name):
		# if lantern is not in inventory and player is past room 2, do not allow pick up of items
		if not self.is_item_in_inventory(1) and self.current_room_id > 2: # lantern item id is 1
			adventure_history_entry = [ 'You fumble around in the darkness. Is there a light source somewhere?' ]
		else:
			try:
				item_in_room = Item.objects.get(name = item_name, room = self.current_room_id)
			except Item.DoesNotExist:
				adventure_history_entry = [ 'There is no {} in this room. Did you spell the name correctly?'.format(item_name) ]
			else:
				item_in_inventory = self.is_item_in_inventory(item_in_room.id)
				if item_in_inventory:
					adventure_history_entry = [ 'You already picked up the {} from this room.'.format(item_name) ]
				else:
					self.place_item_in_inventory(item_in_room)
					adventure_history_entry = [ 'You picked up a {}!'.format(item_name) ]
		player_info = self.get_player_info()
		return {
			**player_info,
			'adventureHistory': adventure_history_entry,
		}
	def place_item_in_inventory(self, item):
		Inventory.objects.create(item = item, player = self)
	def process_monster_attack(self, monster_name):
		monster = Monster.objects.get(name = monster_name)
		battle = Battle.objects.get(player = self.id, monster = monster.id)
		has_shield = self.is_item_in_inventory(4) # shield item id is 4
		if has_shield:
			battle.player_hp = battle.player_hp - 20
			adventure_history_entry = 'The {} strikes back! You absorb the blow with your shield.'.format(monster_name)
		else:
			battle.player_hp = battle.player_hp - 35
			adventure_history_entry = 'The {} strikes back! You have nothing to use to defend yourself.'.format(monster_name)
		if battle.player_hp < 0: battle.player_hp = 0
		battle.save()
		updated_battle_info = self.get_battle_info(monster_name)
		if battle.player_hp == 0:
			game_over = monster_name
		else:
			game_over = False
		return {
			'adventureHistory': [ adventure_history_entry ],
			'battle': updated_battle_info,
			'gameOver': game_over
		}
	def process_attack(self, monster_name):
		monster = Monster.objects.get(name = monster_name)
		battle = Battle.objects.get(player = self.id, monster = monster.id)
		has_sword = self.is_item_in_inventory(3) # sword item id is 3
		if has_sword:
			battle.monster_hp = battle.monster_hp - 25
			adventure_history_entry = 'You swing your sword and strike!'
		else:
			battle.monster_hp = battle.monster_hp - 10
			adventure_history_entry = 'You are unarmed. You take a swing.'
		if battle.monster_hp < 0: battle.monster_hp = 0
		battle.save()
		updated_battle_info = self.get_battle_info(monster_name)
		if battle.monster_hp == 0:
			game_over = True
		else:
			game_over = False
		return {
			'adventureHistory': [ adventure_history_entry ],
			'battle': updated_battle_info,
			'gameOver': game_over
		}
	def process_command(self, command):
		if command.startswith('whisper '):
			split_command = command.lower().split(' ', 2)
			if len(split_command) < 3:
				raise ParseError(detail = 'Invalid whisper. Click on the question mark if you need help.')
			player_name = split_command[1]
			whisper_text = split_command[2]
			return self.whisper(player_name, whisper_text)
		else:
			split_command = command.lower().split(' ', 1)
			if len(split_command) < 2:
				raise ParseError(detail = 'Invalid command. Click on the question mark if you need help.')
			if split_command[0] == 'get':
				item_name = split_command[1]
				return self.pick_up_item(item_name)
			if split_command[0] == 'say':
				say_text = split_command[1]
				return self.say(say_text)
			if split_command[0] == 'shout':
				shout_text = split_command[1]
				return self.shout(shout_text)
		raise ParseError(detail = 'Unhandled command. Click on the question mark if you need help.')
	def restart_game(self):
		self.current_room_id = 1
		self.max_hp = 100
		self.save()
		inventory = Inventory.objects.filter(player = self.id)
		inventory.delete()
		battle = Battle.objects.filter(player = self.id)
		battle.delete()
		return self.get_player_info()
	def say(self, say_text):
		uuids = self.get_player_uuids_in_room()
		for uuid in uuids:
			pusher_client.trigger(
				'player-{}'.format(uuid),
				'get-say',
				{ 'player': self.user.username, 'say': say_text }
			)
		player_info = self.get_player_info()
		return {
			**player_info,
			'adventureHistory': [],
		}
	def shout(self, shout_text):
		uuids = self.get_all_player_uuids()
		for uuid in uuids:
			pusher_client.trigger(
				'player-{}'.format(uuid),
				'get-shout',
				{ 'player': self.user.username, 'shout': shout_text }
			)
		player_info = self.get_player_info()
		return {
			**player_info,
			'adventureHistory': [],
		}
	def whisper(self, player_name, whisper_text):
		player = self.get_player_by_name(player_name)
		if len(player) < 1:
			raise NotFound(detail = 'Player "{}" does not exist.'.format(player_name))
		player = player[0]
		if self.current_room_id != player.current_room_id:
			adventure_history_entry = [ 'Adventurer {}> is in another room. You cannot whisper to them." '.format(player_name) ]
		else:
			adventure_history_entry = [ 'You whispered to {}>: "{}"'.format(player_name, whisper_text) ]
			pusher_client.trigger(
				'player-{}'.format(player.uuid),
				'get-whisper',
				{ 'player': self.user.username, 'whisper': whisper_text }
			)
		player_info = self.get_player_info()
		return {
			**player_info,
			'adventureHistory': adventure_history_entry,
		}
	def walk_in_direction(self, dir):
		current_room = self.get_room()
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
		adventure_history_entry = 'You walked {}.'.format(dir)
		player_info = {}
		if next_room_id == 8: # room with id 8 is the locked room
			if self.is_item_in_inventory(7): # key item id is 7
				adventure_history_entry = 'You unlocked the door and walked {}.'.format(dir)
				self.current_room_id = next_room_id
				player_info = self.get_player_info()
				self.save()
			else:
				adventure_history_entry = 'The door is locked and won\'t budge. Is there some other way to open it?'
		else:
			self.current_room_id = next_room_id
			player_info = self.get_player_info()
			self.save()
		return {
			**player_info,
			'adventureHistory': [ adventure_history_entry ],
		}
	def __str__(self):
		return self.user.username

class Item(models.Model):
	name = models.CharField(max_length = 32, unique = True, default = 'default item name')
	description = models.CharField(max_length = 512, default = 'default item description')
	room = models.ForeignKey(Room, on_delete = models.CASCADE)
	def __str__(self):
		return self.name

class Inventory(models.Model):
	item = models.ForeignKey(Item, on_delete = models.CASCADE)
	player = models.ForeignKey(Player, on_delete = models.CASCADE)
	def __str__(self):
		return self.item.name

class Monster(models.Model):
	name = models.CharField(max_length = 32, unique = True, default = 'default monster name')
	max_hp = models.IntegerField(default = 100)
	img_extension = models.CharField(max_length = 8, default = 'png')

class Battle(models.Model):
	player = models.ForeignKey(Player, on_delete = models.CASCADE)
	monster = models.ForeignKey(Monster, on_delete = models.CASCADE)
	player_hp = models.IntegerField(default = 100)
	monster_hp = models.IntegerField(default = 100)

@receiver(post_save, sender = User)
def create_user_player(sender, instance, created, **kwargs):
	if created:
		Player.objects.create(user = instance)
		Token.objects.create(user = instance)

@receiver(post_save, sender = User)
def save_user_player(sender, instance, **kwargs):
	instance.player.save()
