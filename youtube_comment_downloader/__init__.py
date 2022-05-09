#Written by egbertbouman
#Forked by DrDayoX

import argparse
import io
import json
import os
import sys
import time
import pathlib

from .downloader import YoutubeCommentDownloader, SORT_BY_RECENT


def main(argv=None):
    
    HEART_EITHER = -1
    HEART_FALSE = 0
    HEART_TRUE = 1

    HEAD = [
        "_____.___.___________ _________                                       __    ________                      .__                    .___            ",
        "\__  |   |\__    ___/ \_   ___ \  ____   _____   _____   ____   _____/  |_  \______ \   ______  _  ______ |  |   _________     __| _/___________ ",
        " /   |   |  |    |    /    \  \/ /  _ \ /     \ /     \_/ __ \ /    \   __\  |    |  \ /  _ \ \/ \/ /    \|  |  /  _ \__  \   / __ |/ __ \_  __ \\",
        " \____   |  |    |    \     \___(  <_> )  Y Y  \  Y Y  \  ___/|   |  \  |    |    `   (  <_> )     /   |  \  |_(  <_> ) __ \_/ /_/ \  ___/|  | \/",
        " / ______|  |____|     \______  /\____/|__|_|  /__|_|  /\___  >___|  /__|   /_______  /\____/ \/\_/|___|  /____/\____(____  /\____ |\___  >__|   ",
        " \/                           \/             \/      \/     \/     \/               \/                  \/                \/      \/    \/       "
    ]
    
    def printProgressBar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█', printEnd="\r"):
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + ' ' * (length - filledLength)
        print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=printEnd)
        if iteration == total: print()
        
    parser = argparse.ArgumentParser(add_help=False, description=('Download Youtube comments without using the Youtube API'))

    # DEFAULT ARGUMENTS 
    parser.add_argument('--help', '-h', action='help', default=argparse.SUPPRESS, help='Show this help message and exit')
    parser.add_argument('youtubeid', nargs="?", help='ID of Youtube video for which to download the comments')
    parser.add_argument('--output', '-o', help='Output filename (output format is line delimited JSON)')
    parser.add_argument('--limit', '-l', default=-1,type=int, help='Limit the number of comments')
    parser.add_argument('--language', type=str, default=None, help='Language for Youtube generated text (e.g. en)')
    parser.add_argument('--sort', '-s', type=int, default=SORT_BY_RECENT, help='Whether to download popular (0) or recent comments (1). Defaults to 1')
    parser.add_argument('--url', '-u', help='Youtube URL for which to download the comments')
    parser.add_argument('--append',  help='Appends the new comments into an existing file. Raises an error if trying to append an empty file')

    # OBSOLETE ARGUMENTS
    #parser.add_argument("--thread", "-t", type=int, default=DEFAULT_NUMBER_OF_THREADS, help=f"Set the amount of threads that download and write at the same time. (Default {DEFAULT_NUMBER_OF_THREADS})")
    #parser.add_argument("--mode", "-M", type=str, default="w", help="Set the writing mode of the download file. (r and r+ not allowed, default: w)")

    # SELECTORS
    parser.add_argument("--heart", "-H", type=int, default=HEART_EITHER, help=f"If set {HEART_TRUE}, only saves comment with hearts, if {HEART_FALSE} it saves comments only without a heart. Default: {HEART_EITHER} (Saves all).")

    author_specification = parser.add_mutually_exclusive_group()
    author_specification.add_argument("--author", "--authormatch", "-a", "-aM", type=str, default=None, help="Only saves the comment if the author's name matches the given string")
    author_specification.add_argument("--authorincl", "-aI", type=str, default=None, help="Only saves the comment if the author's name contains the string")
    author_specification.add_argument("--authorexcl", "-aE", type=str, default=None, help="Only saves the comment if the author's name not contains the string")
    author_specification.add_argument("--authorexclmatch", "-aEM", type=str, default=None, help="Only saves the comment if the author's name not matches the string")

    comment_specification = parser.add_mutually_exclusive_group()
    comment_specification.add_argument("--comment", "--commentmatch", "-c", "-cM", type=str, default=None, help="Only saves the comment if the comment matches the given string")
    comment_specification.add_argument("--commentincl", "-cI", type=str, default=None, help="Only saves the comment if the comment contains the given string")
    comment_specification.add_argument("--commentexcl", "-cE", type=str, default=None, help="Only saves the comment if the comment not contains the given string")
    comment_specification.add_argument("--commentexclmatch", "-cEM", type=str, default=None, help="Only saves the comment if the comment not matches the given string")

    parser.add_argument("--minlikes", "-minL", type=int, default=0, help="Sets the minimum like requirement for the comment (inclusive)")
    parser.add_argument("--maxlikes", "-maxL", type=int, default=-1, help="Sets the maximum amount of likes a comment can have (inclusive)")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--verbose", "-v", action="store_true", help="Prints all actions made by the program")
    group.add_argument("--quiet", "-q", action="store_true", help="Prints only the critical events while running the program")
    parser.add_argument("--presearch", action="store_true", help="If selected the program will check for specifics while downloading, and saves only comments that match the specifications. By default it searches trough the comments after all have been downloaded. Use only if you are sure, you'll find what you are looking for!")
    parser.add_argument("--format", action="store_true", help="If selected, the program will format the document to be a json list for other usage. Requires more RAM if you have downloaded more comments.")

    # try: 
    args = parser.parse_args() if argv is None else parser.parse_args(argv)
    
    print("-==#" + "="*(len(HEAD[0]) - 6) + "#==-")
    for head_line in HEAD: print(" " + head_line)
    print("-==#" + "="*(len(HEAD[0]) - 6) + "#==-\n")

    youtube_id = args.youtubeid
    youtube_url = args.url
    output = args.output
    limit = args.limit
    heart = args.heart
    
    if args.append:
        if not os.path.exists(args.append):
            raise FileNotFoundError("The given file path does not exist ")
        else:
            append_file = args.append
    
    if not youtube_id and not youtube_url:
        parser.print_usage()
        raise ValueError('you need to specify a Youtube ID/URL and an output filename')

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

    if not output and args.presearch: output = f"{youtube_id}.comments"
    elif not output and not args.presearch: output = youtube_id
    else: output = args.output

    if os.path.sep in output:
        outdir = os.path.dirname(output)
        if not os.path.exists(outdir):
            os.makedirs(outdir)

    print('\nDownloading Youtube comments for video:', youtube_id or youtube_url)
    downloader = YoutubeCommentDownloader()
    generator = (
        downloader.get_comments(youtube_id, args.sort, args.language)
        if youtube_id
        else downloader.get_comments_from_url(youtube_url, args.sort, args.language)
    )
    count = 0
    presearch_founds = 0    
    
    if args.append is None:
        with io.open(output, 'w', encoding='utf8') as fp:
            start_time = time.time()
            for comment in generator:
                comment_json = json.dumps(comment, ensure_ascii=False)
                count += 1
                sys.stdout.flush()
                if args.presearch:

                    if limit != -1 and count + 1 >= limit: break

                    if not args.quiet and limit != -1: printProgressBar(count, limit, prefix='Progress:', suffix=f"Matched {presearch_founds}/{count} comment(s)", length=50)
                    elif args.quiet: print(f"Progress: {count}/{limit}, and found {presearch_founds}", end="\r")
                    elif limit == -1: print(f"Downloaded {count} and found {presearch_founds} comment(s)...", end="\r")

                    if author != None:
                        if args.author != None and author != comment["author"]: continue
                        elif args.authorincl != None and author not in comment["author"]: continue
                        elif args.authorexcl != None and author in comment["author"]: continue
                        elif args.authorexclmatch != None and author == comment["author"]: continue

                    if text != None:
                        if args.comment != None and text != comment["text"]: continue
                        elif args.commentincl != None and text not in comment["text"]: continue
                        elif args.commentexcl != None and text in comment["text"]: continue
                        elif args.commentexclmatch != None and text == comment["text"]:continue

                    if heart != HEART_EITHER:
                        if heart == HEART_TRUE and not comment["heart"]: continue
                        elif heart == HEART_FALSE and comment["heart"]: continue

                    try:
                        if maxlikes != -1 and not (minlikes <= int(comment["votes"]) <= maxlikes): continue
                        elif maxlikes == -1 and not (minlikes <= int(comment["votes"])): continue
                    except ValueError:
                        if not args.quiet:
                            print(f"[WARNING] Iteration {count}'s like count is greater than 999 ({comment['votes']})")

                    print(comment_json.decode('utf-8') if isinstance(comment_json, bytes) else comment_json, file=fp)
                    presearch_founds += 1
                    
                else:
                    print(comment_json.decode('utf-8') if isinstance(comment_json, bytes) else comment_json, file=fp)
                    if not args.quiet and limit != -1:
                        printProgressBar(count, limit, prefix='Progress:', suffix='Downloaded ' + str(count) + ' comment(s)', length=50)
                    elif args.quiet: print(f"Progress: {count}/{limit}", end="\r")
                    elif limit == -1: print(f"Downloaded {count} comment(s)...", end="\r")

                    if limit != -1 and count >= limit: break

        if args.verbose: print('Done in {:.2f} seconds\n'.format(time.time() - start_time))
        elif args.quiet: print(f"Progress: {count}/{limit}...Done!")
        else: print('Done! [{:.2f} seconds]\n'.format(time.time() - start_time))
        
    elif args.append:
        with open(append_file, "r", encoding="utf8") as apf:
            # First line is latest.
            latest_comment_id = json.loads(apf.readline().rstrip())["cid"]
        
        with io.open(f"{output}.tmp", 'w', encoding='utf8') as fp:
            start_time = time.time()
            for comment in generator:
                comment_json = json.dumps(comment, ensure_ascii=False)
                
                if latest_comment_id == json.loads(comment_json)["cid"]: 
                    print("APPEND POINT FOUND")
                    break
                
                count += 1
                sys.stdout.flush()                                    
                if args.presearch:

                    if limit != -1 and count + 1 >= limit: break

                    if not args.quiet and limit != -1: printProgressBar(count, limit, prefix='Progress:', suffix=f"Matched {presearch_founds}/{count} comment(s)", length=50)
                    elif args.quiet: print(f"Progress: {count}/{limit}, and found {presearch_founds}", end="\r")
                    elif limit == -1: print(f"Downloaded {count} and found {presearch_founds} comment(s)...", end="\r")

                    if author != None:
                        if args.author != None and author != comment["author"]: continue
                        elif args.authorincl != None and author not in comment["author"]: continue
                        elif args.authorexcl != None and author in comment["author"]: continue
                        elif args.authorexclmatch != None and author == comment["author"]: continue

                    if text != None:
                        if args.comment != None and text != comment["text"]: continue
                        elif args.commentincl != None and text not in comment["text"]: continue
                        elif args.commentexcl != None and text in comment["text"]: continue
                        elif args.commentexclmatch != None and text == comment["text"]:continue

                    if heart != HEART_EITHER:
                        if heart == HEART_TRUE and not comment["heart"]: continue
                        elif heart == HEART_FALSE and comment["heart"]: continue

                    try:
                        if maxlikes != -1 and not (minlikes <= int(comment["votes"]) <= maxlikes): continue
                        elif maxlikes == -1 and not (minlikes <= int(comment["votes"])): continue
                    except ValueError:
                        if not args.quiet:
                            print(f"[WARNING] Iteration {count}'s like count is greater than 999 ({comment['votes']})")

                    print(comment_json.decode('utf-8') if isinstance(comment_json, bytes) else comment_json, file=fp)
                    presearch_founds += 1
                    
                else:
                    print(comment_json.decode('utf-8') if isinstance(comment_json, bytes) else comment_json, file=fp)
                    if not args.quiet and limit != -1:
                        printProgressBar(count, limit, prefix='Progress:', suffix='Downloaded ' + str(count) + ' comment(s)', length=50)
                    elif args.quiet: print(f"Progress: {count}/{limit}", end="\r")
                    elif limit == -1: print(f"Downloaded {count} comment(s)...", end="\r")

                    if limit != -1 and count >= limit: break

        if args.verbose: print('Done in {:.2f} seconds\n'.format(time.time() - start_time))
        elif args.quiet: print(f"Progress: {count}/{limit}...Done!")
        else: print('Done! [{:.2f} seconds]\n'.format(time.time() - start_time))
    else:
        raise RuntimeError("Append methond can not be determined!")

    if not args.presearch:
        start_time = time.time()
        print("Starting filtering", end="..." if args.quiet else "\n")
        if not args.quiet:
            if author != None:
                print(f"[AUTHOR] {author}")
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
            if os.path.exists(output + ".comments"):
                os.remove(output + ".comments")
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

                    if args.verbose: print(f"[ITERATION] {count} | Adding line...")
                    ap.write(line)
        if os.path.exists(output) and not args.presearch: os.remove(output)
        if args.verbose: print('Done in {:.2f} seconds\n'.format(time.time() - start_time))
        elif args.quiet: print("Done!")
        else: print('Done! [{:.2f} seconds]\n'.format(time.time() - start_time))

    if args.format:
        print("Formatting to json", end="..." if args.quiet else "\n")
        if not args.quiet:
            print('Reading and converting the data...', end="\n" if args.verbose else "")
        data = []
        if args.verbose:
            printProgressBar(0, limit, prefix='Progress:', suffix='Converting ' + str(0) + ' line(s)', length=50)
        start_time = time.time()
        with open(f"{output}.comments", 'r', encoding='utf8') as r:
            c = 0
            while True:
                line = r.readline()
                if not line: break
                data.append(json.loads(line))
                c += 1
                if args.verbose:
                    printProgressBar(c, limit, prefix='Progress:', suffix='Converting ' + str(c) + ' line(s)', length=50)
        if args.verbose: print('Done in {:.2f} seconds\n'.format(time.time() - start_time))
        elif not args.quiet: print('Done! [{:.2f} seconds]'.format(time.time() - start_time))

        if not args.quiet:
            print('Writing and saving the data...', end="\n" if args.verbose else "")
        if args.verbose:
            printProgressBar(0, 1, prefix='Progress:', suffix='Writing line ' + str(0), length=50)
        start_time = time.time()
        json_data = json.dumps(data, indent=4)
        with open(f"{output}.comments", 'w', encoding='utf8') as r:
            r.write(json_data)
            if args.verbose:
                printProgressBar(1, 1, prefix='Progress:', suffix='Writing line ' + str(c), length=50)

        if args.verbose: print('Done in {:.2f} seconds\n'.format(time.time() - start_time))
        elif args.quiet: print("Done!")
        else: print('Done! [{:.2f} seconds]'.format(time.time() - start_time))

        print()
            
    # except Exception as e:
    #     print('Error:', str(e))
    #     sys.exit(1)