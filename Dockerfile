# 使用 slim 版本減輕 Image 容量
FROM python:3.12.5-slim

# 指定 Image 中的工作目錄
WORKDIR /bot

# 將 Dockerfile 所在目錄下的所有檔案複製到 Image 的工作目錄 /bot 底下
COPY . /bot

# 在 Image 中執行的指令
RUN apt update \
    && pip install --upgrade pip \
    && chmod +x /bot/entrypoint.sh \
    && pip install -r requirements.txt \
    && mkdir -p /tmp/data \
    && cp -r /bot/json/* /tmp/data/

ENTRYPOINT ["/bot/entrypoint.sh"]
#到mumei-bot資料夾後使用終端機執行docker build -t [使用者名稱]/[映像檔名稱]:latest . 來將bot保存成docker映像檔
#到mumei-bot資料夾後使用終端機執行docker push [使用者名稱]/[映像檔名稱]:latest 來將bot上傳至docker hub