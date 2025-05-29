FROM python:3.9-slim-buster

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    unzip \
    gnupg2 \
    ca-certificates \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# 添加 Google Chrome 签名密钥和源（不再使用 apt-key）
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

# 安装最新版 Chrome（不指定版本）
RUN apt-get update && apt-get install -y --no-install-recommends \
    google-chrome-stable \
    && rm -rf /var/lib/apt/lists/* \
    && chmod +x /usr/bin/google-chrome

# 安装匹配的 ChromeDriver（自动检测版本）
RUN CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+') \
    && CHROMEDRIVER_VERSION=$(wget -qO- https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json | \
        grep -A 20 "\"version\": \"${CHROME_VERSION}\"" | grep "linux64" | grep "chromedriver" | head -n1 | cut -d '"' -f 4) \
    && wget -q "${CHROMEDRIVER_VERSION}" -O chromedriver.zip \
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
