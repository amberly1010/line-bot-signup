import os
import re
from flask import Flask, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# LINE Bot API 設定
LINE_CHANNEL_SECRET = '8d141f11e043c01c163ad2ce10cd09f5'  # 更新為你的 Channel Secret
LINE_CHANNEL_ACCESS_TOKEN = 'CeDYTudJGcmApZKWQ5aH6ZDF/bQfelCO8UQSNLM/BiLn9QzGX4P+8Bn0piCtxZose0uqq+xaLp6yGPRe7cGjkOwHpI4D/US3oHCRk4ejqxLyCuTg/PuAKHQLk57j8aqGlzXwbYckznAxhJzeSWNE8QdB04t89/1O/w1cDnyilFU='  # 更新為你的 Channel Access Token

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 群組1的 group_id，將其替換為實際群組ID
GROUP_1_ID = 'your_group_1_id_here'  # 這是群組1的群組 ID

# 儲存報名活動的字典，包含不同群組的報名資料
events = {}

# 解析報名訊息
def parse_registration(text):
    participants = []
    for line in text.splitlines():
        match = re.match(r"([^\(]+)(?:\((.*?)\))?", line.strip())
        if match:
            name = match.group(1).strip()
            item = match.group(2).strip() if match.group(2) else ''
            participants.append((name, item))
    return participants

# 處理接收到的訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message = event.message.text
    group_id = event.source.group_id if event.source.type == 'group' else None

    # 只允許群組1新增活動
    if group_id != GROUP_1_ID:
        if message.startswith('新增'):
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="只有群組1可以新增活動！"))
            return

    # 檢查報名活動的指令
    if message.startswith('新增'):
        # 處理新增活動指令
        activity_name = message[2:].strip()
        if '人' in activity_name:
            # 提取人數限制
            match = re.search(r'(\d+)人', activity_name)
            if match:
                max_participants = int(match.group(1))
                activity_name = activity_name.replace(match.group(0), '').strip()
                if activity_name not in events:
                    events[activity_name] = {}
                events[activity_name][group_id] = {
                    'max_participants': max_participants,
                    'participants': []
                }
        else:
            if activity_name not in events:
                events[activity_name] = {}
            events[activity_name][group_id] = {'max_participants': None, 'participants': []}
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"活動「{activity_name}」已新增。"))
    
    elif message.startswith('截止'):
        # 處理活動截止指令
        activity_name = message[2:].strip()
        if activity_name in events:
            participants_list = []
            for group in events[activity_name].values():
                participants_list.extend([f"{i+1}. {p[0]} ({p[1]})" if p[1] else f"{i+1}. {p[0]}" for i, p in enumerate(group['participants'])])
            participants_list_str = "\n".join(participants_list)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"活動「{activity_name}」的報名名單如下：\n{participants_list_str}"))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="找不到該活動。"))

    elif message.startswith('取消'):
        # 處理取消報名指令
        parts = message.split()
        if len(parts) == 3:
            activity_name = parts[1]
            participant_name = parts[2]
            if activity_name in events:
                for group in events[activity_name].values():
                    participants = group['participants']
                    for i, (name, item) in enumerate(participants):
                        if name == participant_name:
                            participants.pop(i)
                            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"參加者 {participant_name} 已成功取消報名「{activity_name}」。"))
                            return
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"找不到參加者 {participant_name} 在活動 {activity_name} 中。"))
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="找不到該活動。"))
    
    else:
        # 檢查報名訊息
        if message.startswith('報名'):
            activity_name = message[2:].split()[0]
            if activity_name in events:
                participants = parse_registration(message[len(activity_name)+3:].strip())
                group = events[activity_name].get(group_id)
                if group:
                    for participant in participants:
                        group['participants'].append(participant)
                        if group['max_participants'] and len(group['participants']) > group['max_participants']:
                            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"報名已滿，請聯繫負責人。"))
                            return
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"參加者 {', '.join([p[0] for p in participants])} 已成功報名「{activity_name}」。"))
                else:
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="此群組尚未報名此活動。"))
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="找不到該活動。"))

if __name__ == "__main__":
    app.run(debug=True)
