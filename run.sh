#!/bin/bash

# 创建环境变量文件
if [ ! -f .env ]; then
    echo "BOT_TOKEN=your_bot_token" > .env
    echo "CHAT_ID=your_chat_id" >> .env
    echo "CHECK_INTERVAL=300" >> .env
    echo "OVERWRITE=true" >> .env
    echo "TELEGRAM_PROXY=http://127.0.0.1:10808" >> .env
    echo "请编辑 .env 文件配置必要参数"
    exit 1
fi

# 构建Docker镜像
docker-compose build

# 启动容器
docker-compose up -d

# 显示容器状态
docker-compose ps    
