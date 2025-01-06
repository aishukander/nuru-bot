# 使用 slim 版本減輕 Image 容量
FROM python:3.13.1-slim

ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_ROOT_USER_ACTION=ignore

WORKDIR /bot

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    mkdir -p /tmp/data && \
    rm -rf /root/.cache/pip/*

COPY . .

RUN chmod +x /bot/entrypoint.sh && \
    cp -r /bot/json/* /tmp/data/

ENTRYPOINT ["/bot/entrypoint.sh"]

# 建置映像檔：docker build -t [使用者名稱]/[映像檔名稱]:latest .
# 上傳映像檔：docker push [使用者名稱]/[映像檔名稱]:latest