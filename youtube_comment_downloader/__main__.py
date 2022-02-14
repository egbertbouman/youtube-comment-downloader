#!/usr/bin/env python

if __package__ is None:
    import sys, os.path
    path = os.path.realpath(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(os.path.dirname(path)))

import youtube_comment_downloader


if __name__ == '__main__':
    youtube_comment_downloader.main()
