import re

import lyricsgenius
from lyricsgenius.song import Song

genius = None

cruft = re.compile("[\.,\[\]\{\}'’]")
and_ = re.compile("[\+&]")


def init_genius(token):
    global genius
    if token:
        genius = lyricsgenius.Genius(token, verbose=True)


def _clean_str(in_str):
    return and_.sub("and", cruft.sub("", in_str.lower()))


def lg_request(artist, title, verbose=False):
    global genius
    if genius is None:
        return None

    # print(title)
    # breakpoint()

    try:
        response = genius.search_songs(f"{artist} {title}")
    except TypeError:  # token wasn't passed in or found in env
        print("Genius token invalid or not found")
        genius = None
        return None

    results = response["hits"]

    # Exit search if there were no results returned from API
    if not results:
        if verbose:
            print(f"No results found for {title}")
        return None

    # Reject non-songs (Liner notes, track lists, etc.)
    result = next(
        (
            r["result"]
            for r in results
            if genius._result_is_lyrics(r["result"]["title"])
        ),
        None,
    )
    if not result:
        if verbose:
            print(f"Found no lyrics for {title}.")
        return None

    lyrics = genius.lyrics(result["url"])

    # Skip results when URL is a 404 or lyrics are missing
    if not lyrics:
        if verbose:
            print(f"{title} does not have a valid URL with lyrics. Rejecting.")
        return None

    result = Song(result, lyrics)

    if not (result and result.lyrics):
        if verbose:
            print(f'No Genius lyrics found for "{title}"')
        return None

    r_artist = _clean_str(result.artist)
    c_artist = _clean_str(artist)
    if not (c_artist in r_artist or r_artist in c_artist):
        if verbose:
            print(f"Incorrect artist from Genius: {artist} became {result.artist}")
        return None

    r_title = _clean_str(result.title)
    c_title = _clean_str(title)
    if not (c_title in r_title or r_title in c_title):
        if verbose:
            print(f"Incorrect title from Genius: {title} became {result.title}")
        return None

    if verbose:
        print(f'Result found in Genius for "{title}"')
    return result.lyrics
