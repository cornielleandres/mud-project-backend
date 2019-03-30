from django.shortcuts	import render
from django.http		import HttpResponse
from decouple			import config


def index(request):
	front_end_url = config('CORS_ORIGIN_WHITELIST')
	in_dev_env = config('DEBUG', default = False, cast = bool)
	protocol = 'http://' if in_dev_env else 'https://'
	return HttpResponse("""
		<h1 style = 'text-align: center'>Hello! You\'re at the MUD index. The API is up an running.</h1>
		<h2 style = 'text-align: center'>Checkout the front-end at:</h2>
		<h2 style = 'text-align: center'>{}{}</h2>
	""".format(protocol, front_end_url))
