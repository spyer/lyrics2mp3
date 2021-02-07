from .lyrics import Lyrics, ValidationError


class LyricsSL(Lyrics):
    def __init__(self, verbose=False):
        super().__init__("SongLyrics", verbose)

    def parse_single_song(self, href):
        soup = self.parse_html(href)
        parse = soup.find("div", id="songLyricsDiv-outer").get_text().strip()
        if not parse or parse.startswith("We do not have the lyrics for "):
            return None

        return parse

    def parse(self, soup, artist, title):
        found_td = soup.find("div", class_="serpresult")
        self.validate_lyrics_found(found_td, title)

        try:
            found_artist = found_td.find("p").find("a").text.lower()
            found_title = found_td.find("h3").find("a")["title"].lower()
        except (IndexError, AttributeError) as e:
            if self.verbose > 1:
                print("HTML format for site has changed: ", e)
            return None

        self.validate_artist(artist, found_artist)
        self.validate_title(title, found_title)

        href = found_td.find("h3").find("a")["href"]

        parsed_lyrics = self.validate_parse_song(href, title)
        return parsed_lyrics

    def request(self, artist, title):
        search_url = "http://www.songlyrics.com/index.php?section=search&submit=Search&searchIn1=artist&searchIn3=song&searchW="
        url = f"{search_url}{artist}+{title}".replace(" ", "+")
        return super().request(url, artist, title)
