# youtube-comment-downloader
Simple script for downloading Youtube comments without using the Youtube API with expanded selectors and more. The output is in line delimited JSON or JSON array/list.

### Installation

Preferably inside a [python virtual environment](https://virtualenv.pypa.io/en/latest/) install this package via

```
pip install https://github.com/drdayox/youtube-comment-downloader/archive/test.zip
```

### Usage
```
$ youtube-comment-downloader --help
usage: downloader.py [--help] [--output str] [--limit int] [--language str] [--sort int] [--heart int]
                     [--author str | --authorincl str | --authorexcl str | --authorexclmatch str]
                     [--comment str | --commentincl str | --commentexcl str | --commentexclmatch str] [--minlikes int] [--maxlikes int] [--verbose | --quiet] [--presearch]
                     [--format]
                     youtubeid

Download Youtube comments without using the Youtube API

positional arguments:
  youtubeid             ID of Youtube video for which to download the comments

options:
  --help, -h            Show this help message and exit
  --output str, -o str  Output filename (output format is line delimited JSON)
  --limit int, -l int   Limit the number of comments
  --language str        Language for Youtube generated text (e.g. en)
  --sort int, -s int    Whether to download popular (0) or recent comments (1). Defaults to 1
  --heart int, -H int   If set 1, only saves comment with hearts, if 0 it saves comments only without a heart. Default: -1 (Saves all).
  --author str, -a str  Only saves the comment if the author's name matches the given string
  --authorincl str, -aI str
                        Only saves the comment if the author's name contains the string
  --authorexcl str, -aE str
                        Only saves the comment if the author's name not contains the string
  --authorexclmatch str, -aEM str
                        Only saves the comment if the author's name not matches the string
  --comment str, -c str
                        Only saves the comment if the comment matches the given string
  --commentincl str, -cI str
                        Only saves the comment if the comment contains the given string
  --commentexcl str, -cE str
                        Only saves the comment if the comment not contains the given string
  --commentexclmatch str, -cEM str
                        Only saves the comment if the comment not matches the given string
  --minlikes int, -minL int
                        Sets the minimum like requirement for the comment (inclusive)
  --maxlikes int, -maxL int
                        Sets the maximum amount of likes a comment can have (inclusive)
  --verbose, -v         Prints all actions made by the program
  --quiet, -q           Prints only the critical events while running the program
  --presearch           If selected the program will check for specifics while downloading, and saves only comments that match the specifications. By default it searches
                        trough the comments after all have been downloaded. Use only if you are sure, you'll find what you are looking for!
  --format              If selected, the program will format the document to be a json list for other usage. Requires more RAM if you have downloaded more comments.
```

For example:
```
youtube-comment-downloader ScMzIvxBSi4
```

For Youtube IDs starting with - (dash) you will need to run the script with:
`-y=-idwithdash` or `--youtubeid=-idwithdash`

### Dependencies
* Python 2.7+
* requests

The python packages can be installed with:

    pip install -r requirements.txt
