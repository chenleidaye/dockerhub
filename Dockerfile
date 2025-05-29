FROM python:3.9-slim-buster

WORKDIR /app
RUN mkdir -p /app/logs  # 创建日志目录

# 安装依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    unzip \
    gnupg2 \
    ca-certificates \
    fonts-liberation \
    jq \
    && rm -rf /var/lib/apt/lists/*

# 安装 Chrome 浏览器（固定为 114 版本，稳定不变）
# 安装 Chrome 浏览器（固定版本 137）
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends google-chrome-stable=137.0.7151.55-1 \
    && rm -rf /var/lib/apt/lists/*

# 安装 ChromeDriver（对应 137 版本）
RUN CHROMEDRIVER_VERSION=137.0.7151.55 \
    && wget -q "https://storage.googleapis.com/chrome-for-testing-public/${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip" -O chromedriver.zip \
    && unzip chromedriver.zip -d /usr/local/bin/ \
    && mv /usr/local/bin/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver \
    && rm -rf chromedriver.zip /usr/local/bin/chromedriver-linux64 \
    && chmod +x /usr/local/bin/chromedriver

RUN chmod +x /usr/local/bin/chromedriver


# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 环境变量
ENV BOT_TOKEN=your_bot_token
ENV CHAT_ID=your_chat_id
ENV CHECK_INTERVAL=300
ENV OVERWRITE=true
ENV TELEGRAM_PROXY=
ENV PYTHONUNBUFFERED=1

CMD ["python", "wechat_ip_updater.py"]
