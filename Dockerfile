FROM ubuntu:bionic
RUN apt-get update && apt-get install -y git python3 python3-dev python3-pip build-essential libffi-dev musl-dev libssl-dev multipath-tools
RUN update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 10 && update-alternatives --install /usr/bin/python python /usr/bin/python3 10
RUN pip install --upgrade pip
