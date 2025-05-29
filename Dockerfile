FROM python:3.10-slim
WORKDIR /app

# 先复制所有必要文件
COPY config.json .
COPY app.py .  # 提前复制 app.py，确保后续步骤能找到

# 安装依赖前校验配置
RUN python -c "import json, os; \
    if not os.path.exists('config.json'): raise FileNotFoundError('config.json 缺失'); \
    with open('config.json', 'r') as f: json.load(f);"

# 安装依赖
RUN pip install --no-cache-dir \
    selenium==4.10.0 \
    requests==2.31.0 \
    python-dotenv==1.0.0

# 复制 Python 脚本到容器
COPY app.py .

# 配置环境变量（建议通过环境变量传递敏感信息）
ENV BOT_TOKEN="your_telegram_bot_token" \
    CHAT_ID="your_chat_id" \
    TELEGRAM_PROXY="optional_proxy_url" \
    OVERWRITE="True" \
    CHECK_INTERVAL="60"

# 可选：安装 Chrome 浏览器及驱动（用于无头浏览器）
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium-browser \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# 设置 Chrome 驱动路径（与 Selenium 配置一致）
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
ENV CHROME_BIN=/usr/bin/chromium-browser

# 暴露端口（如果程序需要）
# EXPOSE 8080

# 启动程序
CMD ["python", "app.py"]
