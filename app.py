from flask import Flask, request, jsonify
from linebot.v3.messaging import MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhook import WebhookHandler, MessageEvent, TextMessageContent
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

    print("Webhook Received:", body)
    print("X-Line-Signature:", signature)

    if signature is None:
        print("🚨 WARNING: X-Line-Signature is missing! This request is likely from a manual test.")
        return jsonify({"warning": "X-Line-Signature is missing. Manual test detected."}), 200

    try:
        handler.handle(body, signature)
    except Exception as e:
        print(f"🚨 ERROR HANDLING MESSAGE: {str(e)}")
        return jsonify({"error": str(e)}), 400

    return "OK"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    print("🚀 handle_message() 被觸發!")
    
    user_message = event.message.text.strip()
    user_id = event.source.user_id
    
    print(f"📩 Received Message: {user_message} from User: {user_id}")
    
    response_text = process_message(user_message, user_id)
    
    if response_text:
        print(f"🤖 Response: {response_text}")
        reply_message(event.reply_token, response_text)
        print("✅ Message Sent Successfully")
    else:
        print("🚨 ERROR: `process_message()` 回傳了空內容，可能發生錯誤")

def process_message(user_message, user_id):
    global activities

    print(f"🔍 `process_message()` 被執行: {user_message}")
    
    if user_message.startswith("新增+"):
        parts = user_message.replace("新增+", "").strip().split()
        activity_name = parts[0]
        max_participants = parts[1] if len(parts) > 1 and parts[1].endswith("人") else "無上限"
        
        if activity_name in activities:
            print(f"⚠️ 活動 '{activity_name}' 已存在，跳過新增")
            return f"活動 '{activity_name}' 已存在！"
        
        activities[activity_name] = {"participants": [], "max": max_participants}
        print(f"✅ 活動 '{activity_name}' 已建立！ 限制人數: {max_participants}")
        return f"活動 '{activity_name}' 已新增，限制人數: {max_participants}，開始接受報名！"
    
    if user_message.startswith("增加人數+"):
        parts = user_message.replace("增加人數+", "").strip().split()
        
        if len(parts) < 2 or not parts[1].endswith("人") or not parts[1][:-1].isdigit():
            return "❌ 格式錯誤！請使用 `增加人數+活動名稱 人數` 格式，例如 `增加人數+星期四濟世 5人`。"
        
        activity_name = parts[0]
        additional_slots = int(parts[1][:-1])

        if activity_name not in activities:
            return f"⚠️ 活動 '{activity_name}' 不存在，請先使用 `新增+活動名稱` 指令建立！"

        if activities[activity_name]["max"] == "無上限":
            return f"🔹 活動 '{activity_name}' 本來就是無上限，不需增加名額。"

        old_max = int(activities[activity_name]["max"])
        new_max = old_max + additional_slots
        activities[activity_name]["max"] = str(new_max)

        print(f"✅ 活動 '{activity_name}' 人數上限已增加 {additional_slots} 人，總上限變為 {new_max} 人")
        return f"✅ 活動 '{activity_name}' 名額已增加 {additional_slots} 人，現在上限為 {new_max} 人！"
    
    print("🚨 ERROR: `process_message()` 解析訊息時發生問題")
    return "指令無效，請確認格式！"

def reply_message(reply_token, text):
    print(f"🔄 Sending Reply: {text}")
    try:
        message = ReplyMessageRequest(reply_token=reply_token, messages=[TextMessage(text=text)])
        line_bot_api.reply_message(message)
        print("✅ Message Sent to LINE Successfully")
    except Exception as e:
        print(f"🚨 ERROR SENDING MESSAGE: {str(e)}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
