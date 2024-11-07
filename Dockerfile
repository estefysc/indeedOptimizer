# syntax=docker/dockerfile:1
FROM python:3.12-bookworm
# FROM python:3.9-alpine

WORKDIR /tmp/indeed

COPY requirements.txt requirements.txt
RUN apt-get update && apt-get install -y \
    python3-dev \
    tk 
RUN pip install -r requirements.txt

ENV DEBIAN_FRONTEND=noninteractive
# RUN apk update && apk add tk
# RUN apt-get install -y font-terminus font-inconsolata font-dejavu font-noto font-noto-cjk font-awesome font-noto-extra

COPY . .
CMD ["python3", "main.py"]