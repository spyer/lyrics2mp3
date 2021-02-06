import requests
from bs4 import BeautifulSoup, element
import time
import random
import re

from .common import headers

domain = "https://www.lyricsmania.com"


def parse_single_song(href):
    resp = requests.get(
        url=href,
        headers=headers,
    )
    soup = BeautifulSoup(resp.text, "html.parser")

    txt = []
    for node in soup.find("div", class_="lyrics-body").contents[2:]:
        line = None
        if isinstance(node, element.Tag):
            line = node.text.strip()
        elif isinstance(node, element.NavigableString):
            line = node.strip()

        if line:
            txt.append(line)

    parsed_lyrics = "\n".join(txt)
    return parsed_lyrics or None


def parse_lyricsmania(html, artist, title, verbose=False):
    soup = BeautifulSoup(html, "html.parser")
    found_td = soup.find("ul", class_="search").find("a")

    if found_td is None:
        if verbose:
            print(f'Lyrics not found on lyricsmania for "{title}"')
        return None

    try:
        found_title, found_artist_name = found_td.text.lower().split(" - ")
    except IndexError as e:
        if verbose:
            print("HTML format for site has changed: ", e)
        return None
    except ValueError as e:
        if verbose:
            print("Can't parse song title: ", e)
        return None

    if not artist == found_artist_name:
        if verbose:
            print(f"Wrong artist found: {artist} vs {found_artist_name}, skipping")
        return None

    if not (title in found_title or found_title in title):
        if verbose:
            print(f"Wrong song found for {artist}: {title} vs {found_title}, skipping")
        return None

    href = domain + found_td["href"]

    if verbose:
        print("href: ", href)

    try:
        parsed_lyrics = parse_single_song(href)
    except Exception as e:
        print(f'Could not parse lyrics for "{title}": ', e)
        return None

    if verbose:
        print(f'Parsed lyrics for "{title}"')
    return parsed_lyrics


def lm_request(artist, title, verbose=False):
    lm_url = f"{domain}/search.php?k={artist}+{title}".replace(" ", "+")

    resp = requests.get(
        url=lm_url,
        headers=headers,
    )
    parsed_lyrics = parse_lyricsmania(
        resp.text, artist=artist, title=title, verbose=verbose
    )
    return parsed_lyrics
