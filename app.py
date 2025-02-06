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

    # 🔹 檢查 signature 是否為 None，允許測試
    if signature is None:
        print("🚨 WARNING: X-Line-Signature is missing! This request is likely from a manual test.")  # 記錄警告
        return jsonify({"warning": "X-Line-Signature is missing. Manual test detected."}), 200

    try:
        handler.handle(body, signature)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    return "OK"

@handler.add(MessageEvent)
def handle_message(event):
    if isinstance(event.message, TextMessage):
        user_message = event.message.text.strip()
        user_id = event.source.user_id
        
        print(f"📩 Received Message: {user_message} from User: {user_id}")  # 🔍 記錄訊息
        
        response_text = process_message(user_message, user_id)
        print(f"🤖 Response: {response_text}")  # 🔍 記錄回應內容
        
        reply_message(event.reply_token, response_text)
        print("✅ Message Sent Successfully")  # 🔍 記錄成功發送

def process_message(user_message, user_id):
    global activities
    
    if user_message.startswith("新增+"):
        activity_name = user_message.replace("新增+", "").strip()
        activities[activity_name] = []
        return f"活動 '{activity_name}' 已新增，開始接受報名！"
    
    elif user_message.startswith("截止+"):
        activity_name = user_message.replace("截止+", "").strip()
        if activity_name in activities:
            participant_list = "\n".join([f"{idx+1}. {p}" for idx, p in enumerate(activities[activity_name])])
            return f"活動 '{activity_name}' 報名名單：\n{participant_list}"
        return f"活動 '{activity_name}' 不存在或尚未有人報名。"
    
    elif user_message.startswith("取消+"):
        parts = user_message.split("+")
        if len(parts) == 3:
            activity_name, name_to_remove = parts[1], parts[2]
            if activity_name in activities and name_to_remove in activities[activity_name]:
                activities[activity_name].remove(name_to_remove)
                return f"{name_to_remove} 已從 '{activity_name}' 報名名單移除。"
            return f"未找到 '{name_to_remove}' 在 '{activity_name}' 的報名紀錄。"
    
    elif user_message.startswith("刪除+"):
        activity_name = user_message.replace("刪除+", "").strip()
        if activity_name in activities:
            del activities[activity_name]
            return f"活動 '{activity_name}' 已刪除。"
        return f"活動 '{activity_name}' 不存在。"
    
    else:
        for activity_name in activities.keys():
            if user_message.startswith(activity_name):
                participants = user_message[len(activity_name):].strip().split()
                activities[activity_name].extend(participants)
                return f"成功報名 '{activity_name}': {', '.join(participants)}"
    
    return "指令無效，請確認格式！"

def reply_message(reply_token, text):
    print(f"🔄 Sending Reply: {text}")  # 🔍 記錄機器人的回應
    try:
        message = ReplyMessageRequest(reply_token=reply_token, messages=[TextMessage(text=text)])
        line_bot_api.reply_message(message)
        print("✅ Message Sent to LINE Successfully")  # 🔍 確認回應已發送
    except Exception as e:
        print(f"🚨 ERROR SENDING MESSAGE: {str(e)}")  # 🔍 記錄錯誤

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
