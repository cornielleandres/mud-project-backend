from django.shortcuts	import render
from django.http		import HttpResponse


def index(request):
	return HttpResponse("Hello! You're at the MUD index. The API is up an running.")
