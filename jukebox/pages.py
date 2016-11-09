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
            tracks = []
            for s in results.get('song_hits', []):
                tracks.append(metadata.get_track(s['track']))
            artists = []
            for a in results.get('artist_hits', []):
                artists.append(metadata.get_artist(a['artist']))
            albums = []
            for a in results.get('album_hits', []):
                albums.append(metadata.get_album(a['album']))
            settings = ISettings(request.getSession())
            settings.tracks = tracks
            settings.artists = artists
            settings.albums = albums
    return render_template(
        request,
        'index.html',
        form = form
    )

@app.route('/artist/<id>')
@inlineCallbacks
def get_artist(request, id):
    """Render an artist to the home page."""
    form = SearchForm()
    try:
        artist = yield api.get_artist_info(id)
        artist = metadata.get_artist(artist)
    except CallFailure:
        artist = None
    returnValue(
        render_template(
            request,
            'index.html',
            form = form,
            artist = artist
        )
    )

@app.route('/album/<id>')
@inlineCallbacks
def get_album(request, id):
    """Get an album and render it to the home page."""
    form = SearchForm()
    try:
        album = yield api.get_album_info(id)
        album = metadata.get_album(album)
        ISettings(request.getSession()).tracks = album.tracks
    except CallFailure:
        album = None
    returnValue(
        render_template(
            request,
            'index.html',
            form = form,
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
