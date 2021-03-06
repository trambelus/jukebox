"""The Klein instance."""

import logging
from klein import Klein
from .api import api

logger = logging.getLogger(__name__)

app = Klein()
app.track = None # The currently-playing track.
app.stream = None # The currently playing stream.
app.queue = [] # The tracks to be played.
app.owners = {} # track: owner pares.
app.owner = None # The owner of the currently playing track.

from sound_lib.stream import URLStream

def play_manager():
    """Play the next track."""
    if app.stream is None or not app.stream.is_playing: # The current track has finished playing
        if app.queue:
            track = app.queue.pop(0)
            if track in app.owners:
                app.owner = app.owners[track]
                del app.owners[track]
            else:
                app.owner = None
            if track.artists[0].bio is None:
                track.artists[0].populate(api.get_artist_info(track.artists[0].id))
            url = api.get_stream_url(track.id)
            app.stream = URLStream(url.encode())
            logger.info('Playing track: %s.', track)
            app.stream.play()
            app.track = track
        else:
            app.track = None
            app.stream = None
            app.owner = None
