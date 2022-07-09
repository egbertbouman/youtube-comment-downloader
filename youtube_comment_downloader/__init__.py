#Written by egbertbouman
#Forked by eiskaffe

import argparse
import io
import json
import os
import sys
import time

from alive_progress import alive_bar
from grapheme import length
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
        
    parser = argparse.ArgumentParser(add_help=False, description=('Download Youtube comments without using the Youtube API'))

    # DEFAULT ARGUMENTS 
    parser.add_argument('--help', '-h', action='help', default=argparse.SUPPRESS, help='Show this help message and exit')
    parser.add_argument('youtubeid', nargs="*", help='ID of Youtube videos for which to download the comments. If more than one are given and no limit is set, you can end the download for a video by pressing ctrl+c, otherwise it will stick to the limit')
    parser.add_argument('--output', '-o', help='Output filename (output format is line delimited JSON)')
    parser.add_argument('--limit', '-l', default=0,type=int, help='Limit the number of comments. By default it downloads until break')
    parser.add_argument('--language', type=str, default=None, help='Language for Youtube generated text (e.g. en)')
    parser.add_argument('--sort', '-s', type=int, default=SORT_BY_RECENT, help='Whether to download popular (0) or recent comments (1). Defaults to 1')
    parser.add_argument('--url', '-u', nargs="+", help='Youtube URL for which to download the comments. If more than one are given and no limit is set, you can end the download for a video by pressing ctrl+c, otherwise it will stick to the limit')
    parser.add_argument('--append',  help='Appends the new comments into an existing file. Raises an error if trying to append an empty file, can not be done with a formatted file, but can be formatted afterwards')

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
    
    if not args.quiet:
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
    
    print(args)
    if youtube_id is None and youtube_url is None:
        parser.print_usage()
        raise ValueError('you need to specify a Youtube ID/URL and an output filename')
    link_max = 0 if youtube_id is None else len(youtube_id) + 0 if youtube_url is None else len(youtube_url)
    

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

    link_n = 1
    for link in youtube_id + youtube_url:
        print(f'\nDownloading Youtube comments for video: {link}' + "" if link_max == 1 else f" [{link_n}/{link_max}]")
        link_n += 1
        downloader = YoutubeCommentDownloader()
        generator = (
            downloader.get_comments_from_url(link, args.sort, args.language)
            if link[:5] == "https"
            else downloader.get_comments(link, args.sort, args.language)
        )
        
        presearch_founds = 0    
        if args.append is None:
            with io.open(output, 'w', encoding='utf8') as fp:
                start_time = time.time()
                stats = "({rate:.1f}/s, eta: {eta}," if args.presearch else "({rate:.1f}/s, eta: {eta})"
                with alive_bar(limit, ctrl_c=False, unknown="triangles", stats=stats) as bar:
                    if args.presearch: bar.text = "found: 0)"
                    for comment in generator:
                        comment_json = json.dumps(comment, ensure_ascii=False)
                        sys.stdout.flush()
                        if args.presearch:

                            bar.text = f"found: {presearch_founds})"
                            bar()

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
                                    print(f"Like count is greater than 999 ({comment['votes']})")

                            print(comment_json.decode('utf-8') if isinstance(comment_json, bytes) else comment_json, file=fp)
                            presearch_founds += 1
                            if limit != 0 and bar.current() >= limit: break
                        else:
                            bar()
                            print(comment_json.decode('utf-8') if isinstance(comment_json, bytes) else comment_json, file=fp)
                            if limit != 0 and bar.current() >= limit: break
                    count = bar.current()

            if args.presearch:
                if args.quiet:
                    print(f"Found {presearch_founds} out of {count} comments")
                else:
                    print(f"Found {presearch_founds} that match the requirements out of the {count} comments scanned")
            
        elif args.append:
            with open(append_file, "r", encoding="utf8") as apf:
                # First line is latest.
                latest_comment_id = json.loads(apf.readline().rstrip())["cid"]
            
            with io.open(f"{output}.tmp", 'w', encoding='utf8') as fp:
                start_time = time.time()
                stats = "({rate:.1f}/s, eta: {eta}," if args.presearch else "({rate:.1f}/s, eta: {eta})"
                with alive_bar(limit, ctrl_c=False, unknown="triangles", stats=stats) as bar:
                    if args.presearch: bar.text = "found: 0)"
                    for comment in generator:
                        comment_json = json.dumps(comment, ensure_ascii=False)
                        sys.stdout.flush()  
                        
                        if latest_comment_id == json.loads(comment_json)["cid"]: 
                            print("Appendation point found, breaking")
                            break
                        
                        if args.presearch:

                            bar.text = f"found: {presearch_founds})"
                            bar()

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
                                    print(f"Like count is greater than 999 ({comment['votes']})")

                            print(comment_json.decode('utf-8') if isinstance(comment_json, bytes) else comment_json, file=fp)
                            presearch_founds += 1
                            if limit != 0 and bar.current() >= limit: break
                        else:
                            bar()
                            print(comment_json.decode('utf-8') if isinstance(comment_json, bytes) else comment_json, file=fp)
                            if limit != 0 and bar.current() >= limit: break
                    count = bar.current()

            if args.presearch:
                if args.quiet:
                    print(f"Found {presearch_founds} out of {count} comments")
                else:
                    print(f"Found {presearch_founds} that match the requirements out of the {count} comments scanned")
                        
        else:
            raise RuntimeError("Append method can not be determined!")

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
            if not args.append:
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
                os.remove(output)
            elif args.append:
                with open(f"{output}.tmp", "r", encoding="utf8") as fp:
                    if os.path.exists(f"{output}2.tmp"):
                        os.remove(f"{output}2.tmp")
                    with open(f"{output}2.tmp", "a", encoding="utf8") as ap:
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
                
                
            if os.path.exists(f"{output}.tmp") and not args.presearch: os.remove(f"{output}.tmp")
            if args.verbose: print('Done in {:.2f} seconds\n'.format(time.time() - start_time))
            elif args.quiet: print("Done!")
            else: print('Done! [{:.2f} seconds]\n'.format(time.time() - start_time))

        # MERGING
        if args.append:
            print("Appending...",end="")
            if args.presearch:
                with open(f"{output}.tmp", "a", encoding="utf8") as appendee:
                    with open(append_file, "r", encoding="utf8") as rf:
                        while True:
                            line = rf.readline().strip()
                            appendee.write(line+"\n")
                            if not line:
                                break
                if os.path.exists(append_file): os.remove(append_file)
                os.rename(f"{output}.tmp", append_file)
            elif not args.presearch:
                with open(f"{output}2.tmp", "a", encoding="utf8") as appendee:
                    with open(append_file, "r", encoding="utf8") as rf:
                        while True:
                            line = rf.readline().strip()
                            appendee.write(line+"\n")
                            if not line:
                                break
                if os.path.exists(append_file): os.remove(append_file)
                os.rename(f"{output}2.tmp", append_file)
            print("Done!")
                                        

        if args.format and not args.append:
            print("Formatting to json", end="..." if args.quiet else "\n")
            if not args.quiet:
                print('Reading and converting the data...', end="\n" if args.verbose else "")
            data = []
            start_time = time.time()
            with open(f"{output}.comments", 'r', encoding='utf8') as r:
                c = 0
                while True:
                    line = r.readline()
                    if not line: break
                    data.append(json.loads(line))
                    c += 1
            if args.verbose: print('Done in {:.2f} seconds\n'.format(time.time() - start_time))
            elif not args.quiet: print('Done! [{:.2f} seconds]'.format(time.time() - start_time))

            if not args.quiet:
                print('Writing and saving the data...', end="\n" if args.verbose else "")
            start_time = time.time()
            json_data = json.dumps(data, indent=4)
            with open(f"{output}.comments", 'w', encoding='utf8') as r:
                r.write(json_data)

            if args.verbose: print('Done in {:.2f} seconds\n'.format(time.time() - start_time))
            elif args.quiet: print("Done!")
            else: print('Done! [{:.2f} seconds]'.format(time.time() - start_time))

            print()
