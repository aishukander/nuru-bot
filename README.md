# [nuru-bot](https://discord.com/api/oauth2/authorize?client_id=999157840063242330&permissions=8&scope=applications.commands+bot)
要下載一般最新版本請點Release,選最上面的版本然後下載nuru-bot.zip <br>
[要下載最新測試版請點這裡](https://github.com/aishukander/nuru-bot/archive/refs/heads/main.zip) <br>

## 初始化
音樂功能依賴FFmpeg，容器外使用時系統必需安裝FFmpeg。 <br>
容器啟動完成後將Token.json的內容填上即可（預設位置在/opt/nuru-bot/json/）。 <br>

## 啟動
Docker compose <br>
```yml
services:
  nuru-bot:
    container_name: nuru-bot
    image: aishukander/nuru-bot
    restart: unless-stopped
    volumes:
      - /opt/nuru-bot/json:/bot/json
      - /opt/nuru-bot/CallPicture:/bot/CallPicture
```

Docker cli <br>
```bash
docker run -d \
--name=nuru-bot \
--restart=unless-stopped \
-v /opt/nuru-bot/json:/bot/json \
-v /opt/nuru-bot/CallPicture:/bot/CallPicture \
aishukander/nuru-bot
```
