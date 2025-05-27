FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 设置代理环境变量（替换成你自己的代理地址）
ENV HTTP_PROXY="http://your-proxy-host:port"
ENV HTTPS_PROXY="http://your-proxy-host:port"
ENV NO_PROXY="localhost,127.0.0.1"

# 给脚本赋执行权限
RUN chmod +x /app/run.sh

# 后台无限循环执行脚本，每小时执行一次
CMD ["bash", "-c", "while true; do /app/run.sh; sleep 3600; done"]
