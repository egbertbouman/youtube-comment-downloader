import argparse
import io
import json
import os
import sys
import time

import re
import requests

"""
Written by egbertbouman (https://github.com/egbertbouman/youtube-comment-downloader)
Supplementary code by DrDayoX (https://github.com/DrDayoX)
"""

YOUTUBE_VIDEO_URL = 'https://www.youtube.com/watch?v={youtube_id}'

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'

SORT_BY_POPULAR = 0
SORT_BY_RECENT = 1

HEART_EITHER = -1
HEART_FALSE = 0
HEART_TRUE = 1

DEFAULT_NUMBER_OF_THREADS = 10

HEAD = [
    "_____.___.___________ _________                                       __    ________                      .__                    .___            ",
    "\__  |   |\__    ___/ \_   ___ \  ____   _____   _____   ____   _____/  |_  \______ \   ______  _  ______ |  |   _________     __| _/___________ ",
    " /   |   |  |    |    /    \  \/ /  _ \ /     \ /     \_/ __ \ /    \   __\  |    |  \ /  _ \ \/ \/ /    \|  |  /  _ \__  \   / __ |/ __ \_  __ \\",
    " \____   |  |    |    \     \___(  <_> )  Y Y  \  Y Y  \  ___/|   |  \  |    |    `   (  <_> )     /   |  \  |_(  <_> ) __ \_/ /_/ \  ___/|  | \/",
    " / ______|  |____|     \______  /\____/|__|_|  /__|_|  /\___  >___|  /__|   /_______  /\____/ \/\_/|___|  /____/\____(____  /\____ |\___  >__|   ",
    " \/                           \/             \/      \/     \/     \/               \/                  \/                \/      \/    \/       "
]

YT_CFG_RE = r'ytcfg\.set\s*\(\s*({.+?})\s*\)\s*;'
YT_INITIAL_DATA_RE = r'(?:window\s*\[\s*["\']ytInitialData["\']\s*\]|ytInitialData)\s*=\s*({.+?})\s*;\s*(?:var\s+meta|</script|\n)'


def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\\r", "\\r\\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + ' ' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total:
        print()


def regex_search(text, pattern, group=1, default=None):
    match = re.search(pattern, text)
    return match.group(group) if match else default


def ajax_request(session, endpoint, ytcfg, retries=9, sleep=4):
    url = 'https://www.youtube.com' + endpoint['commandMetadata']['webCommandMetadata']['apiUrl']

    data = {'context': ytcfg['INNERTUBE_CONTEXT'],
            'continuation': endpoint['continuationCommand']['token']}

    for _ in range(retries):
        response = session.post(url, params={'key': ytcfg['INNERTUBE_API_KEY']}, json=data)
        if response.status_code == 200:
            return response.json()
        if response.status_code in [403, 413]:
            return {}
        else:
            time.sleep(sleep)


def download_comments(youtube_id, sort_by=SORT_BY_RECENT, language=None, sleep=.1):
    session = requests.Session()
    session.headers['User-Agent'] = USER_AGENT

    response = session.get(YOUTUBE_VIDEO_URL.format(youtube_id=youtube_id))

    if 'uxe=' in response.request.url:
        session.cookies.set('CONSENT', 'YES+cb', domain='.youtube.com')
        response = session.get(YOUTUBE_VIDEO_URL.format(youtube_id=youtube_id))

    html = response.text
    ytcfg = json.loads(regex_search(html, YT_CFG_RE, default=''))
    if not ytcfg:
        return  # Unable to extract configuration
    if language:
        ytcfg['INNERTUBE_CONTEXT']['client']['hl'] = language

    data = json.loads(regex_search(html, YT_INITIAL_DATA_RE, default=''))

    section = next(search_dict(data, 'itemSectionRenderer'), None)
    renderer = next(search_dict(section, 'continuationItemRenderer'), None) if section else None
    if not renderer:
        # Comments disabled?
        return

    needs_sorting = sort_by != SORT_BY_POPULAR
    continuations = [renderer['continuationEndpoint']]

    #THREAD THIS
    #def download_function():
    c = 0
    while continuations:


        continuation = continuations.pop()

        response = ajax_request(session, continuation, ytcfg)

        if not response:
            break
        if list(search_dict(response, 'externalErrorMessage')):
            raise RuntimeError('Error returned from server: ' + next(search_dict(response, 'externalErrorMessage')))

        if needs_sorting:
            sort_menu = next(search_dict(response, 'sortFilterSubMenuRenderer'), {}).get('subMenuItems', [])
            if sort_by < len(sort_menu):
                continuations = [sort_menu[sort_by]['serviceEndpoint']]
                needs_sorting = False
                continue
            raise RuntimeError('Failed to set sorting')

        actions = list(search_dict(response, 'reloadContinuationItemsCommand')) + \
                list(search_dict(response, 'appendContinuationItemsAction'))
        for action in actions:
            for item in action.get('continuationItems', []):
                if action['targetId'] == 'comments-section':
                    # Process continuations for comments and replies.
                    continuations[:0] = [ep for ep in search_dict(item, 'continuationEndpoint')]
                if action['targetId'].startswith('comment-replies-item') and 'continuationItemRenderer' in item:
                    # Process the 'Show more replies' button
                    continuations.append(next(search_dict(item, 'buttonRenderer'))['command']) 
        for comment in reversed(list(search_dict(response, 'commentRenderer'))):
            yield  {'cid': comment['commentId'],
                'text': ''.join([c['text'] for c in comment['contentText'].get('runs', [])]),
                'time': comment['publishedTimeText']['runs'][0]['text'],
                'author': comment.get('authorText', {}).get('simpleText', ''),
                'channel': comment['authorEndpoint']['browseEndpoint'].get('browseId', ''),
                'votes': comment.get('voteCount', {}).get('simpleText', '0'),
                'photo': comment['authorThumbnail']['thumbnails'][-1]['url'],
                'heart': next(search_dict(comment, 'isHearted'), False)}

        #time.sleep(sleep)



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

def heart_parser(a: int, heart: bool) -> bool:
    """Parses the integer and returns a bool
    based on the three heart_[] constants"""
    if a == HEART_EITHER: return heart
    elif a == HEART_TRUE: return True
    elif a == HEART_FALSE: return False
    else: raise RuntimeError(f"heart_parser {a} does not equal to either of the three constants")


def main(argv=None):
    parser = argparse.ArgumentParser(add_help=False,
                                     description=('Download Youtube comments without using the Youtube API'))

    #DEFAULT ARGUMENTS
    parser.add_argument('--help', '-h', action='help', default=argparse.SUPPRESS,
                        help='Show this help message and exit')
    parser.add_argument('youtubeid', help='ID of Youtube video for which to download the comments')
    parser.add_argument('--output', '-o', metavar="str", help='Output filename (output format is line delimited JSON)')
    parser.add_argument('--limit', '-l', metavar="int", default= -1, type=int, help='Limit the number of comments')
    parser.add_argument('--language', type=str, metavar="str", default=None,
                        help='Language for Youtube generated text (e.g. en)')
    parser.add_argument('--sort', '-s', metavar="int", type=int, default=SORT_BY_RECENT,
                        help='Whether to download popular (0) or recent comments (1). Defaults to 1')

    #OBSOLETE ARGUMENTS
    #parser.add_argument("--thread", "-t", type=int, metavar="int", default=DEFAULT_NUMBER_OF_THREADS, help=f"Set the amount of threads that download and write at the same time. (Default {DEFAULT_NUMBER_OF_THREADS})")
    #parser.add_argument("--mode", "-M", type=str, metavar="str", default="w", help="Set the writing mode of the download file. (r and r+ not allowed, default: w)")

    #SELECTORS
    parser.add_argument("--heart", "-H", type=int, metavar="int", default=HEART_EITHER, help=f"If set {HEART_TRUE}, only saves comment with hearts, if {HEART_FALSE} it saves comments only without a heart. Default: {HEART_EITHER} (Saves all).")

    author_specification = parser.add_mutually_exclusive_group()
    author_specification.add_argument("--author", "-a", type=str, metavar="str", default=None, help="Only saves the comment if the author's name matches the given string")
    author_specification.add_argument("--authorincl","-aI", metavar="str", type=str, default=None, help="Only saves the comment if the author's name contains the string")
    author_specification.add_argument("--authorexcl","-aE", metavar="str", type=str, default=None, help="Only saves the comment if the author's name not contains the string")
    author_specification.add_argument("--authorexclmatch","-aEM", metavar="str", type=str, default=None, help="Only saves the comment if the author's name not matches the string")

    comment_specification = parser.add_mutually_exclusive_group()
    comment_specification.add_argument("--comment","-c", metavar="str", type=str, default=None, help="Only saves the comment if the comment matches the given string")
    comment_specification.add_argument("--commentincl", "-cI", metavar="str", type=str, default=None, help="Only saves the comment if the comment contains the given string")
    comment_specification.add_argument("--commentexcl","-cE", metavar="str", type=str, default=None, help="Only saves the comment if the comment not contains the given string")
    comment_specification.add_argument("--commentexclmatch","-cEM", metavar="str", type=str, default=None, help="Only saves the comment if the comment not matches the given string")

    parser.add_argument("--minlikes", "-minL", type=int, metavar="int", default=0, help="Sets the minimum like requirement for the comment (inclusive)")
    parser.add_argument("--maxlikes","-maxL", type=int, metavar="int", default=-1, help="Sets the maximum amount of likes a comment can have (inclusive)")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--verbose", "-v", action="store_true", help="Prints all actions made by the program")
    group.add_argument("--quiet", "-q", action="store_true", help="Prints only the critical events while running the program")
    parser.add_argument("--presearch", action="store_true", help="If selected the program will check for specifics while downloading, and saves only comments that match the specifications. By default it searches trough the comments after all have been downloaded. Use only if you are sure, you'll find what you are looking for!")
    parser.add_argument("--format", action="store_true", help="If selected, the program will format the document to be a json list for other usage. Requires more RAM if you have downloaded more comments.")

    args = parser.parse_args() if argv is None else parser.parse_args(argv)



    print("-==#" + "="*(len(HEAD[0]) - 6) + "#==-")
    for head_line in HEAD:
        print(" "+ head_line)
    print("-==#" + "="*(len(HEAD[0]) - 6) + "#==-")
    print()

    youtube_id = args.youtubeid
    output = args.output
    limit = args.limit

    heart = args.heart

    if args.authorincl: author = args.authorincl
    elif args.authorexcl: author = args.authorexcl
    elif args.authorexclmatch: author = args.authorexclmatch
    else: author = args.author

    if args.commentincl: text = args.commentincl
    elif args.commentexcl: text = args.commentexcl
    elif args.commentexclmatch: text = args.commentexclmatch
    else: text = args.comment

    minlikes = int(args.minlikes)
    maxlikes = int(args.maxlikes)

    if maxlikes != -1 and minlikes >= maxlikes:
        raise Exception("The minimum amount of likes can't be greater than the amount of maximum likes")

    if not output and args.presearch:
        output = f"{youtube_id}.comments"
    elif not output and not args.presearch:
        output = youtube_id
    else:
        output = args.output

    if os.path.sep in output:
        outdir = os.path.dirname(output)
        if not os.path.exists(outdir):
            os.makedirs(outdir)

    print('\nDownloading Youtube comments for video:', youtube_id)
    count = 0
    presearch_founds = 0
    with io.open(output, 'w', encoding='utf8') as fp:

        def downloading_thread():
            pass

        #sys.stdout.write('Downloaded %d comment(s)\r' % count)
        #sys.stdout.flush()

        start_time = time.time()
        count_in_second = 0
        for comment in download_comments(youtube_id, args.sort, args.language):
            comment_str = json.dumps(comment, ensure_ascii=False)
            count += 1
            if args.presearch:

                if limit != -1 and count + 1 >= limit:
                    break

                if not args.quiet and limit != -1:
                    printProgressBar(count, limit, prefix='Progress:', suffix=f"Matched {presearch_founds}/{count} comment(s)",
                                        length=50)
                elif args.quiet:
                    print(f"Progress: {count}/{limit}, and found {presearch_founds}", end="\r")
                elif limit == -1:
                    print(f"Downloaded {count} and found {presearch_founds} comment(s)...", end="\r")

                if author != None:
                    if args.author != None and author != comment["author"]: continue
                    elif args.authorincl != None and author not in comment["author"]: continue
                    elif args.authorexcl != None and author in comment["author"]: continue
                    elif args.authorexclmatch != None and author == comment["author"]: continue

                if text != None:
                    if args.comment != None and text != comment["text"]: continue
                    elif args.commentincl != None and text not in comment["text"]: continue
                    elif args.commentexcl != None and text in comment["text"]: continue
                    elif args.commentexclmatch != None and text == comment["text"]: continue

                if heart != HEART_EITHER:
                    if heart == HEART_TRUE and not comment["heart"]: continue
                    elif heart == HEART_FALSE and comment["heart"]: continue

                try:
                    if maxlikes != -1 and not (minlikes <= int(comment["votes"]) <= maxlikes): continue
                    elif maxlikes == -1 and not (minlikes <= int(comment["votes"])): continue
                except ValueError:
                    if not args.quiet:
                        print(f"[WARNING] Iteration {count}'s like count is greater than 999 ({comment['votes']})")

                print(comment_str.decode('utf-8') if isinstance(comment_str, bytes) else comment_str, file=fp)

                presearch_founds += 1
            else:
                print(comment_str.decode('utf-8') if isinstance(comment_str, bytes) else comment_str, file=fp)
                if not args.quiet and limit != -1:
                    printProgressBar(count, limit, prefix='Progress:', suffix='Downloaded ' + str(count) + ' comment(s)',
                                        length=50)
                elif args.quiet:
                    print(f"Progress: {count}/{limit}", end="\r")
                elif limit == -1:
                    print(f"Downloaded {count} comment(s)...", end="\r")

                if limit != -1 and count >= limit:
                    break
            # else:
            #     print(comment)
            #     if limit != -1 and count >= limit:
            #         break

    if args.verbose: print('Done in {:.2f} seconds\n'.format(time.time() - start_time))
    elif args.quiet: print(f"Progress: {count}/{limit}...Done!")
    else: print('Done! [{:.2f} seconds]\n'.format(time.time() - start_time))

    if not args.presearch:
        start_time = time.time()
        print("Starting filtering", end= "..." if args.quiet else "\n")
        if not args.quiet:
            if author != None: print(f"[AUTHOR] {author}")
            if args.verbose:
                if args.author != None: print(f"[AUTHOR SETTING] author match")
                elif args.authorincl != None: print(f"[AUTHOR SETTING] author inclusive")
                elif args.authorexcl != None: print(f"[AUTHOR SETTING] author exclusive")
                elif args.authorexclmatch != None: print(f"[AUTHOR SETTING] author exclusive match")

            if text != None: print(f"[TEXT] {author}")
            if args.verbose:
                if args.comment != None: print(f"[TEXT SETTING] text match")
                elif args.commentincl != None: print(f"[TEXT SETTING] text inclusive")
                elif args.commentexcl != None: print(f"[TEXT SETTING] text exclusive")
                elif args.commentexclmatch != None: print(f"[TEXT SETTING] text exclusive match")

            if heart == HEART_EITHER: print("[HEART] All")
            else: print(f"[HEART] {str(heart).upper()}")

            print(f"[MINLIKES] {str(minlikes)}")
            print(f"[MAXLIKES] {str(maxlikes) if maxlikes != -1 else 'no limit'}")

        with open(output, "r", encoding="utf8") as fp:
            if os.path.exists(output + ".comments"): os.remove(output + ".comments")
            with open(output + ".comments", "a", encoding="utf8") as ap:
                count = 0
                while True:
                    count += 1
                    line = fp.readline()
                    if not line: break
                    line_json = json.loads(line)

                    if author != None:
                        if args.author != None and author != line_json["author"]: continue
                        elif args.authorincl != None and author not in line_json["author"]: continue
                        elif args.authorexcl != None and author in line_json["author"]: continue
                        elif args.authorexclmatch != None and author == line_json["author"]: continue

                    if text != None:
                        if args.comment != None and text != line_json["text"]: continue
                        elif args.commentincl != None and text not in line_json["text"]: continue
                        elif args.commentexcl != None and text in line_json["text"]: continue
                        elif args.commentexclmatch != None and text == line_json["text"]: continue

                    if heart != HEART_EITHER:
                        if heart == HEART_TRUE and not line_json["heart"]: continue
                        elif heart == HEART_FALSE and line_json["heart"]: continue

                    try:
                        if maxlikes != -1 and not (minlikes <= int(line_json["votes"]) <= maxlikes): continue
                        elif maxlikes == -1 and not (minlikes <= int(line_json["votes"])): continue
                    except ValueError:
                        if not args.quiet:
                            print(f"[WARNING] Iteration {count}'s like count is greater than 999 ({line_json['votes']})")

                    if args.verbose:
                        print(f"[ITERATION] {count} | Adding line...")
                    ap.write(line)
        if os.path.exists(output) and not args.presearch:
            os.remove(output)
        if args.verbose: print('Done in {:.2f} seconds\n'.format(time.time() - start_time))
        elif args.quiet: print("Done!")
        else: print('Done! [{:.2f} seconds]\n'.format(time.time() - start_time))



    # TODO ÜRES SOR ERROR MEGOLDÁSA
    if args.format:
        print("Formatting to json", end= "..." if args.quiet else "\n")
        if not args.quiet: print('Reading and converting the data...', end= "\n" if args.verbose else "")
        data = []
        if args.verbose: printProgressBar(0, limit, prefix='Progress:', suffix='Converting ' + str(0) + ' line(s)', length=50)
        start_time = time.time()
        with open(f"{output}.comments", 'r', encoding='utf8') as r:
            c = 0
            while True:
                line = r.readline()
                if not line: break
                data.append(json.loads(line))
                c += 1
                if args.verbose:
                    printProgressBar(c, limit, prefix='Progress:', suffix='Converting ' + str(c) + ' line(s)',
                                    length=50)
        if args.verbose: print('Done in {:.2f} seconds\n'.format(time.time() - start_time))
        elif not args.quiet: print('Done! [{:.2f} seconds]'.format(time.time() - start_time))

        if not args.quiet: print('Writing and saving the data...',  end= "\n" if args.verbose else "")
        if args.verbose: printProgressBar(0, 1, prefix='Progress:', suffix='Writing line ' + str(0), length=50)
        start_time = time.time()
        json_data = json.dumps(data, indent= 4)
        with open(f"{output}.comments", 'w', encoding='utf8') as r:
            r.write(json_data)
            if args.verbose:
                printProgressBar(1, 1, prefix='Progress:', suffix='Writing line ' + str(c),
                                length=50)

        if args.verbose: print('Done in {:.2f} seconds\n'.format(time.time() - start_time))
        elif args.quiet: print("Done!")
        else: print('Done! [{:.2f} seconds]'.format(time.time() - start_time))

        print()

if __name__ == "__main__":
    main(sys.argv[1:])
