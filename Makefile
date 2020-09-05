build:
	docker build -t youtube-downloader:latest .

run:
	docker build -t youtube-downloader:latest . && docker run -it --rm -v ${CURDIR}:/usr/src/app youtube-downloader:latest

download:
	python3 lib/downloader.py --youtubeid $(youtubeid) --output data/$(output).json

get:
	python3 lib/downloader.py --youtubeid $(id) --output data/$(id).json
