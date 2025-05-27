FROM python:3.9-slim

ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update && apt-get install -y \
    cron \
    gcc \
    python3-lxml \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir requests beautifulsoup4 lxml

# 修复的配置部分
RUN touch /var/log/cron.log && \
    chmod 0644 /etc/cron.d/cronjob

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
