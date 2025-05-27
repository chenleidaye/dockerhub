#!/bin/bash

touch /app/sync.log
> /app/sync.log

SYNC_CMD="python /app/main.py"

echo "欢迎进入交互模式！"
echo "输入 sync 执行同步（当前执行：$SYNC_CMD）"
echo "输入 cron 表达式（例如 * * * * * python /app/main.py）设置定时任务"
echo "输入 exit 退出"

while true; do
  read -p "> " input

  if [[ "$input" == "exit" ]]; then
    echo "退出..."
    break

  elif [[ "$input" == "sync" ]]; then
    echo "执行同步命令..."
    eval $SYNC_CMD

  else
    # 判断是否是 cron 表达式 + 命令
    if [[ "$input" =~ ^(\*|[0-9,-/]+)\ (\*|[0-9,-/]+)\ (\*|[0-9,-/]+)\ (\*|[0-9,-/]+)\ (\*|[0-9,-/]+)\ (.+)$ ]]; then
      echo "$input" > /tmp/mycron
      crontab /tmp/mycron
      service cron start
      echo "定时任务设置成功！当前 crontab:"
      crontab -l
    else
      echo "无效命令或格式，输入 exit 退出"
    fi
  fi
done
