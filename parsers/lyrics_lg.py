import lyricsgenius
from lyricsgenius.song import Song

from .lyrics import Lyrics, ValidationError


class LyricsLG(Lyrics):
    def __init__(self, token, verbose=False):
        super().__init__("Genius", verbose)
        self.genius = lyricsgenius.Genius(token, verbose=True) if token else None

    def request(self, artist, title):
        if self.genius is None:
            if self.verbose > 2:
                print("Token invalid or missing, skipping Genius")
            return None

        try:
            response = self.genius.search_songs(f"{artist} {title}")
        except TypeError:  # token wasn't passed in or found in env
            print("Genius token invalid or missing")
            self.genius = None
            return None

        results = response["hits"]
        self.validate_lyrics_found(results, title)

        # Reject non-songs (Liner notes, track lists, etc.)
        result = next(
            (
                r["result"]
                for r in results
                if self.genius._result_is_lyrics(r["result"]["title"])
            ),
            None,
        )
        if not result:
            if self.verbose > 1:
                print(f"No valid Genius result for {title}.")
            return None

        lyrics = self.genius.lyrics(result["url"])

        # Skip results when URL is a 404 or lyrics are missing
        if not lyrics:
            if self.verbose > 1:
                print(f"{title} does not have a valid URL with lyrics. Rejecting.")
            return None

        result = Song(result, lyrics)

        if not (result and result.lyrics):
            if self.verbose > 1:
                print(f'No Genius lyrics found for "{title}"')
            return None

        try:
            self.validate_artist(artist, result.artist)
            self.validate_title(title, result.title)
        except ValidationError as e:
            return None

        if self.verbose:
            print(f'Parsed lyrics for "{title}"')
        return result.lyrics
