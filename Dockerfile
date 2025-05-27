FROM python:3.11-slim

# 设置时区（可选）
ENV TZ=Asia/Shanghai
RUN apt-get update && apt-get install -y cron curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY app/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ /app/

RUN chmod +x /app/run.sh

# 创建日志目录
RUN mkdir -p /app/log

# 容器启动时执行后台脚本，并用 sleep 定时循环
CMD ["bash", "-c", "\
while true; do \
  /app/run.sh; \
  sleep 3600; \  # 每小时执行一次，可根据需要调整间隔秒数
done"]
