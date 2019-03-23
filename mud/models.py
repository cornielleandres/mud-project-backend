from django.db							import models
from django.contrib.auth.models			import User
from django.db.models.signals			import post_save
from django.dispatch					import receiver
from rest_framework.authtoken.models	import Token
from rest_framework.exceptions			import NotFound
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
	def get_room_info(self, inventory_ids):
		item_objects = Item.objects.filter(room = self.id).exclude(id__in = inventory_ids)
		items = [ { 'name': item.name, 'description': item.description } for item in item_objects ]
		current_room_info = {
			'name': self.name,
			'description': self.description,
			'items': items,
			'validDirections': self.get_valid_directions()
		}
		return current_room_info
	def __str__(self):
		return self.name

class Player(models.Model):
	user = models.OneToOneField(User, on_delete = models.CASCADE)
	uuid = models.UUIDField(default = uuid.uuid4, unique = True)
	current_room_id = models.IntegerField(default = 1)
	def get_all_players(self, current_player_id):
		return [
			(p.user.username, p.uuid)
			for p in Player.objects.all()
			if p.id != int(current_player_id)
		]
	def get_player_info(self):
		inventory = self.get_inventory()
		current_room = self.get_room()
		current_room_info = current_room.get_room_info(inventory['ids'])
		return {
			'currentRoom': current_room_info,
			'inventory': inventory['info'],
			'username': self.user.username,
		}
	def get_inventory(self):
		inventory_objects = Inventory.objects.filter(player = self.id)
		info = []
		ids = []
		for i in inventory_objects:
			info.append({ 'name': i.item.name, 'description': i.item.description })
			ids.append(i.id)
		return { 'info': info, 'ids': ids }
	def get_room(self):
		try:
			room = Room.objects.get(id = self.current_room_id)
		except Room.DoesNotExist:
			raise NotFound(
				detail = 'That room does not exist. Did you provide an invalid direction?',
				code = 404
			)
		else:
			return room
	def __str__(self):
		return self.user.username

class Item(models.Model):
	name = models.CharField(max_length = 32, default = 'default item name')
	description = models.CharField(max_length = 512, default = 'default item description')
	room = models.ForeignKey(Room, on_delete = models.CASCADE)
	def __str__(self):
		return self.name

class Inventory(models.Model):
	item = models.ForeignKey(Item, on_delete = models.CASCADE)
	player = models.ForeignKey(Player, on_delete = models.CASCADE)
	def __str__(self):
		return self.item.name


@receiver(post_save, sender = User)
def create_user_player(sender, instance, created, **kwargs):
	if created:
		Player.objects.create(user=instance)
		Token.objects.create(user=instance)

@receiver(post_save, sender = User)
def save_user_player(sender, instance, **kwargs):
	instance.player.save()
