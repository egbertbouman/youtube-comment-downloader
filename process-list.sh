#!/bin/bash
# File Author:      Sick.Codes https://github.com/sickcodes https://twitter.com/sickcodes
# License:          MIT
# Repo:             https://github.com/egbertbouman/youtube-comment-downloader
# 
# Usage:            ./process-list.sh videolist.txt

mkdir -p ./output

case "$1" in
    '' )        echo "Usage: ./process-list.sh videolist.txt" && exit 1
        ;;
esac


mapfile -t < "$1"

for VIDEO_ID in "${MAPFILE[@]}"; do
    VIDEO_ID="${VIDEO_ID//$'https://www.youtube.com/watch?v='/}"
    echo "${VIDEO_ID}"
    python downloader.py --youtubeid="${VIDEO_ID}" --output="./output/${VIDEO_ID}.json"
done


echo "Finished list"