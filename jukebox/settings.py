"""
settings.py: Session-specific settings.
"""

from zope.interface import Interface, Attribute, implementer
from twisted.python.components import registerAdapter
from twisted.web.server import Session

class ISettings(Interface):
    """Settings for the current session."""
    tracks = Attribute('The tracks loaded for this session.')
    artists = Attribute('The artists loaded for this session.')
    albums = Attribute('The albums loaded for this session.')
    playlists = Attribute('The playlists loaded for this session.')
    message = Attribute('A message to show to the user.')
    tracks_header = Attribute('The heading before the list of tracks.')
    artist = Attribute('The currently-focused artist.')
    album = Attribute('The currently-focused album.')
    playlist = Attribute('The currently loaded playlist.')

@implementer(ISettings)
class Settings(object):
    def __init__(self, session):
        self.tracks = []
        self.artists = []
        self.albums = []
        self.playlists = []
        self.message = None
        self.tracks_header = 'Track Results'
        self.artist = None
        self.album = None
        self.playlist = None

registerAdapter(Settings, Session, ISettings)
