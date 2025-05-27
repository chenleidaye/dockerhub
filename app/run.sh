#!/bin/bash
set -e

# 每次执行脚本时，将日志写到日志文件
LOGFILE="/app/log/crawler_$(date +'%Y%m%d_%H%M%S').log"
mkdir -p /app/log

echo "开始执行爬取任务: $(date)" | tee -a "$LOGFILE"

# 执行爬虫
python3 /app/crawler.py 2>&1 | tee -a "$LOGFILE"
RET=$?

# 发送通知
if [ $RET -eq 0 ]; then
  MSG="✅ 爬取任务完成，详情见日志。"
else
  MSG="❌ 爬取任务失败，详情见日志。"
fi

python3 -c "
import notify
notify.send_message('$MSG')
" || echo "通知发送失败"

# 这里可以添加同步命令，比如 rsync、rclone 同步到远程目录
# 例如：
# rsync -avz /app/strm_files/ user@remote:/path/to/target/

echo "任务结束: $(date)" | tee -a "$LOGFILE"
