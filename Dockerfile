FROM python:3.9-slim-buster

WORKDIR /app

# 安装依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    unzip \
    gnupg2 \
    ca-certificates \
    fonts-liberation \
    jq \
    && rm -rf /var/lib/apt/lists/*

# 安装 Chrome（稳定最新）
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# 安装 ChromeDriver（直接匹配 chrome-stable 对应版本）
RUN CHROME_VERSION=$(apt-cache policy google-chrome-stable | grep Installed | awk '{print $2}' | cut -d '-' -f1) \
    && echo "Using Chrome version: $CHROME_VERSION" \
    && DRIVER_URL=$(wget -qO- https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json | \
        jq -r --arg ver "$CHROME_VERSION" '.channels.Stable.downloads.chromedriver[] | select(.platform=="linux64") | .url') \
    && wget -q "$DRIVER_URL" -O chromedriver.zip \
    && unzip chromedriver.zip -d /usr/local/bin/ \
    && rm chromedriver.zip \
    && chmod +x /usr/local/bin/chromedriver

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

CMD ["python", "wechat_ip_updater.py"]
