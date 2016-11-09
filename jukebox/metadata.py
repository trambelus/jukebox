"""Objects representing meta data."""

from datetime import timedelta

artists = {}
albums = {}
tracks = {}

def get_id(d):
    """Get the id from a dictionary d."""
    return d.get('storeId', d.get('nid', d.get('trackId', d.get('id'))))

class Album:
    """An album."""
    def __init__(self, data = {}):
        """Initialise with some data."""
        self.id = None
        self.name = None
        self.artists = []
        self.artwork = None
        self.tracks = []
        self.year = None
        self.populate(data)
    
    def populate(self, data):
        """Load in some data."""
        self.id = data.get('albumId') or self.id
        if self.id is None:
            raise ValueError('No album ID provided in data %r.' % data)
        albums[self.id] = self
        self.name = data.get('name') or self.name
        if self.name is None:
            self.name = 'Unknown Album'
        if 'artistId' in data:
            self.artists.clear()
            for a in data['artistId']:
                if a: # Skip Various Artists.
                    self.artists.append(get_artist({'artistId': a, 'name': data.get('artist', data.get('albumArtist')) if a == data['artistId'] else None}))
        self.artwork = data.get('albumArtRef') or self.artwork
        if 'tracks' in data:
            self.tracks.clear()
            for t in data['tracks']:
                self.tracks.append(get_track(t))
        self.year = data.get('year') or self.year
        if self.year is None:
            self.year = 'Unknown Year'
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return '{0.__class__.__name__}(name = {0.name}, artists = {artists}, tracks = {tracks}, year = {0.year})'.format(self, artists = [str(a) for a in self.artists], tracks = [str(x) for x in self.tracks])

def get_album(data):
    """Get an album."""
    id = data.get('albumId')
    if id in albums:
        album = albums[id]
    else:
        album = Album(data)
    album.populate(data)
    return album

class Artist:
    """An artist."""
    def __init__(self, data = {}):
        """Initialise with some data."""
        self.id = None
        self.name = None
        self.bio = None
        self.top_tracks = []
        self.artwork_urls = []
        self.albums = []
        self.related_artists = []
        self.populate(data)
    
    def populate(self, data):
        """Populate with some data."""
        self.id = data.get('artistId') or self.id
        if self.id is None:
            raise ValueError('No artist ID provided in data %r. Current id is %r.' % (data, self.id))
        artists[self.id] = self
        self.name = data.get('name') or self.name
        if self.name is None:
            self.name = 'Unknown Artist'
        self.bio = data.get('artistBio') or self.bio
        if 'topTracks' in data:
            self.top_tracks.clear()
            for t in data['topTracks']:
                self.top_tracks.append(get_track(t))
        if 'artistArtRefs' in data:
            self.artwork_urls.clear()
            for thing in data['artistArtRefs']:
                self.artwork_urls.append(thing['url'])
        if 'albums' in data:
            self.albums.clear()
            for a in data['albums']:
                self.albums.append(get_album(a))
        if 'related_artists' in data:
            self.related_artists.clear()
            for a in data['related_artists']:
                if 'artistId' in a: # Skip Various Artists.
                    self.related_artists.append(get_artist(a))
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return '{0.__class__.__name__}(name = {0.name}, related_artists = {related_artists}, top_tracks = {top_tracks})'.format(self, related_artists = [str(a) for a in self.related_artists], top_tracks = [str(t) for t in self.top_tracks])

def get_artist(data):
    """Get an artist from data."""
    id = data.get('artistId')
    if id in artists:
        artist = artists[id]
    else:
        artist = Artist(data)
    artist.populate(data)
    return artist

class Track:
    """A track."""
    def __init__(self, data):
        """Initialise with some data."""
        self.id = None
        self.title = None
        self.artists = []
        self.album = None
        self.track_umber = None
        self.genre = None
        self.duration = None
        self.populate(data)
    
    def populate(self, data):
        """Populate with some data."""
        self.id = get_id(data) or self.id
        if self.id is None:
            raise ValueError('No track ID provided in data %r.' % data)
        tracks[self.id] = self
        self.title = data.get('title') or self.title
        if self.title is None:
            self.title = 'Untitled Track'
        if 'artistId' in data:
            self.artists.clear()
            for a in data['artistId']:
                if a: # Skip Various Artists.
                    self.artists.append(get_artist({'artistId': a, 'name': data.get('artist', 'Unknown Artist') if a == data['artistId'][0] else None}))
        if 'albumId' in data:
            self.album = get_album({'albumId': data['albumId'], 'name': data.get('album')})
        self.track_number = data.get('trackNumber') or self.track_number
        self.genre = data.get('genre') or self.genre
        if self.genre is None:
            self.genre = 'No genre'
        if 'durationMillis' in data:
            self.duration = timedelta(seconds = int(data['durationMillis']) / 1000)
    
    def __str__(self):
        return self.title
    
    def __repr__(self):
        return '{0.__class__.__name__}(title = {0.title}, artists = {artists})'.format(self, artists = [str(a) for a in self.artists])

def get_track(data):
    """Get a track."""
    id = get_id(data)
    if id in tracks:
        track = tracks[id]
    else:
        track = Track(data)
    track.populate(data)
    return track
