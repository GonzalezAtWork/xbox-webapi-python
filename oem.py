import os
import sys

from urllib.parse import parse_qs

sys.path.insert(0, os.path.dirname(__file__))


def application(environ, start_response):
    query_string = environ.get('QUERY_STRING', '')
    params = parse_qs(query_string)
    device = params.get('device', [''])[0]
    action = params.get('action', [''])[0]
    game = params.get('game', [''])[0]

    start_response('200 OK', [('Content-Type', 'text/plain')])
    message = 'It works!\n'
    version = 'Python %s\n' % sys.version.split()[0]
    response = '\n'.join([message, device, action, game, version])
    return [response.encode()]
