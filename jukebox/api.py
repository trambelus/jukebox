"""The gmusicapi Mobileclient instance."""

from gmusicapi.clients import Mobileclient

api = Mobileclient()

from configobj import ConfigObj

config = ConfigObj('creds.ini')
if not config.get('username'):
    config['username'] = ''
if not config.get('password'):
    config['password'] = ''

if not api.login(config['username'], config['password'], api.FROM_MAC_ADDRESS):
    config.write()
    raise ImportError('Incorrect or missing data found in creds.ini. Edit that file and try again.')
