import argparse

from lyrics2mp3.api import Lyrics2MP3

"""
Lyrics2mp3
1. Scans directory or playlist for music files.
2. Searches lyrics for each song on azlyrics.com
3. If 'write_on_not_found', inserts lyrics into music file, or '...' if not found
"""


def generate_args():
    parser = argparse.ArgumentParser(
        description="lyrics2mp3: Find lyrics and add them into music files"
    )
    parser._action_groups.pop()

    optional = parser.add_argument_group("optional arguments")
    file_source = parser.add_mutually_exclusive_group(required=True)

    file_source.add_argument("--dir", help="Directory to search for music files")
    file_source.add_argument("--m3u", help="Playlist to search for music files")

    optional.add_argument(
        "--genius_token",
        help="API token for genius.com music database. Without this token Genius will not be used. Sign up for token at https://genius.com/api-clients",
    )
    optional.add_argument(
        "--write_on_not_found",
        action="store_true",
        help="Write '...' on files with no lyrics found.",
    )
    optional.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing lyrics in music files",
    )
    optional.add_argument(
        "--ignore_artist",
        action="store_true",
        help="Ignore files' artists, look at song name only",
    )
    optional.add_argument(
        "--manually_confirm",
        action="store_true",
        help="Manually confirm any lyrics changes",
    )
    optional.add_argument(
        "--simulate",
        "-s",
        action="store_true",
        help="Simulate retrieval but change no files",
    )
    optional.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Level of debug info to display",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = generate_args()

    l2m = Lyrics2MP3(
        verbose=args.verbose,
        manually_confirm=args.manually_confirm,
        write_on_not_found=args.write_on_not_found,
        overwrite=args.overwrite,
        lg_token=args.genius_token,
    )

    try:
        if args.dir:
            l2m.get_lyrics_from_dir(
                args.dir, ignore_artist=args.ignore_artist, simulate=args.simulate
            )

        elif args.m3u:
            l2m.get_lyrics_from_m3u(
                args.m3u, ignore_artist=args.ignore_artist, simulate=args.simulate
            )

    except KeyboardInterrupt:
        pass

    l2m.print_summary()
