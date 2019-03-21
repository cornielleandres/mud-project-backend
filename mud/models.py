from django.db							import models
from django.contrib.auth.models			import User
from django.db.models.signals			import post_save
from django.dispatch					import receiver
from rest_framework.authtoken.models	import Token
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
		current_room = self.get_room()
		current_room_info = { 'name': current_room.name, 'description': current_room.description }
		return { 'username': self.user.username, 'current_room': current_room_info }
	def get_room(self):
		return Room.objects.get(id = self.current_room_id)
	def __str__(self):
		return self.user.username

@receiver(post_save, sender = User)
def create_user_player(sender, instance, created, **kwargs):
	if created:
		Player.objects.create(user=instance)
		Token.objects.create(user=instance)

@receiver(post_save, sender = User)
def save_user_player(sender, instance, **kwargs):
	instance.player.save()
