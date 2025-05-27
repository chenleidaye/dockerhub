import asyncio
import nest_asyncio
nest_asyncio.apply()

import os
import requests
import threading
import time
from bs4 import BeautifulSoup
from urllib.parse import unquote, urljoin, urlparse, parse_qs
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    filters
)
from telegram.request import HTTPXRequest

# -------------------- 代理配置函数 --------------------
def get_proxy_settings():
    """从环境变量获取代理配置"""
    proxy_url = os.getenv('HTTP_PROXY') or os.getenv('HTTPS_PROXY')
    
    if not proxy_url:
        return None
    
    parsed = urlparse(proxy_url)
    if not parsed.scheme or not parsed.hostname:
        raise ValueError(f"无效代理地址: {proxy_url}")
    
    return {'proxy_url': proxy_url}
# -----------------------------------------------------

# 配置参数
BASE_URL = os.getenv("BASE_URL", "https://5721004.xyz")
SAVE_ROOT = os.getenv("SAVE_ROOT", "strm_files")
TG_TOKEN = os.getenv("TG_TOKEN")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.isdigit()]
stop_event = threading.Event()

# 验证配置
if not TG_TOKEN:
    raise ValueError("必须设置TG_TOKEN环境变量")
if not ADMIN_IDS:
    raise ValueError("必须设置ADMIN_IDS环境变量，例如：ADMIN_IDS=123456789,987654321")

os.makedirs(SAVE_ROOT, exist_ok=True)

# 全局状态跟踪
class AppStatus:
    def __init__(self):
        self.is_scanning = False
        self.progress = {"current_dir": "无"}
        self.last_logs = []
        self.total_files = 0
        self.start_time = None
        self.visited_dirs = set()

app_status = AppStatus()
bot_app = None

# -------------------- 日志函数 --------------------
def log_message(message: str):
    """记录日志并保持最近记录"""
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    full_msg = f"[{timestamp}] {message}"
    app_status.last_logs.append(full_msg)
    if len(app_status.last_logs) > 100:
        app_status.last_logs.pop(0)
    print(full_msg)
# ------------------------------------------------

# [保持原有Telegram命令处理函数不变]...

# -------------------- 修复后的Bot初始化 --------------------
def run_bot():
    global bot_app
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 获取代理配置
        proxy = get_proxy_settings()
        request_config = {'connect_timeout': 30, 'read_timeout': 30}
        
        if proxy:
            request_config['proxy_url'] = proxy['proxy_url']
            log_message(f"🔧 使用代理: {proxy['proxy_url']}")
        
        # 创建Application实例
        application = Application.builder() \
            .token(TG_TOKEN) \
            .request(HTTPXRequest(**request_config)) \
            .build()
        bot_app = application

        # 注册命令处理器
        handlers = [
            CommandHandler("start", start),
            CommandHandler("scan", trigger_scan),
            CommandHandler("status", show_status),
            CommandHandler("logs", show_logs),
        ]
        
        for handler in handlers:
            application.add_handler(handler)

        # 异步任务包装器
        async def main_task():
            try:
                await application.initialize()
                await application.start()
                await application.updater.start_polling()
                
                while not stop_event.is_set():
                    await asyncio.sleep(1)
                
            finally:
                await application.stop()

        log_message("🤖 Telegram Bot 初始化成功")
        loop.run_until_complete(main_task())
        
    except Exception as e:
        error_msg = f"Bot 启动失败: {type(e).__name__}: {str(e)}"
        log_message(error_msg)
    finally:
        if loop.is_running():
            loop.close()
# -----------------------------------------------------------

# [保持其他功能函数不变]...

if __name__ == "__main__":
    # 启动Bot线程
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print("\n正在停止服务...")
        stop_event.set()
        bot_thread.join(timeout=5)
        print("服务已安全退出")
