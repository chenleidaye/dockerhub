# 使用官方Python基础镜像，带slim，节省空间
FROM python:3.11-slim

# 安装Chrome及依赖
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    fonts-liberation \
    libnss3 \
    libx11-6 \
    libx11-xcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libxshmfence1 \
    xdg-utils \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

# 下载并安装Chrome
RUN wget -q -O /tmp/google-chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    dpkg -i /tmp/google-chrome.deb || apt-get -f install -y && \
    rm /tmp/google-chrome.deb

# 安装ChromeDriver
ARG CHROMEDRIVER_VERSION=116.0.5845.96
RUN wget -q -O /tmp/chromedriver_linux64.zip https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip && \
    unzip /tmp/chromedriver_linux64.zip -d /usr/local/bin/ && \
    rm /tmp/chromedriver_linux64.zip && \
    chmod +x /usr/local/bin/chromedriver

# 设置环境变量，避免字体缺失警告
ENV LANG=C.UTF-8

# 复制依赖文件并安装
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制脚本文件
COPY app.py .

# 允许容器访问X服务器（无头模式一般不需要）
# 设置Chrome无头参数由代码内指定

# 入口运行程序
CMD ["python", "app.py"]
