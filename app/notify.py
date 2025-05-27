import requests
import os

TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")

def send_message(text):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print("⚠️ Telegram TOKEN 或 CHAT ID 未设置，跳过通知")
        return
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    try:
        resp = requests.post(url, data={"chat_id": TG_CHAT_ID, "text": text})
        if resp.status_code == 200:
            print("✅ Telegram 通知发送成功")
        else:
            print(f"❌ Telegram 通知失败: {resp.text}")
    except Exception as e:
        print(f"❌ Telegram 通知异常: {e}")
