# youtube-comment-downloader
Simple script for downloading Youtube comments without using the Youtube API. The output is in line delimited JSON.

This is a fork of [egbertbouman/youtube-comment-downloader](https://github.com/egbertbouman/youtube-comment-downloader)

### Usage

You must have `make` and `Docker` installed.

The `youtubeid` argument correspond to the ID in the video URL.

```
usage:
make run (outside of the container)
make download youtubeid=foo output=bar (inside)
make get id=foo
```

For example:
```
make download youtubeid=ScMzIvxBSi4 output=ScMzIvxBSi4
OR
make get id=ScMzIvxBSi4
```

You will then have a file named `ScMzIvxBSi4.json` in the data folder.
