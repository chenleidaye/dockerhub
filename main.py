import os
import requests
import asyncio
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

# 配置参数
BASE_URL = os.getenv("BASE_URL", "https://5721004.xyz")
SAVE_ROOT = os.getenv("SAVE_ROOT", "strm_files")
TG_TOKEN = os.getenv("TG_TOKEN")  # 必须设置
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.isdigit()]

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
bot_app = None  # 全局Bot应用实例

# Telegram Bot 功能 ----------------------------------------------------------
async def send_notification(message: str):
    """发送通知给所有管理员"""
    if not bot_app:
        return
    
    for chat_id in ADMIN_IDS:
        try:
            await bot_app.bot.send_message(
                chat_id=chat_id,
                text=message
            )
        except Exception as e:
            print(f"Telegram通知发送失败: {e}")

def sync_notify(message: str):
    """线程安全的通知发送"""
    asyncio.run_coroutine_threadsafe(
        send_notification(message),
        bot_app._event_loop
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ 未授权访问")
        return
    help_text = (
        "🤖 STRM生成器监控面板\n"
        "可用命令：\n"
        "/start - 显示帮助\n"
        "/scan - 启动扫描\n"
        "/status - 当前状态\n"
        "/logs - 最近日志\n"
        "/cancel - 取消任务"
    )
    await update.message.reply_text(help_text)

async def trigger_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    if app_status.is_scanning:
        await update.message.reply_text("🔍 已有扫描任务进行中")
        return
    
    await update.message.reply_text("🔄 开始后台扫描...")
    threading.Thread(target=main_scan_task).start()

async def show_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = []
    status.append(f"📊 扫描状态: {'🔄 进行中' if app_status.is_scanning else '💤 空闲'}")
    
    if app_status.is_scanning:
        duration = int(time.time() - app_status.start_time)
        status.append(f"⏳ 运行时间: {duration}秒")
        status.append(f"📂 已生成文件: {app_status.total_files}")
        status.append(f"📍 当前目录: {app_status.progress['current_dir']}")
    
    await update.message.reply_text("\n".join(status))

async def show_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logs = app_status.last_logs[-10:] or ["暂无日志"]
    await update.message.reply_text("📜 最近日志：\n" + "\n".join(logs))

def log_message(message: str):
    """记录日志并保持最近记录"""
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    full_msg = f"[{timestamp}] {message}"
    app_status.last_logs.append(full_msg)
    if len(app_status.last_logs) > 100:
        app_status.last_logs.pop(0)
    print(full_msg)  # 同时输出到控制台

# 核心扫描功能 ---------------------------------------------------------------
def should_update_file(file_path: str, new_content: str) -> bool:
    """检查文件是否需要更新"""
    if not os.path.exists(file_path):
        return True
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip() != new_content.strip()
    except Exception:
        return True

def get_real_url(m3u8_url: str) -> str:
    """解析真实播放地址"""
    parsed = urlparse(m3u8_url)
    query = parse_qs(parsed.query)
    
    if 'path' in query:
        base = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        return urljoin(base + "/", query['path'][0].lstrip('/'))
    return m3u8_url

def url_to_local_path(url: str) -> str:
    """转换URL到本地路径"""
    parsed = urlparse(url)
    path_segs = [seg for seg in unquote(parsed.path).split('/') if seg]
    
    # 处理查询参数
    if parsed.query:
        query_segs = [seg for seg in unquote(parsed.query).split('/') if seg]
        path_segs.extend(query_segs)
    
    # 定位关键目录
    markers = {'bu', 's2', 's3', 's4', 's5', 'pc', 'pc2', 'pc3', 'pc4'}
    start_idx = next((i for i, seg in enumerate(path_segs) if seg.lower() in markers), 0)
    
    return os.path.join(SAVE_ROOT, *path_segs[start_idx:])

def process_directory(dir_url: str) -> int:
    """处理单个目录"""
    if dir_url in app_status.visited_dirs:
        return 0
    app_status.visited_dirs.add(dir_url)
    
    log_message(f"进入目录: {dir_url}")
    sync_notify(f"📂 扫描目录: {dir_url}")
    
    try:
        response = requests.get(dir_url, headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": BASE_URL
        }, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8'
    except Exception as e:
        log_message(f"目录访问失败: {dir_url} - {str(e)}")
        return 0

    try:
        soup = BeautifulSoup(response.text, "lxml")
    except Exception as e:
        log_message(f"解析失败: {dir_url} - {str(e)}")
        return 0

    # 收集M3U8文件
    m3u8_files = []
    for a in soup.select('a.video[data-src]'):
        data_src = a.get("data-src", "")
        if not data_src:
            continue
        
        # 屏蔽特定文件
        filename = unquote(data_src.split("/")[-1].split("?")[0])
        if filename.lower() == "jinricp.m3u8":
            log_message(f"🚫 已屏蔽文件: {filename}")
            continue
        
        m3u8_url = urljoin(dir_url, data_src)
        strm_filename = filename.replace(".m3u8", ".strm")
        m3u8_files.append((strm_filename, m3u8_url))
    
    # 生成STRM文件
    count = 0
    if m3u8_files:
        local_dir = url_to_local_path(dir_url)
        os.makedirs(local_dir, exist_ok=True)
        log_message(f"创建本地目录: {local_dir}")

        for filename, url in m3u8_files:
            file_path = os.path.join(local_dir, filename)
            real_url = get_real_url(url)
            
            if should_update_file(file_path, real_url):
                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(real_url)
                    action = "更新" if os.path.exists(file_path) else "新建"
                    log_message(f"文件{action}: {filename}")
                    count += 1
                except Exception as e:
                    log_message(f"文件写入失败: {filename} - {str(e)}")

    # 处理子目录
    sub_dirs = []
    for li in soup.select('li.mdui-list-item.mdui-ripple'):
        a = li.find('a')
        if not a or not (href := a.get('href')):
            continue
        
        if href.startswith(('javascript:', '#')):
            continue
        
        sub_url = urljoin(dir_url, href)
        if 'sample' in sub_url.lower():
            continue
        
        if any(ext in href.lower() for ext in ['.m3u8', '.jpg', '.png']):
            continue
        
        if any(marker in sub_url for marker in ['bu/', 's2/', 'pc/']):
            sub_dirs.append(sub_url)

    # 递归处理子目录
    for sub_url in sub_dirs:
        count += process_directory(sub_url)

    return count

def get_root_dirs():
    """获取初始扫描目录"""
    try:
        response = requests.get(BASE_URL, headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": BASE_URL
        }, timeout=10)
        response.raise_for_status()
    except Exception as e:
        log_message(f"主页访问失败: {str(e)}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    dirs = []
    
    for a in soup.select('a.mdui-list-item.mdui-ripple'):
        href = a.get('href', '')
        if href.startswith('/') and href.endswith('/'):
            full_url = urljoin(BASE_URL, href)
            if any(marker in full_url for marker in ['bu/', 's2/', 'pc/']):
                dirs.append(full_url)
    
    return dirs

def main_scan_task():
    """主扫描任务"""
    app_status.is_scanning = True
    app_status.start_time = time.time()
    app_status.total_files = 0
    app_status.visited_dirs.clear()
    
    try:
        log_message("🚀 扫描任务启动")
        sync_notify("📡 开始扫描网站内容...")

        root_dirs = get_root_dirs() or [f"{BASE_URL}/s2/"]
        total = 0
        
        for idx, url in enumerate(root_dirs):
            app_status.progress["current_dir"] = url
            count = process_directory(url)
            total += count
            app_status.total_files = total
            sync_notify(f"✅ 完成目录 {idx+1}/{len(root_dirs)}\n生成文件: {count}")

        msg = (
            f"🎉 扫描完成！\n"
            f"总文件数: {total}\n"
            f"耗时: {int(time.time() - app_status.start_time)}秒"
        )
        log_message(msg)
        sync_notify(msg)

    except Exception as e:
        error_msg = f"🚨 扫描出错: {str(e)}"
        log_message(error_msg)
        sync_notify(error_msg)
    finally:
        app_status.is_scanning = False
        app_status.start_time = None

# Bot初始化 ----------------------------------------------------------------
def run_bot():
    global bot_app
    try:
        # 创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 初始化应用
        application = Application.builder().token(TG_TOKEN).build()
        bot_app = application

        # 注册命令处理器
        cmd_handlers = [
            CommandHandler("start", start),
            CommandHandler("scan", trigger_scan),
            CommandHandler("status", show_status),
            CommandHandler("logs", show_logs),
        ]
        
        for handler in cmd_handlers:
            application.add_handler(handler)

        # 正确运行异步协程
        print("🤖 Telegram Bot 初始化成功")
        loop.run_until_complete(application.run_polling())
        
    except Exception as e:
        print(f"Bot 启动失败: {str(e)}")
    finally:
        # 清理事件循环
        loop.close()

# 在文件开头添加异步支持
async def main():
    await application.run_polling()

# 主程序 -------------------------------------------------------------------
if __name__ == "__main__":
    # 启动Bot线程
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # 保持主线程运行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sync_notify("🔴 服务已手动停止")
        print("\n服务已关闭")
