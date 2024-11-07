# syntax=docker/dockerfile:1
FROM python:3.10-alpine

WORKDIR /tmp/indeed

RUN apk add --no-cache \
    build-base \
    gcc \
    g++ \
    musl-dev \
    python3-dev

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

ENV DEBIAN_FRONTEND=noninteractive
RUN apk update && apk add tk
RUN apk add font-terminus font-inconsolata font-dejavu font-noto font-noto-cjk font-awesome font-noto-extra

COPY . .
CMD ["python3", "main.py"]