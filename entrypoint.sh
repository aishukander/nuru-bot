#!/bin/bash

if [ -d '/tmp/json' ] && [ -d /bot/json/ ] && [ ! "$(ls -A /bot/json/)" ]; then
    cp -r /tmp/json/* /bot/json/
fi

rm -rf /tmp/json
exec python /bot/main.py