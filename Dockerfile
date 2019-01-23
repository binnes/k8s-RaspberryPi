FROM ubuntu:bionic
RUN apt-get update && apt-get install -y git python python-dev python-pip build-essential libffi-dev musl-dev libssl-dev multipath-tools
RUN pip install --upgrade pip
RUN pip install paramiko
