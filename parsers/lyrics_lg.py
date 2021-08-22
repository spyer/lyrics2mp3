import lyricsgenius
from lyricsgenius.song import Song

from .lyrics import Lyrics, ValidationError, _clean_str


class LyricsLG(Lyrics):
    def __init__(self, token, verbose=False):
        super().__init__("Genius", verbose)
        self.genius = lyricsgenius.Genius(token, verbose=True) if token else None

    def parse(self, title, artist=None):
        msg = "Token invalid or missing, skipping Genius"
        self.validate(self.genius, msg, verbose_gte=3)

        try:
            if artist:
                response = self.genius.search_songs(f"{artist} {title}")
            else:
                response = self.genius.search_songs(title)
        except TypeError:  # token wasn't passed in or found in env
            print("Genius token invalid or missing")
            self.genius = None
            return None

        results = response["hits"]

        self.validate_lyrics_found(results, title)

        # Reject non-songs (Liner notes, track lists, etc.), look for a best title match
        # take the first result if no exact match found
        get_lyrics = self.genius._result_is_lyrics
        results = [r["result"] for r in results if get_lyrics(r["result"])]
        result = None
        if results:
            cln_title = _clean_str(title)
            result = next(
                (r for r in results if _clean_str(r["title"]) == cln_title),
                results[0],
            )
        self.validate(result, f"No valid Genius result for {title}.", verbose_gte=2)

        lyrics = self.genius.lyrics(result["id"])

        # Skip results when URL is a 404 or lyrics are missing
        self.validate(lyrics, f"No valid URL with lyrics for {title}", verbose_gte=2)

        result = Song(result, lyrics)

        if artist:
            self.validate_artist(artist, result.artist)
        self.validate_title(title, result.title)

        return result.lyrics

    def request(self, title, artist=None):
        try:
            parsed_lyrics = self.parse(artist=artist, title=title)
        except ValidationError:
            return None

        if parsed_lyrics and self.verbose:
            print(f'Parsed lyrics from {self.service} for "{title}"')
        elif not parsed_lyrics and self.verbose > 1:
            print(f'Could not parse lyrics from {self.service} for "{title}": ')

        return parsed_lyrics
