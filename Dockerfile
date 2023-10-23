# 使用 slim 版本減輕 Image 容量
FROM python:3.9-slim

# 指定 Image 中的工作目錄
WORKDIR /code

# 將 Dockerfile 所在目錄下的所有檔案複製到 Image 的工作目錄 /code 底下
ADD . /code

# 在 Image 中執行的指令
RUN apt update

RUN apt install -y ffmpeg

RUN apt install -y git

RUN pip install -r requirements.txt

RUN pip install --upgrade --force-reinstall git+https://github.com/ytdl-org/youtube-dl.git@master

# 啟動後通過 python 運行 main.py
CMD ["python", "./main.py"]
#到mumeu-bot資料夾後使用終端機執行docker build -t mumei-bot:latest .