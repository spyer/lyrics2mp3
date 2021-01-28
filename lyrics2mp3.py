import requests
from bs4 import BeautifulSoup
import argparse
import os
import sys
import taglib
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
optional.add_argument('--write_on_not_found', action='store_true')

args = parser.parse_args()

if args.dir is None:
    parser.print_help()
    sys.exit(0)

if args.dir[0] is None or not os.path.isdir(args.dir[0]):
    print(f'Directory "{args.dir[0]}" not found.')
    sys.exit(1)

directory = args.dir[0]


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

    ret = '...' if args.write_on_not_found else None

    href = None
    if found_td is not None:
        try:
            found_artist_name = found_td.find_all("b")[1].text.lower()
            found_title = found_td.find("b").text.lower()
        except IndexError as e:
            print("Whatever man, I gave up years ago: ", e)
            return ret

        if artist == found_artist_name or title == found_title:
            href = found_td.find("a")["href"]
        else:
            print(f"Wrong lyrics found: {artist} vs {found_artist_name}, skipping")
            return ret
    else:
        print(f'Lyrics not found on site for "{title}" :(')
        return ret

    print("href: ", href)

    try:
        parsed_lyrics = parse_single_song(href)
    except Exception as e:
        print(f'not found for "{title}": ', e)
        return ret

    print("parsed lyrics!")
    return parsed_lyrics


def get_lyrics(artist, title):
    url = f"{search_url}{artist} {title}"

    time.sleep(1)

    resp = requests.get(
        url=url,
        headers=headers,
    )
    parsed_lyrics = parse_azlyrics(resp.text, artist=artist, title=title)
    return parsed_lyrics


for dir_path, dirs, files in os.walk(directory):
    path = dir_path.split(os.sep)
    for file in files:
        ext = os.path.splitext(file)[-1].lower()
        if ext in (".mp3", ".m4a"):
            file_path = os.path.join(dir_path, file)

            audiofile = taglib.File(file_path)
            old_lyrics = audiofile.tags.get("LYRICS", [""])[0]

            if old_lyrics is not None and len(old_lyrics) > 10 or args.write_on_not_found and old_lyrics == '...':
                print(f"lyrics found in music file: {file_path} skipping")
                continue
            try:
                search_artist = audiofile.tags["ARTIST"][0].lower()
                search_title = audiofile.tags["TITLE"][0].lower()
            except KeyError:
                print("no artist or title in music file")
                continue

            lyrics = get_lyrics(artist=search_artist, title=search_title)
            if lyrics is not None:
                audiofile.tags["LYRICS"] = lyrics
                audiofile.save()
