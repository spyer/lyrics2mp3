import requests
from bs4 import BeautifulSoup
import argparse
import os
import sys
import taglib
import time
import random

'''
Lyrics2mp3 
1. Scans directory for mp3 files.
2. Searches lyrics for each song on azlyrics.com
3. Inserts lyrics into mp3 file, or '...' if not found
'''

headers = {'User-Agent': 'Mozilla/5.0 (X11; Windows x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/62.0.3239.84 Safari/537.36'}


search_url = 'http://search.azlyrics.com/search.php?q='

parser = argparse.ArgumentParser(description='lyrics2mp3: Find lyrics and add them into mp3 files')
parser._action_groups.pop()

required = parser.add_argument_group('required arguments')
optional = parser.add_argument_group('optional arguments')

required.add_argument('--dir', nargs=1, help='Directory to search for mp3 files')

args = parser.parse_args()

if args.dir is None:
    parser.print_help()
    sys.exit(0)

if args.dir[0] is None or not os.path.isdir(args.dir[0]):
    print('Directory "%s" not found.' % args.dir[0])
    sys.exit(1)

directory = args.dir[0]


def parse_single_song(href):
    time.sleep(random.randint(1, 9))

    resp = requests.get(url=href, headers=headers,)
    soup = BeautifulSoup(resp.text, "html.parser")
    parsed_lyrics = soup.find("div", class_="col-xs-12 col-lg-8 text-center").contents[16].get_text()

    return parsed_lyrics


def parse_azlyrics(html, artist, title):
    soup = BeautifulSoup(html, "html.parser" )
    found_td = soup.find("td", class_="text-left")

    href = None
    if found_td is not None:
        try:
            found_artist_name = found_td.find_all('b')[1].text.lower()
            found_title = found_td.find('b').text.lower()
        except IndexError as e:
            print('Whatever man, I gave up years ago:', e)
            return '...'

        if artist == found_artist_name or title == found_title:
            href = found_td.find('a')['href']
        else:
            print('Wrong lyrics found:', artist, ' vs ', found_artist_name, ' skipping')
            return '...'
    else:
        print('Lyrics not found on site :(')
        return '...'

    print('href:', href)

    try:
        parsed_lyrics = parse_single_song(href)
    except Exception as e:
        print('not found:', e)
        return '...'

    print('parsed lyrics!')
    return parsed_lyrics


def get_lyrics(artist, title):
    url = search_url + artist + ' ' + title

    time.sleep(1)

    resp = requests.get(url=url, headers=headers, )
    parsed_lyrics = parse_azlyrics(resp.text, artist=artist, title=title)

    return parsed_lyrics


for dir_path, dirs, files in os.walk(directory):
    path = dir_path.split(os.sep)
    for file in files:
        ext = os.path.splitext(file)[-1].lower()
        if ext == ".mp3":
            file_path = os.path.join(dir_path, file)

            audiofile = taglib.File(file_path)
            old_lyrics = audiofile.tags.get('LYRICS', [''])[0]

            if (old_lyrics is not None and len(old_lyrics) > 10) or old_lyrics == '...':
                print('lyrics found in mp3 file: ', file_path, ' skipping')
                continue
            try:
                search_artist = audiofile.tags['ARTIST'][0].lower()
                search_title = audiofile.tags['TITLE'][0].lower()
            except KeyError:
                print('no artist or title in mp3 file')
                continue

            lyrics = get_lyrics(artist=search_artist, title=search_title)
            if lyrics is not None:
                audiofile.tags['LYRICS'] = lyrics
                audiofile.save()
