# youtube-comment-downloader
Simple script for downloading Youtube comments without using the Youtube API. The output is in line delimited JSON.

### Installation

Clone the git repository:

```
git clone https://github.com/schneiderkamplab/youtube-insights.git
```

Preferably inside a [python virtual environment](https://virtualenv.pypa.io/en/latest/) install this package via:

```
cd youtube-insights
pip install .
```

### Usage as command-line interface
```
$ youtube-insights --help
usage: youtube-insights [--help] [--youtubeid YOUTUBEID] [--url URL] [--output OUTPUT] [--limit LIMIT] [--language LANGUAGE] [--sort SORT]

Download Youtube comments without using the Youtube API

optional arguments:
  --help, -h                             Show this help message and exit
  --youtubeid YOUTUBEID, -y YOUTUBEID    ID of Youtube video for which to download the comments
  --url URL, -u URL                      Youtube URL for which to download the comments
  --output OUTPUT, -o OUTPUT             Output filename (output format is line delimited JSON)
  --limit LIMIT, -l LIMIT                Limit the number of comments
  --language LANGUAGE, -a LANGUAGE       Language for Youtube generated text. Defaults to en.
  --sort SORT, -s SORT                   Whether to download popular (0) or recent comments (1). Defaults to 1
  --template TEMPLATE, -t TEMPLATE
                        Formatting template using the jsonl fields, e.g., "{author} wrote {time}: {text}". Defaults to None, which outputs the raw JSON.
  --quote QUOTE, -q QUOTE
                        enclose values in quotes when filling template. Defaults to False.
```

For example:
```
youtube-insights --url https://www.youtube.com/watch?v=ScMzIvxBSi4 --output ScMzIvxBSi4.jsonl
```
or using the Youtube ID:
```
youtube-insights --youtubeid ScMzIvxBSi4 --output ScMzIvxBSi4.jsonl
```

For Youtube IDs starting with - (dash) you will need to run the script with:
`-y=idwithdash` or `--youtubeid=idwithdash`

For extracting just the texts, a template can be added:
```
youtube-insights --youtubeid ScMzIvxBSi4 --output ScMzIvxBSi4.txt --limit 10 --template "{text}"
```

Templates can also reference other JSON fields:
```
youtube-insights --youtubeid ScMzIvxBSi4 --output ScMzIvxBSi4.txt --limit 10 --template "{author} wrote {time}: {text}"
```

To export to CSV with author, time, and text:
```
youtube-insights --youtubeid ScMzIvxBSi4 --output ScMzIvxBSi4.csv --limit 10 --template "{author},{time},{text}" --quote True
```

### Usage as library
You can also use this script as a library. For instance, if you want to print out the 10 most popular comments for a particular Youtube video you can do the following:


```python
from itertools import islice
from youtube_insights import *
downloader = YoutubeCommentDownloader()
comments = downloader.get_comments_from_url('https://www.youtube.com/watch?v=ScMzIvxBSi4', sort_by=SORT_BY_POPULAR)
for comment in islice(comments, 10):
    print(comment)
```
