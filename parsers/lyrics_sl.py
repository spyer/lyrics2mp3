import requests
from bs4 import BeautifulSoup
import time
import random

from .common import headers


def parse_single_song(href):
    resp = requests.get(
        url=href,
        headers=headers,
    )
    soup = BeautifulSoup(resp.text, "html.parser")
    parsed_lyrics = soup.find("div", id="songLyricsDiv-outer").get_text().strip()
    if not parsed_lyrics or parsed_lyrics.startswith("We do not have the lyrics for "):
        return None

    return parsed_lyrics


def parse_songlyrics(html, artist, title, verbose=False):
    soup = BeautifulSoup(html, "html.parser")
    found_td = soup.find("div", class_="serpresult")

    if found_td is None:
        if verbose:
            print(f'Lyrics not found on songlyrics for "{title}"')
        return None

    try:
        found_artist_name = found_td.find("p").find("a").text.lower()
        found_title = found_td.find("h3").find("a")["title"].lower()
    except (IndexError, AttributeError) as e:
        if verbose:
            print("HTML format for site has changed: ", e)
        return None

    if not artist == found_artist_name:
        if verbose:
            print(f"Wrong artist found: {artist} vs {found_artist_name}, skipping")
        return None

    if not (title in found_title or found_title in title):
        if verbose:
            print(f"Wrong song found for {artist}: {title} vs {found_title}, skipping")
        return None

    href = found_td.find("h3").find("a")["href"]

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


def sl_request(artist, title, verbose=False):
    search_url = "http://www.songlyrics.com/index.php?section=search&submit=Search&searchIn1=artist&searchIn3=song&searchW="
    sl_url = f"{search_url}{artist}+{title}".replace(" ", "+")

    resp = requests.get(
        url=sl_url,
        headers=headers,
    )
    parsed_lyrics = parse_songlyrics(
        resp.text, artist=artist, title=title, verbose=verbose
    )
    return parsed_lyrics
