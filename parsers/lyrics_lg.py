import re

import lyricsgenius

from .lyrics import Lyrics, ValidationError, _clean_str


def remove_extra_spaces(s):
    return " ".join(s.split())


def replace_apostrophe(s):
    return s.replace("’", "'")


def remove_zero_width_space(s):
    return s.replace("\u200b", "")


def remove_right_to_left_mark(s):
    return s.replace("\u200f", "")


def scrub_string(s):
    """
    Removes opinionated unwanted characters from
    string, namely:
        - zero width spaces '\u200b' ---> ''
        - apostrophe '’' ---> ''
        - extra spaces '    ' ---> ' '
    """
    s = remove_zero_width_space(s)
    s = remove_right_to_left_mark(s)
    s = replace_apostrophe(s)
    s = remove_extra_spaces(s)
    return s


def replace_br(s):
    s = s.replace("<br/>", "\n")
    return s


def regexp_replace(s, pattern, repl=""):
    found = re.findall(pattern, s, flags=re.IGNORECASE)
    for f in found:
        s = s.replace(f, repl)
    return s


def remove_embded(s):
    return regexp_replace(s, r"Embed\d*$")


def remove_see_live_ad(s):
    return regexp_replace(s, r"^See .+ Live")


def remove_contributors(s):
    return regexp_replace(s, r"^\d+ Contributor.+ Lyrics")


def remove_also_like(s):
    s = regexp_replace(s, r"^You might also like", repl="\n")
    return regexp_replace(s, r"You might also like$", repl="\n")


def clean_line(s):
    for fn in [
        scrub_string,
        remove_contributors,
        remove_also_like,
        remove_see_live_ad,
        remove_embded,
        replace_br,
    ]:
        s = fn(s)

    return s


class LyricsLG(Lyrics):
    def __init__(self, token, **kwargs):
        super().__init__("Genius", **kwargs)
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
        result = lyricsgenius.genius.Song(self.genius, result, lyrics=lyrics)

        if artist:
            self.validate_artist(artist, result.artist)
        self.validate_title(title, result.title)

        lyrics = "\n".join([clean_line(s) for s in result.lyrics.split("\n")])

        return lyrics

    def request(self, title, artist=None):
        try:
            parsed_lyrics = self.parse(artist=artist, title=title)
        except ValidationError:
            return None

        parsed_lyrics = self.validate_user_wants_lyrics(parsed_lyrics, title)

        if parsed_lyrics and self.verbose:
            print(f'Parsed lyrics from {self.service} for "{title}"')
        elif not parsed_lyrics and self.verbose > 1:
            print(f'Could not parse lyrics from {self.service} for "{title}": ')

        return parsed_lyrics
