import taglib

import argparse
import os
import sys

from parsers.lyrics_az import LyricsAZ
from parsers.lyrics_lg import LyricsLG
from parsers.lyrics_lm import LyricsLM
from parsers.lyrics_sl import LyricsSL

"""
Lyrics2mp3
1. Scans directory for music files.
2. Searches lyrics for each song on azlyrics.com
3. If 'write_on_not_found', inserts lyrics into music file, or '...' if not found
"""

parser = argparse.ArgumentParser(
    description="lyrics2mp3: Find lyrics and add them into music files"
)
parser._action_groups.pop()

# required = parser.add_argument_group("required arguments")
optional = parser.add_argument_group("optional arguments")
file_source = parser.add_mutually_exclusive_group(required=True)

file_source.add_argument("--dir", help="Directory to search for music files")
file_source.add_argument("--m3u", help="Playlist to search for music files")

optional.add_argument(
    "--genius_token",
    help="API token for genius.com music database. Without this token Genius will not be used. Sign up for token at https://genius.com/api-clients",
)
optional.add_argument(
    "--write_on_not_found",
    action="store_true",
    help="Write '...' on files with no lyrics found.",
)
optional.add_argument(
    "--overwrite", action="store_true", help="Overwrite existing lyrics in music files"
)
optional.add_argument(
    "--simulate",
    "-s",
    action="store_true",
    help="Simulate retrieval but change no files",
)
optional.add_argument(
    "--verbose", "-v", action="count", default=0, help="Level of debug info to display"
)


args = parser.parse_args()

if not (args.dir is None or os.path.isdir(args.dir)):
    print(f'Directory "{args.dir}" not found.')
    sys.exit(1)

directory = args.dir

if args.m3u is not None:
    if not os.path.isfile(args.m3u):
        print(f'File "{args.m3u}" not found.')
        sys.exit(1)

    if not args.m3u.endswith(".m3u"):
        print(f'Playlist "{args.m3u}" is not M3U format.')
        sys.exit(1)

playlist = args.m3u

ly_lg = LyricsLG(args.genius_token, verbose=args.verbose)
ly_az = LyricsAZ(verbose=args.verbose)
ly_lm = LyricsLM(verbose=args.verbose)
ly_sl = LyricsSL(verbose=args.verbose)


def get_lyrics(artist, title, album_artist=None):
    parsed_lyrics = None

    for parser in [ly_lg, ly_az, ly_lm, ly_sl]:
        if parsed_lyrics is not None:
            break

        parsed_lyrics = parser.request(artist, title)

    # fuzzy match
    if parsed_lyrics is None and "(" in artist or "(" in title:
        if args.verbose:
            print(f"Trying {title} without parentheses")
        if album_artist:
            artist = album_artist
        elif "(" in artist:
            artist = artist[: artist.index("(")].strip()
        if "(" in title:
            title = title[: title.index("(")].strip()
        parsed_lyrics = get_lyrics(artist, title)

    if parsed_lyrics is None and args.write_on_not_found:
        return "..."

    return parsed_lyrics


have_lyrics = 0
added_lyrics = 0
no_lyrics_found = 0
err = 0


def parse_file(file_path):
    global have_lyrics
    global added_lyrics
    global no_lyrics_found
    global err

    ext = os.path.splitext(file_path)[-1].lower()
    if ext not in (".mp3", ".m4a"):
        return

    try:
        audiofile = taglib.File(file_path)
        old_lyrics = audiofile.tags.get("LYRICS", [""])[0]
    except OSError as e:
        if args.verbose:
            print(f"Could not read {file_path}, skipping")
        err += 1
        return

    if not args.overwrite and (
        old_lyrics is not None
        and len(old_lyrics) > 10
        or args.write_on_not_found
        and old_lyrics == "..."
    ):
        if args.verbose:
            print(f"Lyrics found in music file: {file_path}, skipping")
        have_lyrics += 1
        return

    try:
        search_album_artist = audiofile.tags.get("ALBUMARTIST")
        if search_album_artist:
            search_album_artist = search_album_artist[0].lower()
        search_artist = audiofile.tags["ARTIST"][0].lower()
        search_title = audiofile.tags["TITLE"][0].lower()
    except KeyError:
        if args.verbose:
            print(f"No artist or title in music file {file_path}")
        err += 1
        return

    lyrics = get_lyrics(
        artist=search_artist, title=search_title, album_artist=search_album_artist
    )
    if lyrics is not None:
        audiofile.tags["LYRICS"] = lyrics
        if args.simulate:
            print("Simulating, not actually saving lyrics")
        else:
            audiofile.save()
        added_lyrics += 1
        if args.verbose:
            print(f"Lyrics found for {search_artist}: {search_title}")
    else:
        no_lyrics_found += 1
        if args.verbose:
            print(f"No lyrics found for {search_artist}: {search_title}")


def report_progress(inline=False):
        l_sum = have_lyrics + added_lyrics + no_lyrics_found + err
        txt = f"{added_lyrics} added, {no_lyrics_found} not found, {err} errored."
        if not args.overwrite:
            txt = f"{have_lyrics} existing, {txt}"

        txt = f"{l_sum} processed: {txt}"
        if inline:
            print(txt)
        else:
            print(f"\r{txt}", end="")


def file_lyrics(file_path):
    parse_file(file_path)
    if not args.verbose:
        report_progress(inline=True)

def end_report():
    if args.verbose:
        report_progress()
    print()

try:
    if args.dir:
        for dir_path, _, files in os.walk(args.dir):
            for file in files:
                file_lyrics(os.path.join(dir_path, file))

    elif args.m3u:
        with open(args.m3u) as m:
            for line in m:
                line = line.strip()
                if line.upper().startswith("#EXT"):
                    continue

                file_lyrics(line)

except KeyboardInterrupt:
    pass

end_report()

