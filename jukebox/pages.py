"""Jukebox app routes."""

from math import floor
from sound_lib.main import BassError
from gmusicapi.exceptions import CallFailure
from .app import app
from .api import api
from .environment import render_template, format_lyrics, format_track, format_artist, format_album, format_playlist, tracks_table_header, environment
from .search_form import SearchForm
from .util import convert, queue_duration
from .settings import ISettings
from . import metadata
from lyricscraper.lyrics import get_lyrics as _get_lyrics
from urllib.parse import unquote
from multidict import MultiDict
from twisted.internet.defer import inlineCallbacks, returnValue
from json import dumps

localhost = '127.0.0.1'

def default_render(request, **kwargs):
    """The default template."""
    kwargs.setdefault('form', SearchForm())
    return render_template(
        request,
        'index.html',
        **kwargs
    )

def _search(request, search):
    """Perform a low-level search."""
    results = api.search(search)
    settings = ISettings(request.getSession())
    settings.tracks_header = 'Track Results'
    settings.artist = None
    settings.album = None
    settings.playlist = None
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

@app.route('/')
@inlineCallbacks
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
            yield _search(request, search)
    returnValue(
        default_render(
            request,
            form = form
        )
    )

@app.route('/artist/<id>')
@inlineCallbacks
def get_artist(request, id):
    """Render an artist to the home page."""
    settings = ISettings(request.getSession())
    settings.artist = None
    settings.playlist = None
    settings.album = None
    try:
        artist = yield api.get_artist_info(id)
        artist = metadata.get_artist(artist)
        settings.artist = artist
    except CallFailure:
        settings.message = 'No artist with that ID.'
    returnValue(
        default_render(request)
    )

@app.route('/album/<id>')
@inlineCallbacks
def get_album(request, id):
    """Get an album and render it to the home page."""
    settings = ISettings(request.getSession())
    settings.artist = None
    settings.playlist = None
    settings.album = None
    try:
        album = yield api.get_album_info(id)
        settings.album = metadata.get_album(album)
        settings.tracks_header = str(environment.filters['escape'](settings.album.name))
        settings.tracks = settings.album.tracks
    except CallFailure:
        settings.tracks_header = 'Unknown Album'
        settings.tracks = []
        settings.message = 'No album with that ID.'
    returnValue(
        default_render(request)
    )

@app.route('/queue_track/<id>')
@inlineCallbacks
def queue_track(request, id):
    """Queue the requested track."""
    settings = ISettings(request.getSession())
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
    if track:
        if queued:
            settings.message = '{} is already queued.'.format(track)
        else:
            settings.message = '{} was added to the play queue.'.format(track)
    else:
        settings.message = 'No track found with that id.'
    returnValue(
        default_render(request)
    )

@app.route('/delete_track/<id>')
def delete_track(request, id):
    """Delete a track from the queue. Only the person who queued the track can do this."""
    settings = ISettings(request.getSession())
    if id in metadata.tracks:
        track = metadata.tracks[id]
    else:
        track = None
    owner = app.owners.get(track)
    if owner == request.getSession().uid or request.transport.getHost().host == localhost:
        if track in app.queue:
            app.queue.remove(track)
            if track in app.owners:
                del app.owners[track]
            settings.message = '{} was removed from the play queue.'.format(track)
        else:
            settings.message = '{} was not removed from the play queue.'.format(track if track is not None else 'Nothing')
    else:
        settings.message = 'You do not have permission to remove this track from the play queue.'
    return default_render(request)

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
    settings = ISettings(request.getSession())
    if app.stream and (request.getSession().uid == app.owner or request.transport.getHost().host == localhost):
        try:
            app.stream.pause()
        except BassError:
            pass
        app.stream = None
        app.owner = None
        app.track = None
        settings.message = 'Track skipped.'
    else:
        settings.message = 'Not skipping.'
    return default_render(request)

@app.route('/station/<id>')
@inlineCallbacks
def get_station(request, id):
    """Get the station with the given ID."""
    settings = ISettings(request.getSession())
    settings.artist = None
    settings.playlist = None
    settings.album = None
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
    settings = ISettings(request.getSession())
    settings.artist = None
    settings.playlist = metadata.get_playlist({'shareToken': id})
    settings.album = None
    try:
        data = yield api.get_shared_playlist_contents(id)
        settings.playlist.tracks.clear()
        for t in data:
            settings.playlist.tracks.append(metadata.get_track(t['track']))
    except CallFailure:
        settings.message = 'Failed to get tracks for the playlist with that ID.' # Playlist will have old tracks or none at all.
    returnValue(
        default_render(request)
    )

@app.route('/modern_search/<string>')
@inlineCallbacks
def modern_search(request, string):
    """Perform an inline search."""
    if string:
        yield _search(request, string)
    returnValue(None)

@app.route('/json')
def get_json(request):
    """Get the contents of settings as json."""
    escape = environment.filters['escape']
    d = {}
    settings = ISettings(request.getSession())
    if app.track is None:
        d['now_playing'] = '<p>Nothing Playing</p>'
        d['progress'] = 0
    else:
        d['now_playing'] = '<p>Now Playing: {0}</p>\n<p>{lyrics} | <a class="track-skip" href="/skip">Skip</a></p>\n<h3>By</h3>{artists}'.format(
            app.track,
            lyrics = format_lyrics(app.track),
            artists = '\n'.join([format_artist(a) for a in app.track.artists])
        )
        d['progress'] = floor((100.0 / (app.stream.get_length() - 1)) * app.stream.get_position())
    if settings.tracks:
        d['tracks'] = tracks_table_header + '\n'.join([format_track(t) for t in settings.tracks]) + '\n</table>'
    else:
        d['tracks'] = '<p>No track results.</p>'
    d['artists'] = '\n'.join([format_artist(a) for a in settings.artists]) or '<p>No artist results.</p>'
    if settings.albums:
        text = '<ul>\n<li>'
        text += '</li>\n<li>'.join([format_album(a) for a in settings.albums])
        text += '</li>\n</ul>'
    else:
        text = '<p>No album results.</p>'
    d['albums'] = text
    d['playlists'] = '\n'.join([format_playlist(p) for p in settings.playlists]) or '<p>No playlist results.</p>'
    d['message'] = settings.message
    d['tracks_header'] = settings.tracks_header
    if settings.artist:
        text = format_artist(settings.artist)
        text += '\n<h3>Top Tracks</h3>\n'
        text += tracks_table_header
        text += '\n'.join([format_track(t) for t in settings.artist.top_tracks])
        text += '\n</table>'
        text += '\n<h3>Albums</h3>\n'
        text += '\n'.join([format_album(a) for a in settings.artist.albums])
        text += '\n<h3>Related Artists</h3>\n'
        text += '\n'.join([format_artist(a) for a in settings.artist.related_artists])
    else:
        text = None
    d['artist'] = text
    if app.queue:
        text = '<li>\n'
        text += '\n'.join(['<li>{artist} - {title} {album_art}{delete}</li>'.format(
            artist = escape(track.artists[0].name) if track.artists else 'Unknown Artist',
            title = escape(track.title),
            album_art = '<a href="{0}" target="_blank"><img str="{0}" alt="Album art"></a> '.format(track.artists[0].artwork_urls[0]) if track.artists and track.artists[0].artwork_urls else '',
            delete = '<a class="track-delete" id="{0.id}">Delete</a>'.format(track)
        ) for track in app.queue])
        text += '\n</ul>\n<p>Duration: %s.</p>' % queue_duration()
        d['queue'] = text
    else:
        d['queue'] = '<p>The play queue is empty.</p>'
    return dumps(d)
