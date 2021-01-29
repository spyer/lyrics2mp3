import requests
from bs4 import BeautifulSoup
import taglib
import lyricsgenius
import argparse
import os
import sys
import time
import random

"""
Lyrics2mp3
1. Scans directory for music files.
2. Searches lyrics for each song on azlyrics.com
3. If 'write_on_not_found', inserts lyrics into music file, or '...' if not found
"""

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Windows x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/62.0.3239.84 Safari/537.36"
}


search_url = "http://search.azlyrics.com/search.php?q="

parser = argparse.ArgumentParser(
    description="lyrics2mp3: Find lyrics and add them into music files"
)
parser._action_groups.pop()

required = parser.add_argument_group("required arguments")
optional = parser.add_argument_group("optional arguments")

required.add_argument("--dir", nargs=1, help="Directory to search for music files")

optional.add_argument("--write_on_not_found", action="store_true", help="If passed in, will write '...' on files with no lyrics found.")
optional.add_argument("--genius_token", help="API key for genius.com music database")

args = parser.parse_args()

if args.dir is None:
    parser.print_help()
    sys.exit(0)

if args.dir[0] is None or not os.path.isdir(args.dir[0]):
    print(f'Directory "{args.dir[0]}" not found.')
    sys.exit(1)

directory = args.dir[0]

genius = None
if args.genius_token:
    genius = lyricsgenius.Genius(args.genius_token)



def parse_single_song(href):
    time.sleep(random.randint(1, 9))

    resp = requests.get(
        url=href,
        headers=headers,
    )
    soup = BeautifulSoup(resp.text, "html.parser")
    parsed_lyrics = (
        soup.find("div", class_="col-xs-12 col-lg-8 text-center")
        .contents[16]
        .get_text()
    )

    return parsed_lyrics


def parse_azlyrics(html, artist, title):
    soup = BeautifulSoup(html, "html.parser")
    found_td = soup.find("td", class_="text-left")

    href = None
    if found_td is not None:
        try:
            found_artist_name = found_td.find_all("b")[1].text.lower()
            found_title = found_td.find("b").text.lower()
        except IndexError as e:
            print("Whatever man, I gave up years ago: ", e)
            return None

        if artist == found_artist_name or title == found_title:
            href = found_td.find("a")["href"]
        else:
            print(f"Wrong lyrics found: {artist} vs {found_artist_name}, skipping")
            return None
    else:
        print(f'Lyrics not found on azlyrics for "{title}"')
        return None

    print("href: ", href)

    try:
        parsed_lyrics = parse_single_song(href)
    except Exception as e:
        print(f'Could not parse lyrics for "{title}": ', e)
        return None

    print("parsed lyrics!")
    return parsed_lyrics


def az_request(artist, title):
    az_url = f"{search_url}{artist} {title}"

    # time.sleep(1)

    resp = requests.get(
        url=az_url,
        headers=headers,
    )
    parsed_lyrics = parse_azlyrics(resp.text, artist=artist, title=title)
    return parsed_lyrics


def lg_request(artist, title):
    global genius
    if genius is None:
        return None

    try:
        result = genius.search_song(title, artist)
    except TypeError:  # token wasn't passed in or found in env
        print("Genius token invalid or not found")
        genius = None
        return None

    if not result or not result.lyrics:
        print(f'No Genius lyrics found for "{title}"')
        return None

    print(f'Result found in Genius for "{title}"')
    return result.lyrics


def get_lyrics(artist, title, album_artist=None):
    # LyricsGenius
    parsed_lyrics = lg_request(artist, title)

    # AZ Lyrics
    if parsed_lyrics is None:
        parsed_lyrics = az_request(artist, title)

    # fuzzy match
    if parsed_lyrics is None and "(" in artist or "(" in title:
        print("Trying without paretheses")
        if album_artist:
            artist = album_artist
        elif "(" in artist:
            artist = artist[: artist.index("(")].strip()
        if "(" in title:
            title = title[: title.index("(")].strip()
        parsed_lyrics = get_lyrics(artist, title)


for dir_path, dirs, files in os.walk(directory):
    path = dir_path.split(os.sep)
    for file in files:
        ext = os.path.splitext(file)[-1].lower()
        if ext in (".mp3", ".m4a"):
            file_path = os.path.join(dir_path, file)

            audiofile = taglib.File(file_path)
            old_lyrics = audiofile.tags.get("LYRICS", [""])[0]

            if (
                old_lyrics is not None
                and len(old_lyrics) > 10
                or args.write_on_not_found
                and old_lyrics == "..."
            ):
                print(f"Lyrics found in music file: {file_path} skipping")
                continue
            try:
                search_album_artist = audiofile.tags["ALBUMARTIST"][0].lower()
                search_artist = audiofile.tags["ARTIST"][0].lower()
                search_title = audiofile.tags["TITLE"][0].lower()
            except KeyError:
                print("No artist or title in music file")
                continue

            lyrics = get_lyrics(artist=search_artist, title=search_title, album_artist=search_album_artist)
            if lyrics is not None:
                audiofile.tags["LYRICS"] = lyrics
                audiofile.save()
