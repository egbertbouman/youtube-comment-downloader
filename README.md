# youtube-comment-downloader
Simple script for downloading Youtube comments without using the Youtube API. The output is in line delimited JSON.

### Dependencies
* Python 2.7+
* requests
* lxml
* cssselect

The python packages can be installed with

```bash
pip install --user -r requirements.txt

# or
pip install --user requests lxml cssselect
```    

### Usage
```
usage: downloader.py [--help] [--youtubeid YOUTUBEID] [--output OUTPUT]

Download Youtube comments without using the Youtube API

optional arguments:
  --help, -h            Show this help message and exit
  --youtubeid YOUTUBEID, -y YOUTUBEID
                        ID of Youtube video for which to download the comments
  --output OUTPUT, -o OUTPUT
                        Output filename (output format is line delimited JSON)
```

Examples:
```bash
python downloader.py --youtubeid ScMzIvxBSi4 --output ScMzIvxBSi4.json

python downloader.py --youtubeid="ScMzIvxBSi4" --output="ScMzIvxBSi4.json"

# For Youtube IDs starting with '-' you must quote your arguments:

# https://www.youtube.com/watch?v=-4sGPBeBHag
python downloader.py --youtubeid="-4sGPBeBHag" --output="-4sGPBeBHag.json"

```

### Bulk Usage:

Create a text file list of `video URL's` or `video ID's` or both.

```bash
./process-list.sh videolist.txt
```