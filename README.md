# youtube-comment-downloader
Simple script for downloading Youtube comments without using the Youtube API. The output is in line delimited JSON.

### Installation

Preferably inside a [python virtual environment](https://virtualenv.pypa.io/en/latest/) install this package via

```
pip install https://github.com/egbertbouman/youtube-comment-downloader/archive/master.zip
```

### Usage
```
$ youtube-comment-downloader --help
usage: youtube-comment-downloader [--help] [--youtubeid YOUTUBEID] [--output OUTPUT] [--limit LIMIT]

Download Youtube comments without using the Youtube API

optional arguments:
  --help, -h            Show this help message and exit
  --youtubeid YOUTUBEID, -y YOUTUBEID
                        ID of Youtube video for which to download the comments
  --output OUTPUT, -o OUTPUT
                        Output filename (output format is line delimited JSON)
  --limit LIMIT, -l LIMIT
                        Limit the number of comments
```

For example:
```
youtube-comment-downloader --youtubeid ScMzIvxBSi4 --output ScMzIvxBSi4.json
```

For Youtube IDs starting with - (dash) you will need to run the script with:
`-y=-idwithdash` or `--youtubeid=-idwithdash`

### Dependencies
* Python 2.7+
* requests
* lxml
* cssselect

The python packages can be installed with:

    pip install -r requirements.txt
