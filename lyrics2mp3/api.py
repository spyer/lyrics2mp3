import taglib

import os

from .parsers.lyrics_az import LyricsAZ
from .parsers.lyrics_lg import LyricsLG
from .parsers.lyrics_lm import LyricsLM
from .parsers.lyrics_sl import LyricsSL


class Lyrics2MP3:
    def __init__(
        self,
        verbose: bool = False,
        manually_confirm: bool = False,
        write_on_not_found: bool = False,
        overwrite: bool = False,
        lg_token: str = None,
    ):
        self.verbose = verbose
        self.manually_confirm = manually_confirm
        self.write_on_not_found = write_on_not_found
        self.overwrite = overwrite

        self.have_lyrics = 0
        self.added_lyrics = 0
        self.no_lyrics_found = 0
        self.err = 0

        lyrics_args = dict(verbose=verbose, manually_confirm=manually_confirm)

        self.ly_lg = None
        if lg_token:
            self.ly_lg = LyricsLG(lg_token, **lyrics_args)

        self.ly_az = LyricsAZ(**lyrics_args)
        self.ly_lm = LyricsLM(**lyrics_args)
        self.ly_sl = LyricsSL(**lyrics_args)

    def get_lyrics(self, title, artist=None, album_artist=None):
        parsed_lyrics = None

        for parser in [self.ly_lg, self.ly_az, self.ly_lm, self.ly_sl]:
            if parser is None:
                continue

            if parsed_lyrics is not None:
                break

            parsed_lyrics = parser.request(title, artist=artist)

        # fuzzy match
        if parsed_lyrics is None and (
            artist and "(" in artist or title and "(" in title
        ):
            if self.verbose:
                print(f"Trying {title} without parentheses")
            if album_artist:
                artist = album_artist
            elif artist and "(" in artist:
                artist = artist[: artist.index("(")].strip()
            if "(" in title:
                title = title[: title.index("(")].strip()
            parsed_lyrics = self.get_lyrics(title, artist=artist)

        if parsed_lyrics is None and self.write_on_not_found:
            return "..."

        return parsed_lyrics

    def parse_file(self, file_path, ignore_artist=False, simulate=False):
        ext = os.path.splitext(file_path)[-1].lower()
        if ext not in (".mp3", ".m4a"):
            return

        try:
            audiofile = taglib.File(file_path)
            old_lyrics = audiofile.tags.get("LYRICS", [""])[0]
        except OSError:
            if self.verbose:
                print(f"Could not read {file_path}, skipping")
            self.err += 1
            return

        if not self.overwrite and (
            old_lyrics is not None
            and len(old_lyrics) > 10
            or self.write_on_not_found
            and old_lyrics == "..."
        ):
            if self.verbose:
                print(f"Lyrics found in music file: {file_path}, skipping")
            self.have_lyrics += 1
            return

        try:
            search_artist = None
            search_album_artist = None
            if not ignore_artist:
                search_album_artist = audiofile.tags.get("ALBUMARTIST")
                if search_album_artist:
                    search_album_artist = search_album_artist[0].lower()
                search_artist = audiofile.tags["ARTIST"][0].lower()
            search_title = audiofile.tags["TITLE"][0].lower()
        except KeyError:
            if self.verbose:
                print(f"No artist or title in music file {file_path}")
            self.err += 1
            return

        lyrics = self.get_lyrics(
            title=search_title, artist=search_artist, album_artist=search_album_artist
        )

        artist_str = f"{search_artist}: " if search_artist else ""

        if lyrics is not None:
            audiofile.tags["LYRICS"] = lyrics
            if simulate:
                print("Simulating, not actually saving lyrics")
            else:
                audiofile.save()
            self.added_lyrics += 1
            if self.verbose:
                print(f"Lyrics found for {artist_str}{search_title}")
        else:
            self.no_lyrics_found += 1
            if self.verbose:
                print(f"No lyrics found for {artist_str}{search_title}")

    def get_lyrics_from_dir(self, dir, ignore_artist=False, simulate=False):
        if not (dir is None or os.path.isdir(dir)):
            raise LookupError(f'Directory "{dir}" not found.')

        for dir_path, _, files in os.walk(dir):
            for file in files:
                self.file_lyrics(
                    os.path.join(dir_path, file),
                    ignore_artist=ignore_artist,
                    simulate=simulate,
                )

    def get_lyrics_from_m3u(self, m3u, ignore_artist=False, simulate=False):
        if not os.path.isfile(m3u):
            raise FileNotFoundError(f'File "{m3u}" not found.')

        if not m3u.endswith(".m3u"):
            raise SyntaxError(f'Playlist "{m3u}" is not M3U format.')

        with open(m3u) as m:
            for line in m:
                line = line.strip()
                if line.upper().startswith("#EXT"):
                    continue

                self.file_lyrics(line, ignore_artist=ignore_artist, simulate=simulate)

    def file_lyrics(self, file_path, ignore_artist=False, simulate=False):
        self.parse_file(file_path, ignore_artist=ignore_artist, simulate=simulate)
        if not self.verbose:
            self.report_progress(inline=True)

    def report_progress(self, inline=False):
        l_sum = self.have_lyrics + self.added_lyrics + self.no_lyrics_found + self.err
        txt = f"{self.added_lyrics} added, {self.no_lyrics_found} not found, {self.err} errored."
        if not self.overwrite:
            txt = f"{self.have_lyrics} existing, {txt}"

        txt = f"{l_sum} processed: {txt}"
        if inline:
            print(f"\r{txt}", end="")
        else:
            print(txt)

    def print_summary(self):
        if self.verbose:
            self.report_progress()
        print()
