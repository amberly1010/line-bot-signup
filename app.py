from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import re

app = Flask(__name__)

# 設定你的 LINE Bot Channel Access Token 和 Channel Secret
LINE_BOT_API = "2006843879"
HANDLER = "8d141f11e043c01c163ad2ce10cd09f5"
line_bot_api = LineBotApi(LINE_BOT_API)
handler = WebhookHandler(HANDLER)

# 活動報名資料存儲
events = {}

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return "Invalid signature", 400
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text.strip()
    reply_token = event.reply_token

    # 新增活動
    if user_message.startswith("新增+"):
        event_name = user_message[3:].strip()
        if event_name in events:
            return
        events[event_name] = []
    
    # 報名活動
    for event_name in events:
        if user_message.startswith(event_name):
            participants = re.findall(r"([^\s()]+(?:\([^()]*\))?)", user_message[len(event_name):].strip())
            events[event_name].extend(participants)
            return
    
    # 取消報名
    if user_message.startswith("取消+"):
        parts = user_message[3:].split("+")
        if len(parts) == 2 and parts[0] in events:
            events[parts[0]] = [p for p in events[parts[0]] if not p.startswith(parts[1])]
            return
    
    # 刪除活動
    if user_message.startswith("刪除+"):
        event_name = user_message[3:].strip()
        if event_name in events:
            del events[event_name]
            return
    
    # 截止報名並輸出名單
    if user_message.startswith("截止+"):
        event_name = user_message[3:].strip()
        if event_name in events:
            response = f"{event_name} 報名名單:\n" + "\n".join([f"{i+1}.{p}" for i, p in enumerate(events[event_name])])
            line_bot_api.reply_message(reply_token, TextSendMessage(text=response))
            return

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
