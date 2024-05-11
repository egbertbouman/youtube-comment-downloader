# youtube-comment-downloader
Simple script for downloading Youtube comments without using the Youtube API. The output is in line delimited JSON.

### Installation

Preferably inside a [python virtual environment](https://virtualenv.pypa.io/en/latest/) install this package via:

```
pip install youtube-comment-downloader
```

Or directly from the GitHub repository:

```
pip install https://github.com/egbertbouman/youtube-comment-downloader/archive/master.zip
```

### Usage as command-line interface
```
$ youtube-comment-downloader --help
usage: youtube-comment-downloader [--help] [--youtubeid YOUTUBEID] [--url URL] [--output OUTPUT] [--limit LIMIT] [--language LANGUAGE] [--sort SORT]

Download Youtube comments without using the Youtube API

optional arguments:
  --help, -h                             Show this help message and exit
  --youtubeid YOUTUBEID, -y YOUTUBEID    ID of Youtube video for which to download the comments
  --url URL, -u URL                      Youtube URL for which to download the comments
  --output OUTPUT, -o OUTPUT             Output filename (output format is line delimited JSON)
  --pretty, -p                           Change the output format to indented JSON
  --limit LIMIT, -l LIMIT                Limit the number of comments
  --language LANGUAGE, -a LANGUAGE       Language for Youtube generated text (e.g. en)
  --sort SORT, -s SORT                   Whether to download popular (0) or recent comments (1). Defaults to 1
```

For example:
```
youtube-comment-downloader --url https://www.youtube.com/watch?v=ScMzIvxBSi4 --output ScMzIvxBSi4.json
```
or using the Youtube ID:
```
youtube-comment-downloader --youtubeid ScMzIvxBSi4 --output ScMzIvxBSi4.json
```

For Youtube IDs starting with - (dash) you will need to run the script with:
`-y=idwithdash` or `--youtubeid=idwithdash`


### Usage as Python Library
You can also use this script as a library. Here's example code that you can use

1. For instance, if you want to print out the 10 most popular comments for a particular Youtube video you can do the following:

```python
from itertools import islice
from youtube_comment_downloader import *
downloader = YoutubeCommentDownloader()
youtube_url = 'https://www.youtube.com/watch?v=ScMzIvxBSi4' # Change this to a youtube link to the video you want to download the comment
comments = downloader.get_comments_from_url(youtube_url, sort_by=SORT_BY_POPULAR)
for comment in islice(comments, 10):
    print(comment)
```

2. Script for download the comments as excel or csv file. 

```python
# Initiate Library
import pandas as pd
from youtube_comment_downloader import *

# Initiate Downloader and Youtube_url
downloader = YoutubeCommentDownloader()
Youtube_URL = 'https://www.youtube.com/watch?v=ScMzIvxBSi4' # Change this to a youtube link to the video you want to download the comment
comments = downloader.get_comments_from_url(Youtube_URL, sort_by=SORT_BY_POPULAR)

# Initiate a dictionary to save all comments from Youtube Video
all_comments_dict = {
    'cid': [],
    'text': [],
    'time': [],
    'author': [],
    'channel': [],
    'votes': [],
    'replies': [],
    'photo': [],
    'heart': [],
    'reply': [],
    'time_parsed': []
}

# Take all comment and save it in dictionary using for loop
for comment in comments:
    for key in all_comments_dict.keys():
        all_comments_dict[key].append(comment[key])

# Convert Dictionary to Dataframe using Pandas
comments_df = pd.DataFrame(all_comments_dict)

# Display Dataframe
display(comments_df)

# Uncomment this if you want to save in excel format
# comments_df.to_excel('comments_data.xlsx', index=False)

# Uncomment this if you want to sve in csv format
# comments_df.to_csv('comments_data.csv', index=False)
```
   
