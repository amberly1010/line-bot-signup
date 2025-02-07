from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import re

app = Flask(__name__)

# LINE Bot API 設定
LINE_CHANNEL_SECRET = '8d141f11e043c01c163ad2ce10cd09f5'  # 更新為你的 Channel Secret
LINE_CHANNEL_ACCESS_TOKEN = 'CeDYTudJGcmApZKWQ5aH6ZDF/bQfelCO8UQSNLM/BiLn9QzGX4P+8Bn0piCtxZose0uqq+xaLp6yGPRe7cGjkOwHpI4D/US3oHCRk4ejqxLyCuTg/PuAKHQLk57j8aqGlzXwbYckznAxhJzeSWNE8QdB04t89/1O/w1cDnyilFU='  # 更新為你的 Channel Access Token

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

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

# 設置 callback 路由來處理來自 LINE 的 Webhook 請求
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    
    # 驗證 webhook 請求的簽名
    try:
        handler.handle(body, signature)
    except Exception as e:
        abort(400)
    
    return 'OK'

# 處理來自 LINE 的訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message = event.message.text
    # 獲取群組 ID
    if event.source.type == 'group':
        group_id = event.source.group_id
        print(f"來自群組的訊息，群組 ID 是: {group_id}")  # 印出 group_id
    else:
        group_id = None

    # 群組1 ID
    GROUP_A_ID = 'Cf1bd502f60c18931d43b68d91fe8abb5'  # 群組1的 group_id (群組A)
    # 群組2 ID (需替換成真實的群組2 ID)
    GROUP_B_ID = '其他群組B的group_id'  # 替換為群組2的 group_id (群組B)
    
    if message.startswith('新增'):
        parts = message.split()
        activity_name = parts[1]
        participants_limit = parts[2]  # 例如 10人
        group_limit = parts[3].upper() if len(parts) > 3 else None  # AJ, BJ 或 None（無限制）

        # 提取最大人數
        max_participants = int(re.search(r'\d+', participants_limit).group())
        
        if group_limit == 'AJ':
            events[activity_name] = {'allowed_group': GROUP_A_ID, 'max_participants': max_participants, 'participants': {}}
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"活動「{activity_name}」已新增，僅允許群組A參加。"))
        elif group_limit == 'BJ':
            events[activity_name] = {'allowed_group': GROUP_B_ID, 'max_participants': max_participants, 'participants': {}}
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"活動「{activity_name}」已新增，僅允許群組B參加。"))
        else:
            events[activity_name] = {'allowed_group': None, 'max_participants': max_participants, 'participants': {}}
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"活動「{activity_name}」已新增，無群組限制。"))
    
    elif message.startswith('報名'):
        activity_name = message[2:].split()[0]
        if activity_name in events:
            allowed_group = events[activity_name].get('allowed_group')
            
            if allowed_group and group_id != allowed_group:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"活動「{activity_name}」僅允許指定群組參加！"))
                return

            participants = parse_registration(message[len(activity_name)+3:].strip())
            group = events[activity_name]['participants']
            for participant in participants:
                group[participant[0]] = participant[1] if len(participant) > 1 else None
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"參加者 {', '.join([p[0] for p in participants])} 已成功報名「{activity_name}」。"))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="找不到該活動。"))

    elif message.startswith('截止'):
        activity_name = message[2:].strip()
        if activity_name in events:
            participants_list = []
            for group in events[activity_name].values():
                participants_list.extend([f"{i+1}. {p[0]} ({p[1]})" if p[1] else f"{i+1}. {p[0]}" for i, p in enumerate(group['participants'])])
            participants_list_str = "\n".join(participants_list)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"活動「{activity_name}」的報名名單如下：\n{participants_list_str}"))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="找不到該活動。"))

# 測試路由：根路徑
@app.route('/')
def home():
    return "LINE Bot is running!"

if __name__ == "__main__":
    app.run(debug=True)
