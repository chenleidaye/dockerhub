import asyncio
import os
import threading
import time
from urllib.parse import urlparse

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
from telegram.request import HTTPXRequest



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
# -------------------- 代理配置函数 --------------------
def get_proxy_settings():
    proxy_url = os.getenv('HTTP_PROXY') or os.getenv('HTTPS_PROXY')
    if not proxy_url:
        return None
    parsed = urlparse(proxy_url)
    if not parsed.scheme or not parsed.hostname:
        raise ValueError(f"无效代理地址: {proxy_url}")
    return {'proxy_url': proxy_url}
# -----------------------------------------------------
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

def get_proxy_settings():
    proxy_url = os.getenv('HTTP_PROXY') or os.getenv('HTTPS_PROXY')
    if not proxy_url:
        return None
    parsed = urlparse(proxy_url)
    if not parsed.scheme or not parsed.hostname:
        raise ValueError(f"无效代理地址: {proxy_url}")
    return {'proxy_url': proxy_url}

async def main():
    proxy = get_proxy_settings()
    request_config = {'connect_timeout': 30, 'read_timeout': 30}
    if proxy:
        request_config['proxy_url'] = proxy['proxy_url']
        print(f"🔧 使用代理: {proxy['proxy_url']}")

    application = Application.builder() \
        .token(TG_TOKEN) \
        .request(HTTPXRequest(**request_config)) \
        .build()

    # 注册命令处理器
    handlers = [
        CommandHandler("start", start),
        CommandHandler("scan", trigger_scan),
        CommandHandler("status", show_status),
        CommandHandler("logs", show_logs),
    ]
    for handler in handlers:
        application.add_handler(handler)

    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    print("🤖 Telegram Bot 初始化成功")

    try:
        while not stop_event.is_set():
            await asyncio.sleep(1)
    finally:
        await application.stop()

def run_bot_thread():
    asyncio.run(main())

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot_thread, daemon=True)
    bot_thread.start()

    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print("\n正在停止服务...")
        stop_event.set()
        bot_thread.join(timeout=5)
        print("服务已安全退出")
