# 使用官方python基础镜像
FROM python:3.11-slim

# 安装必要工具和Chrome浏览器
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    gnupg \
    fonts-liberation \
    libx11-xcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxrandr2 \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libgbm1 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libxss1 \
    libnss3 \
    libxshmfence1 \
    xdg-utils \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

# 安装 Chrome 浏览器（Google Chrome Stable）
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y google-chrome-stable

# 下载对应版本的chromedriver（这里以114版本为例，你要根据本地Chrome版本替换）
RUN CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+') && \
    DRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION") && \
    wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip" && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    rm /tmp/chromedriver.zip && \
    chmod +x /usr/local/bin/chromedriver

# 安装Python依赖
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# 复制脚本
COPY . /app
WORKDIR /app

# 创建挂载点目录，用于存放cookie和二维码图片
VOLUME ["/app/data"]

# 环境变量（可根据需要覆盖）
ENV BOT_TOKEN=""
ENV CHAT_ID=""
ENV CHECK_INTERVAL=1800
ENV OVERWRITE=True

# 启动脚本
CMD ["python", "main.py"]
