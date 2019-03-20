from django.conf.urls	import url
from django.urls		import path
from .					import views, api

urlpatterns = [
	path('', views.index, name = 'index'),
	url('players', api.players),
	url('rooms', api.rooms),
]
