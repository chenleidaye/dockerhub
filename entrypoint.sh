#!/bin/bash
set -ex

# 初始化日志文件
LOG_FILE="/var/log/cron.log"
touch $LOG_FILE
chmod 666 $LOG_FILE

echo "🕒 当前时间: $(date)" | tee -a $LOG_FILE

# 应用环境变量
if [ -n "$BASE_URL" ]; then
    echo "🔄 设置BASE_URL为: $BASE_URL" | tee -a $LOG_FILE
    sed -i "s|^BASE_URL = .*|BASE_URL = \"$BASE_URL\"|" /app/main.py
fi

# 立即执行并记录详细日志
echo "🚀 开始首次同步..." | tee -a $LOG_FILE
if /usr/local/bin/python /app/main.py 2>&1 | tee -a $LOG_FILE; then
    echo "✅ 首次同步成功完成" | tee -a $LOG_FILE
else
    echo "❌ 首次同步失败，错误码: $?" | tee -a $LOG_FILE
fi

# 配置cron任务
echo "🔄 设置定时任务: $CRON_SCHEDULE" | tee -a $LOG_FILE
echo "$CRON_SCHEDULE /usr/local/bin/python /app/main.py >> $LOG_FILE 2>&1" > /etc/cron.d/cronjob
chmod 0644 /etc/cron.d/cronjob
crontab /etc/cron.d/cronjob

# 启动服务
echo "🔛 启动cron服务..." | tee -a $LOG_FILE
cron -f &
tail -f $LOG_FILE
