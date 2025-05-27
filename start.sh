#!/bin/bash

echo "0 */6 * * * python3 /app/app.py >> /app/cron.log 2>&1" > /etc/cron.d/strm-cron
crontab /etc/cron.d/strm-cron

cron

touch /app/cron.log   # <=== 先创建空日志文件

tail -f /app/cron.log
