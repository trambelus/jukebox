"""The jinja2 environment."""

import application, os.path
from jinja2 import Environment, FileSystemLoader
from .app import app
from .settings import ISettings
from .util import format_timedelta, queue_duration

environment = Environment(
    loader = FileSystemLoader(os.path.join('jukebox', 'templates'))
)

environment.filters['format_timedelta'] = format_timedelta

def format_track(track):
    """Format a track into a table row: track number, track title, album, artist(s), album art."""
    escape = environment.filters['escape']
    return '<tr>\n<td>{0.track_number}</td>\n<td><a class="track-queue" id="{0.id}" href="/queue_track/{0.id}">{title}</a></td>\n<td><a class="track-album" id="{0.id}" href="/album/{0.album.id}">{album}</a></td>\n<td>{artists}</td>\n<td>{duration}</td>\n<td>{album_art}</td>\n<td>{lyrics}</td>\n</tr>\n'.format(
        track,
        title = escape(track.title),
        album = escape(track.album),
        artists = ', '.join(['<a class="track-artist" id="{0.id}" href="/artist/{0.id}">{0.name}</a>'.format(artist) for artist in track.artists]),
        duration = format_timedelta(track.duration),
        album_art = '<a href="{0.artwork}" target="_blank"><img src="{0.artwork}" alt="Album art"></a>'.format(track.album) if track.album.artwork is not None else '-',
        lyrics = format_lyrics(track)
    )

environment.filters['format_track'] = format_track

def format_album(album):
    """Format an album."""
    escape = environment.filters['escape']
    return '<span><a class="track-album" id="{0.id}" href="/album/{0.id}">{artist} - {name} ({year})</a></span>{artwork}'.format(
        album,
        artist = escape(album.artists[0].name if album.artists else 'Unknown Artist'),
        name = escape(album.name),
        year = escape(album.year),
        artwork = ' <a href="{0}" target="_blank"><img src="{0}" alt="Album art"></a>'.format(album.artwork) if album.artwork else ''
    )

environment.filters['format_album'] = format_album

def format_artist(artist):
    """Format an artist."""
    escape = environment.filters['escape']
    text = '<h4><a class="track-artist" id="{0.id}" href="/artist/{0.id}">{name}</a></h4>'.format(artist, name = escape(artist.name))
    if artist.artwork_urls:
        text += '\n<ul>'
        for url in artist.artwork_urls:
            text += '\n<li><a href="{0}" target="_blank"><img src="{0}" alt="Artist artwork"></a></li>'.format(url)
        text += '\n</ul>'
    if artist.bio:
        text += '\n<p>{}</p>'.format(str(artist.bio).replace('\n\n', '</p>\n<p>'))
    return text

environment.filters['format_artist'] = format_artist

def format_playlist(playlist):
    """Format a playlist."""
    escape = environment.filters['escape']
    return '<h3><a class="playlist-link" id="{0.id}" href="/playlist/{0.id}">{name}</a></h3>\n<p><pre>{description}</pre></h3>'.format(
        playlist,
        name = escape(playlist.name),
        description = escape(playlist.description)
    )

environment.filters['format_playlist'] = format_playlist

def format_lyrics(track):
    """Format a lyrics link."""
    urlencode = environment.filters['urlencode']
    return '<a href="/lyrics/{artist_encode}/{title_encode}" target="_blank">Lyrics</a>'.format(
        artist_encode = urlencode(track.artists[0] if track.artists else 'Unknown Artist'),
        title_encode = urlencode(track.title)
    )

environment.filters['format_lyrics'] = format_lyrics

tracks_table_header = '<table>\n<tr>\n<th>Track Number</th>\n<th>Title</th>\n<th>Album</th>\n<th>Artist(s)</th>\n<th>Duration</th>\n<th>Album Art</th><th>Lyrics</th>\n</tr>\n'

environment.globals['tracks_table_header'] = tracks_table_header

environment.globals['app_name'] = '{0.name} V{0.__version__}'.format(application)
environment.globals['app'] = app

def render_template(request, name, *args, **kwargs):
    """
    Render a template and return it as a string.
    
    Return the resulting template rendered with args and kwargs.
    
    The following keyword arguments are provided by this function unless overridden:
    session - The session object for the request.
    settings - The ISettings for the session.
    duration - A timedelta representing the duration of the queue.
    """
    template = environment.get_template(name)
    kwargs.setdefault('request', request)
    kwargs.setdefault('session', request.getSession())
    kwargs.setdefault('settings', ISettings(kwargs['session']))
    kwargs.setdefault('duration', queue_duration())
    return template.render(*args, **kwargs)
