FROM alpine:latest
RUN apk add --no-cache git python python-dev py-pip build-base avahi libffi-dev musl-dev openssl-dev
RUN pip install --upgrade pip
RUN pip install paramiko
