import lyricsgenius
from lyricsgenius.song import Song

from .lyrics import Lyrics, ValidationError


class LyricsLG(Lyrics):
    def __init__(self, token, verbose=False):
        super().__init__("Genius", verbose)
        self.genius = lyricsgenius.Genius(token, verbose=True) if token else None

    def parse(self, artist, title):
        msg = "Token invalid or missing, skipping Genius"
        self.validate(self.genius, msg, verbose_gte=3)

        try:
            response = self.genius.search_songs(f"{artist} {title}")
        except TypeError:  # token wasn't passed in or found in env
            print("Genius token invalid or missing")
            self.genius = None
            return None

        results = response["hits"]
        self.validate_lyrics_found(results, title)

        # Reject non-songs (Liner notes, track lists, etc.)
        get_lyrics = self.genius._result_is_lyrics
        result = next(
            (r["result"] for r in results if get_lyrics(r["result"]["title"])),
            None,
        )
        self.validate(result, f"No valid Genius result for {title}.", verbose_gte=2)

        lyrics = self.genius.lyrics(result["url"])

        # Skip results when URL is a 404 or lyrics are missing
        self.validate(lyrics, f"No valid URL with lyrics for {title}", verbose_gte=2)

        result = Song(result, lyrics)

        self.validate_artist(artist, result.artist)
        self.validate_title(title, result.title)

        return result.lyrics

    def request(self, artist, title):
        try:
            parsed_lyrics = self.parse(artist=artist, title=title)
        except ValidationError:
            return None

        if parsed_lyrics and self.verbose:
            print(f'Parsed lyrics from {self.service} for "{title}"')
        elif not parsed_lyrics and self.verbose > 1:
            print(f'Could not parse lyrics from {self.service} for "{title}": ')

        return parsed_lyrics
