import requests
from bs4 import BeautifulSoup
import time
import random

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Windows x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/62.0.3239.84 Safari/537.36"
}


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


def parse_azlyrics(html, artist, title, verbose=False):
    soup = BeautifulSoup(html, "html.parser")
    found_td = soup.find("td", class_="text-left")

    href = None
    if found_td is not None:
        try:
            found_artist_name = found_td.find_all("b")[1].text.lower()
            found_title = found_td.find("b").text.lower()
        except IndexError as e:
            if verbose:
                print("Whatever man, I gave up years ago: ", e)
            return None

        if artist == found_artist_name or title == found_title:
            href = found_td.find("a")["href"]
        else:
            if verbose:
                print(f"Wrong lyrics found: {artist} vs {found_artist_name}, skipping")
            return None
    else:
        if verbose:
            print(f'Lyrics not found on azlyrics for "{title}"')
        return None

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


def az_request(artist, title, verbose=False):
    search_url = "http://search.azlyrics.com/search.php?q="
    az_url = f"{search_url}{artist} {title}"

    # time.sleep(1)

    resp = requests.get(
        url=az_url,
        headers=headers,
    )
    parsed_lyrics = parse_azlyrics(
        resp.text, artist=artist, title=title, verbose=verbose
    )
    return parsed_lyrics
