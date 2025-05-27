#!/bin/bash
set -e

# 应用环境变量到Python脚本
if [ -n "$BASE_URL" ]; then
    sed -i "s|^BASE_URL = .*|BASE_URL = \"$BASE_URL\"|" /app/main.py
fi

# 立即执行一次同步任务
echo "🚀 启动立即同步..."
/usr/local/bin/python /app/main.py >> /var/log/cron.log 2>&1 || true
echo "✅ 初始同步完成，开始定时任务..."

# 配置cron任务
echo "$CRON_SCHEDULE /usr/local/bin/python /app/main.py >> /var/log/cron.log 2>&1" > /etc/cron.d/cronjob
chmod 0644 /etc/cron.d/cronjob
crontab /etc/cron.d/cronjob

# 启动服务
echo "🕒 定时任务已设置：$CRON_SCHEDULE"
cron -f &
tail -f /var/log/cron.log
