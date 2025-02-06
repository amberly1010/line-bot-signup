from flask import Flask, request
from linebot.v3.messaging import MessagingApiClient, ReplyMessageRequest, TextMessage
from linebot.v3.webhook import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
import os

app = Flask(__name__)

# 讀取 LINE CHANNEL 資訊
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

# 初始化 Line Bot
line_bot_api = MessagingApiClient(channel_access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 測試首頁
@app.route("/", methods=["GET"])
def home():
    return "Line Bot 活動報名系統運行中！"

# Webhook 接收 LINE 訊息
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return "Invalid Signature", 400

    return "OK", 200

# 處理文字訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    reply_text = f"你說的是: {user_message}"

    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=reply_text)]
        )
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False)
