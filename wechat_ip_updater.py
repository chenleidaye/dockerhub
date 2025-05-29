import re
import time
import os
import requests
import schedule
import pytz
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service

# ==================== 配置区域 ====================
BOT_TOKEN = os.getenv("BOT_TOKEN", "BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID", "CHAT_ID")
COOKIE_FILE = "wechat_cookie.txt"  # Cookie保存文件
QR_IMAGE_PATH = 'wechat_qrcode.png'  # 二维码保存路径

# 新增：应用ID变量（可配置多个，用逗号分隔）
APP_IDS = os.getenv("APP_IDS", "123456789,23456789").split(',')
BASE_URL = "https://work.weixin.qq.com/wework_admin/frame#/apps/modApiApp/"

# 自动生成完整URL列表
wechat_urls = [BASE_URL + app_id.strip() for app_id in APP_IDS if app_id.strip()]

ip_urls = [
    "https://myip.ipip.net",
    "https://ddns.oray.com/checkip",
    "https://ip.3322.net",
    "https://4.ipw.cn"
]
ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'

overwrite = os.getenv("OVERWRITE", "true").lower() == "true"
check_interval = int(os.getenv("CHECK_INTERVAL", "60"))
driver = None
current_ip_address = "0.0.0.0"
telegram_proxy = os.getenv("TELEGRAM_PROXY", None)
# =================================================

def load_cookie():
    """从文件加载Cookie"""
    if os.path.exists(COOKIE_FILE):
        with open(COOKIE_FILE, "r") as f:
            return f.read().strip()
    return ""

def save_cookie(cookie):
    """保存Cookie到文件"""
    with open(COOKIE_FILE, "w") as f:
        f.write(cookie)

def send_telegram_message(text, notification_type="info"):
    """发送美观的Telegram通知"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    proxies = {"http": telegram_proxy, "https": telegram_proxy} if telegram_proxy else None
    
    # 根据通知类型设置表情符号
    emojis = {
        "success": "✅",
        "error": "❌",
        "warning": "⚠️",
        "info": "ℹ️",
        "login": "🔑",
        "ip": "🌐",
        "qr": "📲"
    }
    
    # 创建美观的Markdown消息
    header = {
        "success": f"{emojis['success']} *操作成功* {emojis['success']}",
        "error": f"{emojis['error']} *发生错误* {emojis['error']}",
        "warning": f"{emojis['warning']} *需要注意* {emojis['warning']}",
        "info": f"{emojis['info']} *系统通知* {emojis['info']}",
        "login": f"{emojis['login']} *登录信息* {emojis['login']}",
        "ip": f"{emojis['ip']} *IP地址更新* {emojis['ip']}",
        "qr": f"{emojis['qr']} *登录二维码* {emojis['qr']}"
    }
    
    # 格式化消息内容
shanghai_tz = pytz.timezone('Asia/Shanghai')
now = datetime.now(shanghai_tz).strftime('%Y-%m-%d %H:%M:%S')

formatted_text = (
    f"{header.get(notification_type, header['info'])}\n"
    f"══════════════════════════\n"
    f"{text}\n"
    f"══════════════════════════\n"
    f"_🕒 {now}_"
)
    
    payload = {
        "chat_id": CHAT_ID, 
        "text": formatted_text, 
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload, proxies=proxies, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"[X] Telegram消息发送失败: {e}")
        return False

def send_telegram_image(image_path, caption=""):
    """发送图片到Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    proxies = {"http": telegram_proxy, "https": telegram_proxy} if telegram_proxy else None
    
    with open(image_path, 'rb') as photo:
        files = {"photo": photo}
        data = {"chat_id": CHAT_ID, "caption": caption, "parse_mode": "Markdown"}
        try:
            response = requests.post(url, files=files, data=data, proxies=proxies, timeout=20)
            return response.status_code == 200
        except Exception as e:
            print(f"[X] Telegram图片发送失败: {e}")
            return False

def get_ip_from_url(url):
    """从指定URL获取公网IP"""
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            match = re.search(ip_pattern, r.text)
            if match:
                return match.group()
        return None
    except Exception as e:
        print(f"[X] 请求失败 {url}: {e}")
        return None

def get_current_ip():
    """从多个服务获取当前公网IP"""
    for url in ip_urls:
        ip = get_ip_from_url(url)
        if ip:
            print(f"[√] 获取公网IP成功: {ip}")
            return ip
    print("[X] 所有IP服务均失败")
    return None

def capture_wechat_qrcode(driver):
    """获取企业微信登录二维码并发送到Telegram"""
    try:
        url = "https://work.weixin.qq.com/wework_admin/loginpage_wx"
        driver.get(url)
        print("[*] 打开企业微信登录页，等待二维码显示...")
        
        # 等待二维码加载：等待iframe出现
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#wx_reg iframe')))
        
        # 获取 iframe 并切换
        iframe = driver.find_element(By.CSS_SELECTOR, '#wx_reg iframe')
        driver.switch_to.frame(iframe)
        
        # 添加等待，确保二维码已渲染完成
        qrcode_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'img')))
        
        # 等待二维码的实际显示，增加合理的时间
        time.sleep(2)  # 这里可以根据实际情况稍作调整
        
        # 获取 QR 码并截图
        qrcode_element.screenshot(QR_IMAGE_PATH)
        print(f"[+] 二维码已截图保存为 {QR_IMAGE_PATH}")

        driver.switch_to.default_content()  # 切回主页面
        
        # 发送二维码到Telegram
        caption = (
            "🔑 *企业微信登录二维码*\n"
            "══════════════════════════\n"
            "1. 打开企业微信APP\n"
            "2. 点击右上角+\n"
            "3. 选择'扫一扫'\n"
            "4. 扫描此二维码登录\n"
            "══════════════════════════\n"
            f"_🕒 {time.strftime('%Y-%m-%d %H:%M:%S')}_"
        )
        
        if send_telegram_image(QR_IMAGE_PATH, caption):
            print("[√] 二维码已发送到Telegram，请扫码登录")
            send_telegram_message("请使用企业微信APP扫描二维码登录，二维码将在5分钟后失效", "qr")
            return True
        else:
            print("[X] 二维码发送失败")
            return False
            
    except Exception as e:
        print(f"[-] 获取二维码失败: {e}")
        return False

def handle_login(driver):
    """处理登录流程并保存新Cookie"""
    try:
        # 获取并发送二维码
        if not capture_wechat_qrcode(driver):
            return None
        
        # 等待登录成功
        print("[*] 等待扫码登录...")
        WebDriverWait(driver, 300).until(
            EC.url_contains("wework_admin/frame")
        )
        print("[√] 登录成功")
        
        # 保存新Cookie
        cookies = driver.get_cookies()
        cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
        save_cookie(cookie_str)
        print(f"[√] Cookie已保存到 {COOKIE_FILE}")
        
        # 发送登录成功通知
        send_telegram_message("企业微信登录成功！Cookie已保存，后续将自动使用保存的Cookie", "success")
        
        return driver
        
    except TimeoutException:
        print("[X] 登录超时，二维码已过期")
        send_telegram_message("登录超时，二维码已过期，请重新启动程序获取新二维码", "error")
        return None
    except Exception as e:
        print(f"[X] 登录处理失败: {e}")
        send_telegram_message(f"登录处理失败: {str(e)}", "error")
        return None

from selenium.webdriver.chrome.service import Service  # 新增导入

def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')  # 禁用沙箱
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--incognito')
    options.add_argument('--disable-dev-shm-usage')  # 关键：禁用 /dev/shm 共享内存
    options.add_argument('--disable-accelerated-2d-canvas')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--memory-pressure-off')  # 关闭内存压力管理
    
    # 设置较低的内存限制（根据容器资源调整）
    options.add_argument('--disable-features=VizDisplayCompositor')
    options.add_argument('--disable-features=IsolateOrigins,site-per-process')

    chrome_driver_path = os.getenv("CHROME_DRIVER_PATH", "/usr/local/bin/chromedriver")
    service = Service(chrome_driver_path)  # 创建 Service 对象
    
    # 关键：通过 service 参数传递驱动路径，无 executable_path
    driver = webdriver.Chrome(service=service, options=options)
    
    # 加载 Cookie 逻辑不变...
    cookie_str = load_cookie()
    if cookie_str:
        driver.get("https://work.weixin.qq.com/")
        for cookie in cookie_str.split('; '):
            if '=' not in cookie:
                continue
            name, value = cookie.split('=', 1)
            driver.add_cookie({"name": name, "value": value})
    
    # 验证登录状态不变...
    driver.get(wechat_urls[0])
    time.sleep(3)
    
    try:
        driver.find_element(By.CLASS_NAME, 'login_stage_title_text')
        print("[!] Cookie已失效，需要重新登录")
        send_telegram_message("保存的Cookie已失效，需要重新登录企业微信", "warning")
        return handle_login(driver)
    except:
        print("[√] Cookie有效，登录成功")
        return driver

def update_ip(driver, new_ip):
    """更新企业微信可信IP"""
    try:
        setip = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//div[contains(@class, "app_card_operate") and contains(@class, "js_show_ipConfig_dialog")]'))
        )
        setip.click()
        
        input_area = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//textarea[@class="js_ipConfig_textarea"]'))
        )
        confirm_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//a[contains(@class, "js_ipConfig_confirmBtn")]'))
        )
        
        if overwrite:
            input_area.clear()
            input_area.send_keys(new_ip)
            mode = "覆盖模式"
        else:
            existing = input_area.get_attribute("value")
            if new_ip in existing:
                print(f"[!] {new_ip} 已存在，跳过更新")
                return False, "IP已存在"
            input_area.send_keys(f";{new_ip}")
            mode = "追加模式"
        
        confirm_btn.click()
        time.sleep(1)
        return True, mode
    except Exception as e:
        print(f"[X] IP更新失败: {e}")
        return False, str(e)

def update_all_apps_ip(driver, new_ip):
    """更新所有应用的IP"""
    success_count = 0
    total = len(wechat_urls)
    details = []
    
    for i, url in enumerate(wechat_urls, 1):
        app_id = url.split("/")[-1]
        print(f"[*] 正在更新应用 {i}/{total} (ID: {app_id}): {url}")
        driver.get(url)
        time.sleep(2)
        success, message = update_ip(driver, new_ip)
        status = "✅ 成功" if success else "❌ 失败"
        details.append(f"{i}. {status} - {message}")
        
        if success:
            success_count += 1
            print(f"[√] 应用 {i} (ID: {app_id}) 更新成功")
        else:
            print(f"[X] 应用 {i} (ID: {app_id}) 更新失败: {message}")
    
    # 创建美观的更新报告
    report = (
        f"🌐 *新IP地址*: `{new_ip}`\n"
        f"🔧 *更新模式*: {'覆盖模式' if overwrite else '追加模式'}\n"
        f"══════════════════════════\n"
        f"📊 *更新结果*: {success_count}/{total} 个应用成功\n"
        f"══════════════════════════\n"
    )
    
    # 添加每个应用的更新详情
    report += "\n".join(details)
    
    if success_count > 0:
        send_telegram_message(report, "ip")
    else:
        send_telegram_message(report, "error")
    
    return success_count


def job():
    global driver, current_ip_address
    new_ip = get_current_ip()
    
    if new_ip != current_ip_address:
        print(f"[INFO] 公网 IP 发生变化：{current_ip_address} → {new_ip}")
        if not driver:
            driver = init_driver()
        update_all_apps_ip(driver, new_ip)
        current_ip_address = new_ip
    else:
        print(f"[INFO] 公网 IP 无变化，仍为：{new_ip}，刷新页面保持登录")
        if not driver:
            driver = init_driver()
        keep_session_alive(driver)
        
def keep_session_alive(driver):
    try:
        driver.get("https://work.weixin.qq.com/")
        print("[√] 已刷新页面以保持会话活跃")
    except Exception as e:
        print(f"[X] 刷新页面失败: {e}")
        
def main_loop():
    global driver, current_ip_address
    schedule.every(3).minutes.do(job)
    print("[INFO] 企业微信 IP 自动更新服务已启动，定时任务每 3 分钟执行一次")

    last_ip_check = time.time() - check_interval  # 强制第一次检查
    
    print("====== 企业微信可信IP自动更新程序 ======")
    print(f"检查间隔: {check_interval//60} 分钟")
    print(f"覆盖模式: {'开启' if overwrite else '追加'}")
    print(f"监控应用数: {len(wechat_urls)}")
    print("="*50)
    
    # 发送启动通知
    send_telegram_message("企业微信可信IP自动更新程序已启动", "info")
    
    while True:
        try:
            current_time = time.time()
            if current_time - last_ip_check < check_interval:
                sleep_time = check_interval - (current_time - last_ip_check)
                print(f"[*] 下次检查在 {int(sleep_time//60)} 分 {int(sleep_time%60)} 秒后...")
                time.sleep(min(sleep_time, 60))
                continue
            last_ip_check = current_time
            
            job()  # 调用job，统一处理IP更新
            
        except KeyboardInterrupt:
            print("\n[!] 程序被用户中断")
            send_telegram_message("程序已被手动终止", "warning")
            if driver:
                driver.quit()
            break
        except Exception as e:
            print(f"[X] 主循环异常: {e}")
            send_telegram_message(f"主循环发生异常:\n```\n{str(e)}\n```\n程序将在60秒后重试", "error")
            if driver:
                driver.quit()
                driver = None
            time.sleep(60)

if __name__ == '__main__':
    try:
        main_loop()
    except Exception as e:
        print(f"[X] 程序崩溃: {e}")
        send_telegram_message(f"程序发生崩溃:\n```\n{str(e)}\n```\n请检查系统状态", "error")    
