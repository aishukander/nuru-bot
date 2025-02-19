FROM python:3.13.1-slim

ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_ROOT_USER_ACTION=ignore

WORKDIR /bot

COPY requirements.txt .

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    mkdir -p /tmp/data && \
    rm -rf /root/.cache/pip/*

COPY . .

RUN chmod +x /bot/entrypoint.sh && \
    cp -r /bot/json/* /tmp/data/

ENTRYPOINT ["/bot/entrypoint.sh"]