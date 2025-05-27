# 使用官方Python基础镜像
FROM python:3.9-slim

# 设置时区（中国用户需要）
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 安装系统依赖（合并为一个RUN指令）
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    curl \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# 创建工作目录
WORKDIR /app

# 复制项目文件
COPY . .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 设置权限
RUN chmod +x /app/main.py

# 定义启动命令
CMD ["python", "main.py"]
