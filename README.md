# [nuru-bot](https://discord.com/api/oauth2/authorize?client_id=999157840063242330&permissions=8&scope=applications.commands+bot)
## Images tag
git tags are automatically built and updated after push.  
latest will be automatically updated when Releases are published.

## Introduction
Music function relies on FFmpeg, and FFmpeg must be installed on the system when used outside the container.  
After the container startup is completed, fill in the content of Token.toml (the default location is /opt/nuru-bot/toml/)  
The command can be directly referred to Help.toml(if i don't forget to update)  

## Startup
Docker compose <br>
```yml
services:
  nuru-bot:
    container_name: nuru-bot
    image: ghcr.io/aishukander/nuru-bot:latest
    restart: unless-stopped
    volumes:
      - /opt/nuru-bot/toml:/bot/toml
      - /opt/nuru-bot/CallPicture:/bot/CallPicture
```

Docker cli <br>
```bash
docker run -d \
--name=nuru-bot \
--restart=unless-stopped \
-v /opt/nuru-bot/json:/bot/json \
-v /opt/nuru-bot/CallPicture:/bot/CallPicture \
ghcr.io/aishukander/nuru-bot:latest
```
