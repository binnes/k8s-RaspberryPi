FROM ubuntu:bionic
RUN apt-get update && apt-get install -y git python3 python3-dev python3-pip build-essential libffi-dev musl-dev libssl-dev multipath-tools
RUN pip install --upgrade pip
