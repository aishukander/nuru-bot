# 使用 slim 版本減輕 Image 容量
FROM python:3.10.10-slim

# 指定 Image 中的工作目錄
WORKDIR /code

# 將 Dockerfile 所在目錄下的所有檔案複製到 Image 的工作目錄 /code 底下
COPY . /code

# 在 Image 中執行的指令
RUN apt update

RUN apt install -y ffmpeg

RUN apt install -y git

RUN pip install -r requirements.txt

RUN mkdir -p /tmp/data && cp -r /code/json/* /tmp/data/

ENTRYPOINT ["/bin/bash", "-c", "if [ -d /code/json/ ] && [ ! $(ls -A /code/json/) ]; then cp -r /tmp/data/* /code/json/; fi && exec python ./main.py"]
#到mumei-bot資料夾後使用終端機執行docker build -t [使用者名稱]/[映像檔名稱]:latest . 來將bot保存成docker映像檔
#到mumei-bot資料夾後使用終端機執行docker push [使用者名稱]/[映像檔名稱]:latest 來將bot上傳至docker hub