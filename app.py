from flask import Flask, request, jsonify
from linebot.v3.messaging import MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhook import WebhookHandler, MessageEvent
import os

app = Flask(__name__)

# 設定 LINE API 金鑰
LINE_CHANNEL_ACCESS_TOKEN = "CeDYTudJGcmApZKWQ5aH6ZDF/bQfelCO8UQSNLM/BiLn9QzGX4P+8Bn0piCtxZose0uqq+xaLp6yGPRe7cGjkOwHpI4D/US3oHCRk4ejqxLyCuTg/PuAKHQLk57j8aqGlzXwbYckznAxhJzeSWNE8QdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "8d141f11e043c01c163ad2ce10cd09f5"

# 檢查環境變數是否正確
print(f"LINE_CHANNEL_ACCESS_TOKEN: {LINE_CHANNEL_ACCESS_TOKEN}")
print(f"LINE_CHANNEL_SECRET: {LINE_CHANNEL_SECRET}")

# 建立 API 客戶端
line_bot_api = MessagingApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 活動報名資料結構
activities = {}

@app.route("/", methods=["GET"])
def home():
    return "LINE Bot is running!"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    print("Webhook Received:", body)  # 🔍 確認 Webhook 收到的內容
    print("X-Line-Signature:", signature)  # 🔍 確認是否有收到 Signature

    if signature is None:
        print("🚨 WARNING: X-Line-Signature is missing! This request is likely from a manual test.")  # 記錄警告
        return jsonify({"warning": "X-Line-Signature is missing. Manual test detected."}), 200

    try:
        handler.handle(body, signature)
    except Exception as e:
        print(f"🚨 ERROR HANDLING MESSAGE: {str(e)}")  # 記錄錯誤
        return jsonify({"error": str(e)}), 400

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print("🚀 handle_message() 被觸發!")  # 確保這個函數有被執行
    
    user_message = event.message.text.strip()
    user_id = event.source.user_id
    reply_token = event.reply_token  # 取得 replyToken
    
    print(f"📩 Received Message: {user_message} from User: {user_id}")  # 記錄收到的訊息

    response_text = process_message(user_message, user_id)

    if response_text:
        print(f"🤖 Response: {response_text}")  # 記錄回應內容
        reply_message(reply_token, response_text)
        print("✅ Message Sent Successfully")  # 確認訊息已回傳
    else:
        print("🚨 ERROR: `process_message()` 回傳了空內容，可能發生錯誤")

def process_message(user_message, user_id):
    global activities
    print(f"🔍 `process_message()` 被執行: {user_message}")  # 記錄訊息內容
    
    if user_message.startswith("新增+"):
        activity_name = user_message.replace("新增+", "").strip()
        
        if activity_name in activities:
            print(f"⚠️ 活動 '{activity_name}' 已存在，跳過新增")
            return f"活動 '{activity_name}' 已存在！"
        
        activities[activity_name] = []
        print(f"✅ 活動 '{activity_name}' 已建立！")  # 記錄活動成功新增
        return f"活動 '{activity_name}' 已新增，開始接受報名！"
    
    print("🚨 ERROR: `process_message()` 解析訊息時發生問題")
    return "指令無效，請確認格式！"

def reply_message(reply_token, text):
    print(f"🔄 Sending Reply: {text}")  # 記錄機器人回應
    try:
        message = ReplyMessageRequest(reply_token=reply_token, messages=[TextMessage(text=text)])
        line_bot_api.reply_message(message)
        print("✅ Message Sent to LINE Successfully")  # 確認回應成功發送
    except Exception as e:
        print(f"🚨 ERROR SENDING MESSAGE: {str(e)}")  # 記錄錯誤

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
