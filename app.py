from flask import Flask, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os, re

app = Flask(__name__)

# LINE BOT 設定
LINE_CHANNEL_ACCESS_TOKEN = "你的 Channel Access Token"
LINE_CHANNEL_SECRET = "你的 Channel Secret"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 活動儲存
activities = {}

# 根路由（測試用）
@app.route("/", methods=["GET"])
def home():
    return "Line Bot Signup is Running!"

# Webhook 接收 LINE 訊息
@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return "Invalid Signature", 400
    return "OK", 200

# 解析 LINE 訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text.strip()
    reply_text = process_message(user_message)
    if reply_text:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

# 訊息處理邏輯
def process_message(text):
    global activities

    # 新增活動：新增+活動名稱（+人數限制）
    match = re.match(r"^新增\s*(\S+)(?:\s*(\d+)人)?$", text)
    if match:
        activity_name = match.group(1)
        limit = int(match.group(2)) if match.group(2) else None
        if activity_name in activities:
            return "活動已存在!"
        activities[activity_name] = {"limit": limit, "participants": []}
        return f"活動 '{activity_name}' 已建立{f'，最多 {limit} 人' if limit else ''}。"

    # 報名活動
    for activity in activities:
        if text.startswith(activity):
            names = re.findall(r"(\S+)(?:（(.*?)）)?", text[len(activity):].strip())
            if not names:
                return "請輸入有效的報名資訊。"
            for name, item in names:
                if activities[activity]["limit"] and len(activities[activity]["participants"]) >= activities[activity]["limit"]:
                    return "報名人數已滿!"
                activities[activity]["participants"].append((name, item))
            return "報名成功!"

    # 截止活動：截止+活動名稱
    match = re.match(r"^截止\s*(\S+)$", text)
    if match:
        activity_name = match.group(1)
        if activity_name not in activities:
            return "活動不存在!"
        participants = activities[activity_name]["participants"]
        del activities[activity_name]
        return f"{activity_name} 報名名單:\n" + "\n".join(f"{i+1}. {name}{f'（{item}）' if item else ''}" for i, (name, item) in enumerate(participants))

    # 取消報名：取消+活動名稱+姓名
    match = re.match(r"^取消\s*(\S+)\s*(\S+)$", text)
    if match:
        activity_name, name = match.groups()
        if activity_name not in activities:
            return "活動不存在!"
        activities[activity_name]["participants"] = [p for p in activities[activity_name]["participants"] if p[0] != name]
        return f"{name} 已取消報名 {activity_name}。"

    # 刪除活動：刪除+活動名稱
    match = re.match(r"^刪除\s*(\S+)$", text)
    if match:
        activity_name = match.group(1)
        if activity_name not in activities:
            return "活動不存在!"
        del activities[activity_name]
        return f"活動 '{activity_name}' 已刪除。"

    return None

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
