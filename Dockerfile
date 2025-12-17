ARG Python_version=3.13.1-slim
ARG Bot_version=development

# Build Stage
FROM python:${Python_version} AS builder

ENV \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_ROOT_USER_ACTION=ignore

WORKDIR /bot

COPY . .

# compile ffmpeg statically and install required packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends wget xz-utils && \
    wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz && \
    tar xf ffmpeg-release-amd64-static.tar.xz && \
    mv ffmpeg-*-amd64-static/ffmpeg /usr/local/bin/ && \
    mv ffmpeg-*-amd64-static/ffprobe /usr/local/bin/ && \
    rm -f ffmpeg-release-amd64-static.tar.xz && \
    rm -rf ffmpeg-*-amd64-static

RUN mkdir -p /tmp/toml && \
    find /bot/toml -type f ! -name 'Token.toml' -exec cp {} /tmp/toml/ \; && \
    mv /bot/toml/default_Token.toml /tmp/toml/Token.toml && \
    rm -rf /bot/toml/*

# Runtime Stage
FROM python:${Python_version}
ARG Bot_version
LABEL org.opencontainers.image.authors="aishukander <hank960924@gmail.com>"

ENV \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_ROOT_USER_ACTION=ignore \
    BOT_VERSION=${Bot_version}

WORKDIR /bot

# copy ffmpeg and bot files from builder stage
COPY --from=builder /usr/local/bin/ffmpeg /usr/local/bin/ffmpeg
COPY --from=builder /usr/local/bin/ffprobe /usr/local/bin/ffprobe
COPY --from=builder /tmp/toml/ /tmp/toml/
COPY --from=builder /bot/ /bot/

# install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends libopus0 firefox-esr && \
    rm -rf /var/lib/apt/lists/* && \
    # install Python requirements
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    rm -rf /root/.cache/pip/* && \
    chmod +x /bot/entrypoint.sh

ENTRYPOINT ["/bot/entrypoint.sh"]