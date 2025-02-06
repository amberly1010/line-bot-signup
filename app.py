from flask import Flask, request, jsonify
from linebot.v3.messaging import MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhook import WebhookHandler
import os

app = Flask(__name__)

# 設定 LINE API 金鑰
LINE_CHANNEL_ACCESS_TOKEN = "CeDYTudJGcmApZKWQ5aH6ZDF/bQfelCO8UQSNLM/BiLn9QzGX4P+8Bn0piCtxZose0uqq+xaLp6yGPRe7cGjkOwHpI4D/US3oHCRk4ejqxLyCuTg/PuAKHQLk57j8aqGlzXwbYckznAxhJzeSWNE8QdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "8d141f11e043c01c163ad2ce10cd09f5"

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
    
    try:
        handler.handle(body, signature)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
    return "OK"

@handler.add("message")
def handle_message(event):
    if isinstance(event.message, TextMessage):
        user_message = event.message.text.strip()
        user_id = event.source.user_id
        
        response_text = process_message(user_message, user_id)
        reply_message(event.reply_token, response_text)

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
    message = ReplyMessageRequest(reply_token=reply_token, messages=[TextMessage(text=text)])
    line_bot_api.reply_message(message)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
