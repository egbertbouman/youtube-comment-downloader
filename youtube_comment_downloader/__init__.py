import argparse
import csv
import io
import json
import os
import sys
import time

from .downloader import YoutubeCommentDownloader, SORT_BY_POPULAR, SORT_BY_RECENT

JSON_INDENT = 4

CSV_FIELDS = [
    'cid', 'text', 'time', 'author', 'channel',
    'votes', 'replies', 'photo', 'heart', 'reply', 'time_parsed'
]


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
    parser.add_argument('--json', metavar='OUTPUT', help='Write comments as JSON')
    parser.add_argument('--csv', metavar='OUTPUT', help='Write comments as CSV')
    parser.add_argument('--output', '-o', help='Deprecated alias for --json')
    parser.add_argument('--pretty', '-p', action='store_true', help='Pretty-print JSON output')
    parser.add_argument('--limit', '-l', type=int, help='Limit the number of comments')
    parser.add_argument('--language', '-a', type=str, default=None, help='Language for Youtube generated text (e.g. en)')
    parser.add_argument('--sort', '-s', type=int, default=SORT_BY_RECENT,
                        help='Whether to download popular (0) or recent comments (1). Defaults to 1')

    try:
        args = parser.parse_args() if argv is None else parser.parse_args(argv)

        youtube_id = args.youtubeid
        youtube_url = args.url
        limit = args.limit
        pretty = args.pretty

        if args.output:
            print('Warning: --output is deprecated, use --json instead', file=sys.stderr)
            if args.json:
                raise ValueError('Do not combine --output with --json')
            args.json = args.output

        if (not youtube_id and not youtube_url) or (not args.json and not args.csv):
            parser.print_usage()
            raise ValueError('you need to specify a Youtube ID/URL and at least one output target')

        if args.json and os.sep in args.json:
            outdir = os.path.dirname(args.json)
            if not os.path.exists(outdir):
                os.makedirs(outdir)

        if args.csv and os.sep in args.csv:
            outdir = os.path.dirname(args.csv)
            if not os.path.exists(outdir):
                os.makedirs(outdir)

        print('Downloading Youtube comments for', youtube_id or youtube_url)
        downloader = YoutubeCommentDownloader()
        generator = (
            downloader.get_comments(youtube_id, args.sort, args.language)
            if youtube_id
            else downloader.get_comments_from_url(youtube_url, args.sort, args.language)
        )

        json_fp = None
        csv_fp = None
        csv_writer = None
        json_count = 0
        csv_count = 0
        start_time = time.time()
        comment = next(generator, None)

        while comment:
            if args.json and not json_fp:
                json_fp = io.open(args.json, 'w', encoding='utf8')
                if pretty:
                    json_fp.write('{\n' + ' ' * JSON_INDENT + '"comments": [\n')

            if args.csv and not csv_fp:
                csv_fp = io.open(args.csv, 'w', encoding='utf8', newline='')
                csv_writer = csv.DictWriter(csv_fp, fieldnames=CSV_FIELDS, extrasaction='ignore')
                csv_writer.writeheader()

            if args.json:
                comment_str = to_json(comment, indent=JSON_INDENT if pretty else None)
                next_comment = None if limit and json_count >= limit else next(generator, None)
                if pretty and next_comment is not None:
                    comment_str += ','
                print(comment_str, file=json_fp)
                json_count += 1

            if args.csv:
                row = {key: comment.get(key, '') for key in CSV_FIELDS}
                csv_writer.writerow(row)
                csv_count += 1

            if args.json:
                comment = next_comment
            else:
                comment = None if limit and csv_count >= limit else next(generator, None)

            sys.stdout.write('Downloaded %d comment(s)\r' % max(json_count, csv_count))
            sys.stdout.flush()

        if args.json and pretty and json_fp:
            json_fp.write(' ' * JSON_INDENT + ']\n}')
        if json_fp:
            json_fp.close()
        if csv_fp:
            csv_fp.close()

        done_count = max(json_count, csv_count)
        print('\n[{:.2f} seconds] Done!'.format(time.time() - start_time) if done_count else 'No comment available!')

    except Exception as e:
        print('Error:', str(e))
        sys.exit(1)
