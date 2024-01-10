import argparse
import io
import json
import os
import sys
import time
from tqdm import tqdm

from .downloader import YoutubeCommentDownloader, SORT_BY_POPULAR, SORT_BY_RECENT

def main(argv = None):
    parser = argparse.ArgumentParser(add_help=False, description=('Download Youtube comments without using the Youtube API'))
    parser.add_argument('--help', '-h', action='help', default=argparse.SUPPRESS, help='Show this help message and exit')
    parser.add_argument('--youtubeid', '-y', help='ID of Youtube video for which to download the comments')
    parser.add_argument('--url', '-u', help='Youtube URL for which to download the comments')
    parser.add_argument('--output', '-o', help='Output filename (output format is line delimited JSON)')
    parser.add_argument('--limit', '-l', type=int, help='Limit the number of comments')
    parser.add_argument('--language', '-a', type=str, default="en", help='Language for Youtube generated text. Defaults to en.')
    parser.add_argument('--sort', '-s', type=int, default=SORT_BY_RECENT,
                        help='Whether to download popular (0) or recent comments (1). Defaults to 1')
    parser.add_argument('--template', '-t', default=None, type=str, help='Formatting template using the jsonl fields, e.g., "{author} wrote {time}: {text}". Defaults to None, which outputs the raw JSON.')
    parser.add_argument('--quote', '-q', type=bool, default=False, help="enclose values in quotes when filling template. Defaults to False.")
    parser.add_argument('--min-length', '-m', default=None, type=int, help="include only comments of a certain minimum length. Defaults to None, i.e., include all comments.")

    try:
        args = parser.parse_args() if argv is None else parser.parse_args(argv)

        youtube_id = args.youtubeid
        youtube_url = args.url
        output = args.output
        limit = args.limit

        if (not youtube_id and not youtube_url) or not output:
            parser.print_usage(file=sys.stderr)
            raise ValueError('you need to specify a Youtube ID/URL and an output filename')

        if os.sep in output:
            outdir = os.path.dirname(output)
            if not os.path.exists(outdir):
                os.makedirs(outdir)

        print('Downloading Youtube comments for', youtube_id or youtube_url, file=sys.stderr)
        downloader = YoutubeCommentDownloader()
        comment_count = (
            downloader.get_count(youtube_id)
            if youtube_id
            else downloader.get_count_from_url(youtube_url)
        )
        total = min(limit, comment_count) if limit else comment_count
        generator = (
            downloader.get_comments(youtube_id, args.sort, args.language)
            if youtube_id
            else downloader.get_comments_from_url(youtube_url, args.sort, args.language)
        )

        if args.template is not None:
            args.template = eval(f"'{args.template}'")
        count = 0
        start_time = time.time()
        with io.open(output, 'w', encoding='utf8') as fp:
            for comment in tqdm(generator, total=total):
                if args.min_length is not None and len(comment['text']) < args.min_length:
                    continue
                comment_str = (
                    json.dumps(comment, ensure_ascii=False, indent=None)
                    if args.template is None
                    else args.template.format(**{k:repr(v) if args.quote else v for k, v in comment.items()})
                )
                if limit and count >= limit:
                    break
                comment_str = comment_str.decode('utf-8') if isinstance(comment_str, bytes) else comment_str
                print(comment_str, file=fp)
                count += 1
            print(f"{count} comments of {'any' if args.min_length is None else args.min_length} length", file=fp)
        print('\n[{:.2f} seconds] Done!'.format(time.time() - start_time), file=sys.stderr)

    except Exception as e:
        print('Error:', str(e), file=sys.stderr)
        sys.exit(1)
