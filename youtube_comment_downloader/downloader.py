#!/usr/bin/env python

from __future__ import print_function

import argparse
import io
import json
import os
import re
import sys
import time

import dateparser
import requests

YOUTUBE_VIDEO_URL = 'https://www.youtube.com/watch?v={youtube_id}'

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'

SORT_BY_POPULAR = 0
SORT_BY_RECENT = 1

YT_CFG_RE = r'ytcfg\.set\s*\(\s*({.+?})\s*\)\s*;'
YT_INITIAL_DATA_RE = r'(?:window\s*\[\s*["\']ytInitialData["\']\s*\]|ytInitialData)\s*=\s*({.+?})\s*;\s*(?:var\s+meta|</script|\n)'


class YoutubeCommentDownloader:

    def __init__(self):
        self.session = requests.Session()
        self.session.headers['User-Agent'] = USER_AGENT

    def ajax_request(self, endpoint, ytcfg, retries=5, sleep=20):
        url = 'https://www.youtube.com' + endpoint['commandMetadata']['webCommandMetadata']['apiUrl']

        data = {'context': ytcfg['INNERTUBE_CONTEXT'],
                'continuation': endpoint['continuationCommand']['token']}

        for _ in range(retries):
            response = self.session.post(url, params={'key': ytcfg['INNERTUBE_API_KEY']}, json=data)
            if response.status_code == 200:
                return response.json()
            if response.status_code in [403, 413]:
                return {}
            else:
                time.sleep(sleep)

    def get_comments(self, youtube_id, sort_by=SORT_BY_RECENT, language=None, sleep=.1):
        response = self.session.get(YOUTUBE_VIDEO_URL.format(youtube_id=youtube_id))

        if 'uxe=' in response.request.url:
            self.session.cookies.set('CONSENT', 'YES+cb', domain='.youtube.com')
            response = self.session.get(YOUTUBE_VIDEO_URL.format(youtube_id=youtube_id))

        html = response.text
        ytcfg = json.loads(self.regex_search(html, YT_CFG_RE, default=''))
        if not ytcfg:
            return # Unable to extract configuration
        if language:
            ytcfg['INNERTUBE_CONTEXT']['client']['hl'] = language

        data = json.loads(self.regex_search(html, YT_INITIAL_DATA_RE, default=''))

        section = next(self.search_dict(data, 'itemSectionRenderer'), None)
        renderer = next(self.search_dict(section, 'continuationItemRenderer'), None) if section else None
        if not renderer:
            # Comments disabled?
            return

        needs_sorting = sort_by != SORT_BY_POPULAR
        continuations = [renderer['continuationEndpoint']]
        while continuations:
            continuation = continuations.pop()
            response = self.ajax_request(continuation, ytcfg)

            if not response:
                break

            error = next(self.search_dict(response, 'externalErrorMessage'), None)
            if error:
                raise RuntimeError('Error returned from server: ' + error)

            if needs_sorting:
                sort_menu = next(self.search_dict(response, 'sortFilterSubMenuRenderer'), {}).get('subMenuItems', [])
                if sort_by < len(sort_menu):
                    continuations = [sort_menu[sort_by]['serviceEndpoint']]
                    needs_sorting = False
                    continue
                raise RuntimeError('Failed to set sorting')

            actions = list(self.search_dict(response, 'reloadContinuationItemsCommand')) + \
                      list(self.search_dict(response, 'appendContinuationItemsAction'))
            for action in actions:
                for item in action.get('continuationItems', []):
                    if action['targetId'] == 'comments-section':
                        # Process continuations for comments and replies.
                        continuations[:0] = [ep for ep in self.search_dict(item, 'continuationEndpoint')]
                    if action['targetId'].startswith('comment-replies-item') and 'continuationItemRenderer' in item:
                        # Process the 'Show more replies' button
                        continuations.append(next(self.search_dict(item, 'buttonRenderer'))['command'])

            for comment in reversed(list(self.search_dict(response, 'commentRenderer'))):
                time_text = comment['publishedTimeText']['runs'][0]['text']
                time_parsed = dateparser.parse(time_text.split('(')[0].strip()).timestamp()
                yield {'cid': comment['commentId'],
                       'text': ''.join([c['text'] for c in comment['contentText'].get('runs', [])]),
                       'time': time_text,
                       'time_parsed': time_parsed,
                       'author': comment.get('authorText', {}).get('simpleText', ''),
                       'channel': comment['authorEndpoint']['browseEndpoint'].get('browseId', ''),
                       'votes': comment.get('voteCount', {}).get('simpleText', '0'),
                       'photo': comment['authorThumbnail']['thumbnails'][-1]['url'],
                       'heart': next(self.search_dict(comment, 'isHearted'), False)}

            time.sleep(sleep)

    @staticmethod
    def regex_search(text, pattern, group=1, default=None):
        match = re.search(pattern, text)
        return match.group(group) if match else default

    @staticmethod
    def search_dict(partial, search_key):
        stack = [partial]
        while stack:
            current_item = stack.pop()
            if isinstance(current_item, dict):
                for key, value in current_item.items():
                    if key == search_key:
                        yield value
                    else:
                        stack.append(value)
            elif isinstance(current_item, list):
                for value in current_item:
                    stack.append(value)


def main(argv = None):
    parser = argparse.ArgumentParser(add_help=False, description=('Download Youtube comments without using the Youtube API'))
    parser.add_argument('--help', '-h', action='help', default=argparse.SUPPRESS, help='Show this help message and exit')
    parser.add_argument('--youtubeid', '-y', help='ID of Youtube video for which to download the comments')
    parser.add_argument('--output', '-o', help='Output filename (output format is line delimited JSON)')
    parser.add_argument('--limit', '-l', type=int, help='Limit the number of comments')
    parser.add_argument('--language', '-a', type=str, default=None, help='Language for Youtube generated text (e.g. en)')
    parser.add_argument('--sort', '-s', type=int, default=SORT_BY_RECENT,
                        help='Whether to download popular (0) or recent comments (1). Defaults to 1')

    try:
        args = parser.parse_args() if argv is None else parser.parse_args(argv)

        youtube_id = args.youtubeid
        output = args.output
        limit = args.limit

        if not youtube_id or not output:
            parser.print_usage()
            raise ValueError('you need to specify a Youtube ID and an output filename')

        if os.sep in output:
            outdir = os.path.dirname(output)
            if not os.path.exists(outdir):
                os.makedirs(outdir)

        print('Downloading Youtube comments for video:', youtube_id)
        downloader = YoutubeCommentDownloader()
        count = 0
        with io.open(output, 'w', encoding='utf8') as fp:
            sys.stdout.write('Downloaded %d comment(s)\r' % count)
            sys.stdout.flush()
            start_time = time.time()
            for comment in downloader.get_comments(youtube_id, args.sort, args.language):
                comment_json = json.dumps(comment, ensure_ascii=False)
                print(comment_json.decode('utf-8') if isinstance(comment_json, bytes) else comment_json, file=fp)
                count += 1
                sys.stdout.write('Downloaded %d comment(s)\r' % count)
                sys.stdout.flush()
                if limit and count >= limit:
                    break
        print('\n[{:.2f} seconds] Done!'.format(time.time() - start_time))

    except Exception as e:
        print('Error:', str(e))
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
