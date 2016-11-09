"""Test metadata."""

from jukebox.metadata import Artist, Album, Track, get_track
from jukebox.api import api

def test_track():
    data = api.get_all_songs()[0]
    assert isinstance(data, dict)
    t = get_track(data)
    assert isinstance(t, Track)
    assert isinstance(t.album, Album)
    t.album.populate(api.get_album_info(t.album.id))
    assert isinstance(t.artists, list) and len(t.artists) >= 1
    assert isinstance(t.artists[0], Artist)
    t.artists[0].populate(api.get_artist_info(t.artists[0].id))
    assert isinstance(t.artists[0].top_tracks, list)
