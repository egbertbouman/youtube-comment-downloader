FROM alpine:3.7

RUN apk add --no-cache python3 \
                       python3-dev \
                       make \
                       g++ \
                       libxml2-dev \
                       libxslt-dev

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip3 install --upgrade pip==20.1.1 && \
    pip3 install -r requirements.txt

COPY . .
