#!/bin/bash

if [ -d '/tmp/toml' ] && [ -d /bot/toml/ ] && [ ! "$(ls -A /bot/toml/)" ]; then
    cp -r /tmp/toml/* /bot/toml/
fi

rm -rf /tmp/toml
exec python /bot/main.py