import argparse
import io
import json
import os
import sys
import time

from .downloader import YoutubeCommentDownloader, SORT_BY_POPULAR, SORT_BY_RECENT

INDENT = 4


def to_json(comment, indent=None):
    comment_str = json.dumps(comment, ensure_ascii=False, indent=indent)
    if indent is None:
        return comment_str
    padding = ' ' * (2 * indent) if indent else ''
    return ''.join(padding + line for line in comment_str.splitlines(True))


def main(argv = None):
    parser = argparse.ArgumentParser(add_help=False, description=('Download Youtube comments without using the Youtube API'))
    parser.add_argument('--help', '-h', action='help', default=argparse.SUPPRESS, help='Show this help message and exit')
    parser.add_argument('--youtubeid', '-y', help='ID of Youtube video for which to download the comments')
    parser.add_argument('--url', '-u', help='Youtube URL for which to download the comments')
    parser.add_argument('--output', '-o', help='Output filename (output format is line delimited JSON)')
    parser.add_argument('--pretty', '-p', action='store_true', help='Change the output format to indented JSON')
    parser.add_argument('--limit', '-l', type=int, help='Limit the number of comments')
    parser.add_argument('--language', '-a', type=str, default=None, help='Language for Youtube generated text (e.g. en)')
    parser.add_argument('--sort', '-s', type=int, default=SORT_BY_RECENT,
                        help='Whether to download popular (0) or recent comments (1). Defaults to 1')

    try:
        args = parser.parse_args() if argv is None else parser.parse_args(argv)

        youtube_id = args.youtubeid
        youtube_url = args.url
        output = args.output
        limit = args.limit
        pretty = args.pretty

        if (not youtube_id and not youtube_url) or not output:
            parser.print_usage()
            raise ValueError('you need to specify a Youtube ID/URL and an output filename')

        if os.sep in output:
            outdir = os.path.dirname(output)
            if not os.path.exists(outdir):
                os.makedirs(outdir)

        print('Downloading Youtube comments for', youtube_id or youtube_url)
        downloader = YoutubeCommentDownloader()
        generator = (
            downloader.get_comments(youtube_id, args.sort, args.language)
            if youtube_id
            else downloader.get_comments_from_url(youtube_url, args.sort, args.language)
        )

        count = 1
        with io.open(output, 'w', encoding='utf8') as fp:
            sys.stdout.write('Downloaded %d comment(s)\r' % count)
            sys.stdout.flush()
            start_time = time.time()

            if pretty:
                fp.write('{\n' + ' ' * INDENT + '"comments": [\n')

            comment = next(generator, None)
            while comment:
                comment_str = to_json(comment, indent=INDENT if pretty else None)
                comment = None if limit and count >= limit else next(generator, None)  # Note that this is the next comment
                comment_str = comment_str + ',' if pretty and comment is not None else comment_str
                print(comment_str.decode('utf-8') if isinstance(comment_str, bytes) else comment_str, file=fp)
                sys.stdout.write('Downloaded %d comment(s)\r' % count)
                sys.stdout.flush()
                count += 1

            if pretty:
                fp.write(' ' * INDENT +']\n}')
        print('\n[{:.2f} seconds] Done!'.format(time.time() - start_time))

    except Exception as e:
        print('Error:', str(e))
        sys.exit(1)
