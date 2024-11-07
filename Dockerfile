# syntax=docker/dockerfile:1
FROM python:3.10-alpine
# FROM python:3.9-alpine

WORKDIR /tmp/indeed

COPY requirements.txt requirements.txt
RUN apk update && apk add --no-cache \
    build-base \
    gcc \
    musl-dev \
    python3-dev \
    tk \
    linux-headers
RUN pip install -r requirements.txt

ENV DEBIAN_FRONTEND=noninteractive
# RUN apk update && apk add tk
RUN apk add font-terminus font-inconsolata font-dejavu font-noto font-noto-cjk font-awesome font-noto-extra

COPY . .
CMD ["python3", "main.py"]