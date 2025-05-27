FROM python:3.10-slim

# 安装 cron
RUN apt-get update && apt-get install -y cron

# 创建工作目录
WORKDIR /app

# 复制文件
COPY main.py /app/main.py
COPY cronctl.sh /cronctl.sh
COPY requirements.txt /app/requirements.txt

# 权限 & 日志文件
RUN chmod +x /cronctl.sh && touch /app/sync.log

# 安装依赖
RUN pip install --no-cache-dir -r /app/requirements.txt

# 启动交互脚本
CMD ["/bin/bash", "/cronctl.sh"]
