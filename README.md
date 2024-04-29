# mumei-bot
邀請連結:[點這裡](https://discord.com/api/oauth2/authorize?client_id=999157840063242330&permissions=8&scope=applications.commands+bot)    
這是一個我使用python製做的discord bot  
在對話框輸入~adminhelp來獲取所有的指令(包括管理者限定指令)  
要下載一般最新版本請點Release,選最上面的版本然後下載mumei-bot.zip  
要下載最新測試版請點[這裡](https://github.com/aishukander/mumei-bot/archive/refs/heads/main.zip)  
---------------------------------------------------------------------------------------------  
windows請安裝ffmpeg並啟動rely.ps1  
linux(Debian)請啟動rely.sh  
---------------------------------------------------------------------------------------------  
於json資料夾內新稱 token.json 並放入以下對應資料  
"BOT_TOKEN":"",  
"GOOGLE_AI_KEY":""  
---------------------------------------------------------------------------------------------  
Docker compose
```
version: "3"

services:
  mumei-bot:
    container_name:mumei-bot
    image: aishukander/mumei-bot
    restart: unless-stopped
    volumes:
      - /etc/mumei-bot/json:/code/json
```
Docker cli  
```
docker run -d --name=mumei-bot --restart=unless-stopped -v /etc/mumei-bot/json:/code/json aishukander/mumei-bot

```
---------------------------------------------------------------------------------------------  
