FROM alpine:latest
RUN apk add --no-cache git python python-dev py-pip build-base avahi
RUN pip install --upgrade pip
