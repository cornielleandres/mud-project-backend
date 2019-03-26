from django.db							import models
from django.contrib.auth.models			import User
from django.db.models.signals			import post_save
from django.dispatch					import receiver
from rest_framework.authtoken.models	import Token
from rest_framework.exceptions			import NotFound, ParseError
import uuid

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
	hp = models.IntegerField(default = 100)
	attack = models.IntegerField(default = 25)
	defense = models.IntegerField(default = 25)
	def get_all_players(self, current_player_id):
		return [
			(p.user.username, p.uuid)
			for p in Player.objects.all()
			if p.id != int(current_player_id)
		]
	def get_battle_info(self, monster):
		monster = Monster.objects.get(name = monster)
		monster_battle_info = {
			'name': monster.name,
			'maxHp': monster.max_hp,
			'hp': monster.hp,
			'imgExtension': monster.img_extension
		}
		player_battle_info = {
			'maxHp': self.max_hp,
			'hp': self.hp
		}
		return {
			'player': player_battle_info,
			'monster': monster_battle_info
		}
	def get_player_info(self):
		inventory = self.get_inventory()
		current_room = self.get_room()
		current_room_info = current_room.get_room_info(inventory['item_ids'])
		return {
			'currentRoom': current_room_info,
			'inventory': inventory['info'],
			'username': self.user.username,
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
	def process_command(self, command):
		split_command = command.lower().split(' ', 1)
		if len(split_command) < 2:
			raise ParseError(detail = 'Invalid command. Click on the question mark if you need help.')
		if split_command[0] == 'get':
			item_name = split_command[1]
			return self.pick_up_item(item_name)
		raise ParseError(detail = 'Unhandled command. Click on the question mark if you need help.')
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
	hp = models.IntegerField(default = 100)
	attack = models.IntegerField(default = 50)
	defense = models.IntegerField(default = 50)
	img_extension = models.CharField(max_length = 8, default = 'png')

@receiver(post_save, sender = User)
def create_user_player(sender, instance, created, **kwargs):
	if created:
		Player.objects.create(user = instance)
		Token.objects.create(user = instance)

@receiver(post_save, sender = User)
def save_user_player(sender, instance, **kwargs):
	instance.player.save()
