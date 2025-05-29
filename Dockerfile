FROM python:3.10-slim

# 设置工作目录为容器内的 /app 目录
WORKDIR /app

# 复制所有必要文件到容器内的 /app 目录（确保路径正确）
COPY config.json .   # 复制到 /app/config.json
COPY app.py .        # 复制到 /app/app.py

# 安装依赖前校验文件存在性和 JSON 格式
RUN python -c "import json, os; \
    if not os.path.exists('config.json'): raise FileNotFoundError('config.json 缺失'); \
    if not os.path.exists('app.py'): raise FileNotFoundError('app.py 缺失'); \
    with open('config.json', 'r') as f: json.load(f);"

# 安装 Python 依赖（使用官方源，避免网络问题）
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple \
    selenium==4.10.0 \
    requests==2.31.0

# 安装 Chrome 浏览器及驱动（用于无头浏览器）
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium-browser=1:116.0.5845.187-1 \
    chromium-driver=1:116.0.5845.187-0ubuntu1 \
    && rm -rf /var/lib/apt/lists/*

# 设置 Chrome 相关环境变量（与 Selenium 配置一致）
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver \
    CHROME_BIN=/usr/bin/chromium-browser \
    DISPLAY=:99  # 解决无头浏览器潜在问题（可选）

# 启动程序（确保脚本名称与复制的文件名一致）
CMD ["python", "app.py"]
