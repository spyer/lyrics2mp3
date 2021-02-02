import taglib

import argparse
import os
import sys

import lyrics_az
import lyrics_lg

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
    "--write_on_not_found",
    action="store_true",
    help="If passed in, will write '...' on files with no lyrics found.",
)
optional.add_argument("--genius_token", help="API key for genius.com music database")
optional.add_argument("--verbose", "-v", action="store_true", help="Lots of debug info")


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

lyrics_lg.init_genius(args.genius_token)


def get_lyrics(artist, title, album_artist=None):
    # LyricsGenius
    parsed_lyrics = lyrics_lg.lg_request(artist, title, verbose=args.verbose)

    # AZ Lyrics
    if parsed_lyrics is None:
        parsed_lyrics = lyrics_az.az_request(artist, title, verbose=args.verbose)

    # fuzzy match
    if parsed_lyrics is None and "(" in artist or "(" in title:
        if args.verbose:
            print("Trying without paretheses")
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


def parse_file(file_path):
    global have_lyrics
    global added_lyrics
    global no_lyrics_found

    ext = os.path.splitext(file_path)[-1].lower()
    if ext not in (".mp3", ".m4a"):
        return

    audiofile = taglib.File(file_path)
    old_lyrics = audiofile.tags.get("LYRICS", [""])[0]

    if (
        old_lyrics is not None
        and len(old_lyrics) > 10
        or args.write_on_not_found
        and old_lyrics == "..."
    ):
        if args.verbose:
            print(f"Lyrics found in music file: {file_path} skipping")
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
        return

    lyrics = get_lyrics(
        artist=search_artist, title=search_title, album_artist=search_album_artist
    )
    if lyrics is not None:
        audiofile.tags["LYRICS"] = lyrics
        audiofile.save()
        added_lyrics += 1
    else:
        no_lyrics_found += 1

    if not args.verbose:
        print(
            f"\r{have_lyrics + added_lyrics + no_lyrics_found} processed: {have_lyrics} existing, {added_lyrics} added, {no_lyrics_found} not found.",
            end="",
        )


if args.dir:
    for dir_path, _, files in os.walk(args.dir):
        for file in files:
            parse_file(os.path.join(dir_path, file))

elif args.m3u:
    with open(args.m3u) as m:
        for line in m:
            line = line.strip()
            if line.upper().startswith("#EXT"):
                continue

            parse_file(line)
