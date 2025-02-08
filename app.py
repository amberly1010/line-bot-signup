from flask import Flask, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import re
import os

app = Flask(__name__)

# LINE 機器人設定
LINE_CHANNEL_SECRET = "8d141f11e043c01c163ad2ce10cd09f5"
LINE_CHANNEL_ACCESS_TOKEN = "CeDYTudJGcmApZKWQ5aH6ZDF/bQfelCO8UQSNLM/BiLn9QzGX4P+8Bn0piCtxZose0uqq+xaLp6yGPRe7cGjkOwHpI4D/US3oHCRk4ejqxLyCuTg/PuAKHQLk57j8aqGlzXwbYckznAxhJzeSWNE8QdB04t89/1O/w1cDnyilFU="

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 活動儲存結構
activities = {}
GROUP_A_ID = "Cf1bd502f60c18931d43b68d91fe8abb5"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return "Invalid signature", 400
    
    return "OK", 200

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text.strip()
    reply_text = ""
    
    # 新增活動
    match = re.match(r"^新增 (.+?) (\d+人)? ?(AJ|BJ)?$", user_message)
    if match:
        activity_name, max_participants, group_tag = match.groups()
        activity_name = activity_name.strip()
        max_participants = int(max_participants[:-1]) if max_participants else None
        
        if activity_name in activities:
            reply_text = f"活動 '{activity_name}' 已存在"
        else:
            activities[activity_name] = {"max": max_participants, "participants": [], "group": group_tag}
            reply_text = f"活動 '{activity_name}' 已新增，{'最多 ' + str(max_participants) + ' 人' if max_participants else '無人數限制'}"
    
    # 更新活動人數
    match = re.match(r"^更新 (.+?) (\d+人)$", user_message)
    if match:
        activity_name, new_max = match.groups()
        activity_name = activity_name.strip()
        if activity_name in activities:
            activities[activity_name]["max"] = int(new_max[:-1])
            reply_text = f"活動 '{activity_name}' 已更新，最多 {new_max}"
        else:
            reply_text = "找不到該活動"
    
    # 報名活動
    match = re.match(r"^報名 (.+?)\n(.+)$", user_message, re.DOTALL)
    if match:
        activity_name, participants = match.groups()
        activity_name = activity_name.strip()
        if activity_name not in activities:
            reply_text = f"找不到活動 '{activity_name}'"
        else:
            participants_list = [p.strip() for p in participants.split("\n") if p.strip()]
            added_count = 0
            for participant in participants_list:
                if participant not in activities[activity_name]["participants"]:
                    if activities[activity_name]["max"] and len(activities[activity_name]["participants"]) >= activities[activity_name]["max"]:
                        break
                    activities[activity_name]["participants"].append(participant)
                    added_count += 1
            
            if added_count > 0:
                reply_text = f"報名成功！活動 '{activity_name}' 目前參加名單：\n"
                for i, p in enumerate(activities[activity_name]["participants"], 1):
                    reply_text += f"{i}. {p}\n"
            
            if activities[activity_name]["max"] and len(activities[activity_name]["participants"]) >= activities[activity_name]["max"]:
                reply_text += f"\n報名已達到最大人數，活動 '{activity_name}' 現在已額滿。"
    
    # 查詢名單
    match = re.match(r"^名單 (.+)$", user_message)
    if match:
        activity_name = match.group(1).strip()
        if activity_name in activities:
            reply_text = f"活動 '{activity_name}' 報名名單：\n"
            for i, p in enumerate(activities[activity_name]["participants"], 1):
                reply_text += f"{i}. {p}\n"
        else:
            reply_text = "找不到該活動"
    
    # 截止活動
    match = re.match(r"^截止 (.+)$", user_message)
    if match:
        activity_name = match.group(1).strip()
        if activity_name in activities:
            reply_text = f"活動 '{activity_name}' 已結束。最終名單如下：\n"
            for i, p in enumerate(activities[activity_name]["participants"], 1):
                reply_text += f"{i}. {p}\n"
            del activities[activity_name]
        else:
            reply_text = "找不到該活動"
    
    if reply_text:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)