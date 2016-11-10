"""Jukebox app routes."""

from gmusicapi.exceptions import CallFailure
from .app import app
from .api import api
from .environment import render_template
from .search_form import SearchForm
from .util import convert
from .settings import ISettings
from . import metadata
from lyricscraper.lyrics import get_lyrics as _get_lyrics
from urllib.parse import unquote
from multidict import MultiDict
from twisted.internet.defer import inlineCallbacks, returnValue

def default_render(request, **kwargs):
    """The default template."""
    kwargs.setdefault('form', SearchForm())
    return render_template(
        request,
        'index.html',
        **kwargs
    )

@app.route('/')
def home(request):
    """Home page."""
    form = SearchForm()
    if request.args:
        data = convert(request.args)
        if 'search' in data:
            data['search'] = data['search'][0]
        form.process(
            MultiDict(
                data
            )
        )
        search = form.data.get('search')
        if search:
            results = api.search(search)
            settings = ISettings(request.getSession())
            settings.tracks.clear()
            for s in results.get('song_hits', []):
                settings.tracks.append(metadata.get_track(s['track']))
            settings.artists.clear()
            for a in results.get('artist_hits', []):
                settings.artists.append(metadata.get_artist(a['artist']))
            settings.albums.clear()
            for a in results.get('album_hits', []):
                settings.albums.append(metadata.get_album(a['album']))
            settings.playlists.clear()
            for p in results.get('playlist_hits', []):
                settings.playlists.append(metadata.get_playlist(p['playlist']))
    return default_render(
        request,
        form = form
    )

@app.route('/artist/<id>')
@inlineCallbacks
def get_artist(request, id):
    """Render an artist to the home page."""
    try:
        artist = yield api.get_artist_info(id)
        artist = metadata.get_artist(artist)
    except CallFailure:
        artist = None
    returnValue(
        default_render(
            request,
            artist = artist
        )
    )

@app.route('/album/<id>')
@inlineCallbacks
def get_album(request, id):
    """Get an album and render it to the home page."""
    try:
        album = yield api.get_album_info(id)
        album = metadata.get_album(album)
        ISettings(request.getSession()).tracks = album.tracks
    except CallFailure:
        album = None
    returnValue(
        default_render(
            request,
            album = album
        )
    )

@app.route('/queue_track/<id>')
@inlineCallbacks
def queue_track(request, id):
    """Queue the requested track."""
    try:
        track = yield api.get_track_info(id)
        track = metadata.get_track(track)
        queued = (track is app.track) or (track in app.queue)
        if not queued:
            app.queue.append(track)
            app.owners[track] = request.getSession().uid
    except CallFailure:
        track = None
        queued = False
    returnValue(
        render_template(
            request,
            'track_queued.html',
            track = track,
            queued = queued
        )
    )

@app.route('/delete_track/<id>')
def delete_track(request, id):
    """Delete a track from the queue. Only the person who queued the track can do this."""
    removed = False
    if id in metadata.tracks:
        track = metadata.tracks[id]
    else:
        track = None
    owner = app.owners.get(track)
    if owner == request.getSession().uid:
        if track in app.queue:
            app.queue.remove(track)
            if track in app.owners:
                del app.owners[track]
            removed = True
    return render_template(
        request,
        'track_deleted.html',
        track = track,
        removed = removed
    )

@app.route('/queue')
def queue(request):
    """Show the queue."""
    return render_template(request, 'queue.html')

@app.route('/lyrics/<artist>/<title>')
@inlineCallbacks
def get_lyrics(request, artist, title):
    """Get the lyrics for a particular track."""
    artist = unquote(artist)
    title = unquote(title)
    lyrics = yield _get_lyrics(artist, title)
    returnValue(
        render_template(
            request,
            'lyrics.html',
            artist = artist,
            title = title,
            lyrics = lyrics
        )
    )

@app.route('/skip')
def skip(request):
    """Skip the currently playing track."""
    if app.stream and request.getSession().uid == app.owner:
        app.stream.pause()
        app.stream = None
        app.track = None
    request.redirect('/')

@app.route('/station/<id>')
@inlineCallbacks
def get_station(request, id):
    """Get the station with the given ID."""
    settings = ISettings(request.getSession())
    try:
        station = yield api.get_station_tracks(id)
        settings.tracks = [metadata.get_track(x) for x in station]
    except CallFailure:
        settings.tracks = []
    returnValue(default_render(request))

@app.route('/playlist/<id>')
@inlineCallbacks
def get_playlist(request, id):
    """Get a playlist."""
    playlist = metadata.get_playlist({'shareToken': id})
    try:
        data = yield api.get_shared_playlist_contents(id)
        playlist.tracks.clear()
        for t in data:
            playlist.tracks.append(metadata.get_track(t['track']))
    except CallFailure:
        pass # Playlist will have old tracks or none at all.
    returnValue(
        default_render(
            request,
            playlist = playlist
        )
    )
