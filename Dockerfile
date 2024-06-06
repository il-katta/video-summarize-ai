FROM docker.io/library/python:3.11-slim-bookworm as base

RUN --mount=type=cache,target=/var/lib/apt/lists \
    --mount=type=cache,target=/var/cache/apt \
    set -x && \
    apt-get -qq update && \
    apt-get -y -qq install --no-install-recommends ffmpeg

ADD requirements.txt /tmp/requirements.txt

RUN --mount=type=cache,target=/root/.cache/pip \
    set -x && \
    pip install -r /tmp/requirements.txt

FROM base
LABEL authors="andrea"

ADD . /src/app

RUN --mount=type=cache,target=/root/.cache/pip \
    set -x && \
    pip install -e /src/app


ENTRYPOINT ["audio_summary_telegram_bot"]
