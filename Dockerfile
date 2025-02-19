# 建構階段
ARG PYTHON_VERSION=3.13.1
FROM python:${PYTHON_VERSION}-slim AS builder

ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_ROOT_USER_ACTION=ignore

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 最終階段
ARG PYTHON_VERSION
FROM python:${PYTHON_VERSION}-slim

ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_ROOT_USER_ACTION=ignore

COPY --from=builder /usr/bin/ffmpeg /usr/bin/
COPY --from=builder /usr/lib/x86_64-linux-gnu/libav* /usr/lib/x86_64-linux-gnu/
COPY --from=builder /usr/lib/x86_64-linux-gnu/libswscale* /usr/lib/x86_64-linux-gnu/

WORKDIR /bot

COPY --from=builder /usr/local/lib/python${PYTHON_VERSION%.*}/site-packages /usr/local/lib/python${PYTHON_VERSION%.*}/site-packages

COPY . .

RUN mkdir -p /tmp/data && \
    chmod +x /bot/entrypoint.sh && \
    cp -r /bot/json/* /tmp/data/

ENTRYPOINT ["/bot/entrypoint.sh"]