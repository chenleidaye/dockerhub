FROM python:3.9-slim-buster

WORKDIR /app

# 安装系统依赖（含字体，避免截图报错）
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    unzip \
    gnupg2 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# 安装 Chrome 浏览器（指定稳定版本，避免动态解析）
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update && apt-get install -y --no-install-recommends \
    google-chrome-stable=114.0.5735.91-1 \
    && rm -rf /var/lib/apt/lists/* \
    && chmod +x /usr/bin/google-chrome-stable

# 安装 ChromeDriver（使用国内镜像源，如阿里云）
RUN CHROME_VERSION=114.0.5735.91 \
    && CHROMEDRIVER_VERSION=$(wget -qO- https://cdn.npm.taobao.org/dist/chromedriver/LATEST_RELEASE_${CHROME_VERSION}) \
    && wget -q https://cdn.npm.taobao.org/dist/chromedriver/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip \
    -O chromedriver_linux64.zip \
    && unzip chromedriver_linux64.zip -d /usr/local/bin/ \
    && rm chromedriver_linux64.zip \
    && chmod +x /usr/local/bin/chromedriver

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 环境变量（与之前一致）
ENV BOT_TOKEN=your_bot_token
ENV CHAT_ID=your_chat_id
ENV CHECK_INTERVAL=300
ENV OVERWRITE=true
ENV TELEGRAM_PROXY=

CMD ["python", "wechat_ip_updater.py"]
