#!/bin/bash
# cronctl.sh
# 用法示例：
# ./cronctl.sh "* * * * * python /app/main.py"

if [ $# -eq 0 ]; then
  echo "Usage: $0 \"* * * * * command\""
  exit 1
fi

expr="$1"

# 先把表达式写入临时文件
echo "$expr" > /tmp/mycron

# 安装 crontab
crontab /tmp/mycron

# 启动 cron 服务（后台）
service cron start

echo "已写入定时任务并启动cron："
crontab -l
