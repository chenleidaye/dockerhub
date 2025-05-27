#!/bin/bash
set -e

# 如果设置了环境变量CRON_SCHEDULE，则更新cron任务
if [ -n "$CRON_SCHEDULE" ]; then
    echo "Updating cron schedule to: $CRON_SCHEDULE"
    echo "$CRON_SCHEDULE /usr/local/bin/python /app/main.py >> /var/log/cron.log 2>&1" > /etc/cron.d/cronjob
fi

# 应用环境变量到Python脚本
if [ -n "$BASE_URL" ]; then
    sed -i "s|^BASE_URL = .*|BASE_URL = \"$BASE_URL\"|" /app/main.py
fi

# 启动cron服务
echo "Starting cron service..."
cron -f &
tail -f /var/log/cron.log
