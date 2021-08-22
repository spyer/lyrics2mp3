from .lyrics import Lyrics


class LyricsAZ(Lyrics):
    def __init__(self, verbose=False):
        super().__init__("azlyrics", verbose)

    def parse_single_song(self, href):
        soup = self.parse_html(href)
        parsed_lyrics = (
            soup.find("div", class_="col-xs-12 col-lg-8 text-center")
            .contents[16]
            .get_text()
        )
        return parsed_lyrics

    def parse(self, soup, title, artist=None):
        found_td = soup.find("td", class_="text-left")
        self.validate_lyrics_found(found_td, title)

        try:
            found_artist = found_td.find_all("b")[1].text.lower()
            found_title = found_td.find("b").text.lower()
        except IndexError as e:
            if self.verbose > 1:
                print("HTML format for site has changed: ", e)
            return None

        if artist:
            self.validate_artist(artist, found_artist)
        self.validate_title(title, found_title)

        href = found_td.find("a")["href"]

        parsed_lyrics = self.validate_parse_song(href, title)
        return parsed_lyrics

    def request(self, title, artist=None):
        search_url = "http://search.azlyrics.com/search.php?q="
        artist_q = f"{artist} " if artist else ""
        url = f"{search_url}{artist_q}{title}"
        return super().request(url, title, artist=artist)
