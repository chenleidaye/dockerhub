FROM python:3.9-slim

# 设置时区
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    cron \
    gcc \
    python3-lxml \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app
COPY . /app

# 安装Python依赖
RUN pip install --no-cache-dir requests beautifulsoup4 lxml

# 设置cron和权限
RUN touch /var/log/cron.log \
    && chmod 0644 /etc/cron.d/cronjob \
    && crontab /etc/cron.d/cronjob

# 设置入口点
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
