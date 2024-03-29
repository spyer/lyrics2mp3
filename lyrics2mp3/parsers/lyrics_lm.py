from bs4 import element


from .lyrics import Lyrics


class LyricsLM(Lyrics):
    def __init__(self, **kwargs):
        super().__init__("LyricsMania", **kwargs)
        self.domain = "https://www.lyricsmania.com"

    def parse_single_song(self, href):
        soup = self.parse_html(href)

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

    def parse(self, soup, title, artist=None):
        found_td = soup.find("ul", class_="search").find("a")
        self.validate_lyrics_found(found_td, title)

        try:
            found_title, found_artist = found_td.text.lower().split(" - ")
        except IndexError as e:
            if self.verbose > 1:
                print("HTML format for site has changed: ", e)
            return None
        except ValueError as e:
            if self.verbose > 1:
                print("Can't parse song title: ", e)
            return None

        if artist:
            self.validate_artist(artist, found_artist)
        self.validate_title(title, found_title)

        href = self.domain + found_td["href"]

        parsed_lyrics = self.validate_parse_song(href, title)
        return parsed_lyrics

    def request(self, title, artist=None):
        artist_q = f"{artist}+" if artist else ""
        url = f"{self.domain}/search.php?k={artist_q}{title}".replace(" ", "+")
        return super().request(url, title, artist=artist)
