# lyrics2mp3

Parse lyrics and add them into mp3 and m4a files (via id tags).
Lyrics can then be viewed on iPhone, iTunes and other players.

What script does:
1. Scans directory recursively, or each file in playlist, for music files.
2. Reads artist and title from music tag.
3. Searches lyrics for each song on genius.com, azlyrics.com, lyricsgenius.com, songlyrics.com
4. Inserts lyrics into music file if found (unless simulating).

Installation:

```
git clone https://github.com/spyer/lyrics2mp3.git
pip3 install -r requirements.txt
```

If you have trouble installing, please check if **taglib** library is installed (may have to compile).

Usage:

```
Required arguments:
  one of:
    --dir DIR               Directory to search for music files
    --m3u PATH              Playlist to search for music files

Optional arguments:
  --genius_token TOKEN      API token for genius.com music database. Without this token Genius will not be used. Sign up for token at https://genius.com/api-clients
  --write_on_not_found      Write '...' on files with no lyrics found
  --overwrite               Overwrite existing lyrics
  --ignore_artist           Ignore files' artists, look at song name only 
  --simulate, -s            Simulate retrieval but change no files
  --verbose, -v             Level of debug info to display
  --help                    Show all arguments
```
