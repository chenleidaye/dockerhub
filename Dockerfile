FROM python:3.9-slim

# 设置时区
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 安装依赖
RUN apt-get update && apt-get install -y \
    cron \
    gcc \
    python3-lxml \
    && rm -rf /var/lib/apt/lists/*

# 先复制cron文件
COPY cronjob /etc/cron.d/cronjob

# 再设置权限和创建日志文件
RUN touch /var/log/cron.log && \
    chmod 0644 /etc/cron.d/cronjob

# 复制其他文件
WORKDIR /app
COPY . /app

# 安装Python依赖
RUN pip install --no-cache-dir requests beautifulsoup4 lxml

# 入口点配置
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
