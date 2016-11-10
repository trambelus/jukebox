"""The jinja2 environment."""

import application, os.path
from datetime import timedelta
from jinja2 import Environment, FileSystemLoader
from .app import app
from .settings import ISettings

environment = Environment(
    loader = FileSystemLoader(os.path.join('jukebox', 'templates'))
)

def format_timedelta(td):
    """Format timedelta td."""
    fmt = [] # The format as a list.
    seconds = int(td.total_seconds())
    years, seconds = divmod(seconds, 31536000)
    if years:
        fmt.append('%d %s' % (years, 'year' if years == 1 else 'years'))
    months, seconds = divmod(seconds, 2592000)
    if months:
        fmt.append('%d %s' % (months, 'month' if months == 1 else 'months'))
    days, seconds = divmod(seconds, 86400)
    if days:
        fmt.append('%d %s' % (days, 'day' if days == 1 else 'days'))
    hours, seconds = divmod(seconds, 3600)
    if hours:
        fmt.append('%d %s' % (hours, 'hour' if hours == 1 else 'hours'))
    minutes, seconds = divmod(seconds, 60)
    if minutes:
        fmt.append('%d %s' % (minutes, 'minute' if minutes == 1 else 'minutes'))
    if seconds:
        fmt.append('%d %s' % (seconds, 'second' if seconds == 1 else 'seconds'))
    if len(fmt) == 1:
        return fmt[0]
    else:
        res = ''
        for pos, item in enumerate(fmt):
            if pos == len(fmt) - 1:
                res += ', and '
            elif res:
                res += ', '
            res += item
        return res

environment.filters['format_timedelta'] = format_timedelta

def format_track(track):
    """Format a track into a table row: track number, track title, album, artist(s), album art."""
    escape = environment.filters['escape']
    urlencode = environment.filters['urlencode']
    return '<tr>\n<td>{0.track_number}</td>\n<td><a href="/queue_track/{0.id}">{title}</a></td>\n<td><a href="/album/{0.album.id}">{album}</a></td>\n<td>{artists}</td>\n<td>{duration}</td>\n<td>{album_art}</td>\n<td><a href="/lyrics/{artist_encode}/{title_encode}" target="_blank">Lyrics</a></td>\n</tr>\n'.format(
        track,
        title = escape(track.title),
        album = escape(track.album),
        artists = ', '.join(['<a href="/artist/{0.id}">{0.name}</a>'.format(artist) for artist in track.artists]),
        duration = format_timedelta(track.duration),
        album_art = '<a href="{0.artwork}" target="_blank"><img src="{0.artwork}" alt="Album art"></a>'.format(track.album) if track.album.artwork is not None else '-',
        artist_encode = urlencode(track.artists[0] if track.artists else 'Unknown Artist'),
        title_encode = urlencode(track.title)
    )

environment.filters['format_track'] = format_track

def format_album(album):
    """Format an album."""
    escape = environment.filters['escape']
    return '<a href="/album/{0.id}">{artist} - {name} ({year})</a>{artwork}'.format(
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
    text = '<h4><a href="/artist/{0.id}">{name}</a></h4>'.format(artist, name = escape(artist.name))
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
    return '<h3><a href="/playlist/{0.id}">{name}</a></h3>\n<p><pre>{description}</pre></h3>'.format(
        playlist,
        name = escape(playlist.name),
        description = escape(playlist.description)
    )

environment.filters['format_playlist'] = format_playlist

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
    tracks_table_header - The header row for the tracks table (includes <table>).
    table_footer # A generic table footer.
    """
    template = environment.get_template(name)
    kwargs.setdefault('request', request)
    kwargs.setdefault('session', request.getSession())
    kwargs.setdefault('settings', ISettings(kwargs['session']))
    kwargs.setdefault('duration', sum([track.duration for track in app.queue], timedelta()))
    kwargs.setdefault('tracks_table_header', '<table>\n<tr>\n<th>Track Number</th>\n<th>Title</th>\n<th>Album</th>\n<th>Artist(s)</th>\n<th>Duration</th>\n<th>Album Art</th><th>Lyrics</th>\n</tr>\n')
    kwargs.setdefault('table_footer', '</table>')
    return template.render(*args, **kwargs)
