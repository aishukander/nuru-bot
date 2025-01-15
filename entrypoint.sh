#!/bin/bash

if [ -d '/tmp/data' ] && [ -d /bot/json/ ] && [ ! "$(ls -A /bot/json/)" ]; then
    cp -r /tmp/data/* /bot/json/
fi

rm -rf /tmp/data
exec python /bot/main.py