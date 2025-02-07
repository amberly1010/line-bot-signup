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

# 設置 callback 路由來處理來自 LINE 的 webhook 請求
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    
    print(f"簽名: {signature}")  # 印出簽名
    print(f"請求體: {body}")  # 印出請求的內容

    # 驗證 webhook 請求的簽名
    try:
        handler.handle(body, signature)
    except Exception as e:
        print(f"處理錯誤: {str(e)}")  # 輸出錯誤信息
        abort(400)
    
    return 'OK'

# 處理來自 LINE 的訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message = event.message.text
    # 獲取群組 ID
    if event.source.type == 'group':
        group_id = event.source.group_id
    else:
        group_id = None

    # 群組1 ID
    GROUP_A_ID = 'Cf1bd502f60c18931d43b68d91fe8abb5'  # 群組1的 group_id (群組A)
    # 群組2 ID (需替換成真實的群組2 ID)
    GROUP_B_ID = '其他群組B的group_id'  # 替換為群組2的 group_id (群組B)
    
    if message.startswith('新增'):
        parts = message.split()

        # 檢查訊息格式
        if len(parts) < 3:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="指令格式錯誤，請使用：新增 活動名稱 人數 AJ/BJ"))
            return

        activity_name = parts[1].strip()  # 去掉空格，避免名稱錯誤
        participants_limit = parts[2]  # 例如 10人
        group_limit = parts[3].upper() if len(parts) > 3 else None  # AJ, BJ 或 None（無限制）

        # 檢查活動名稱是否已存在
        if activity_name in events:
            # 如果活動已存在，更新人數限制
            try:
                max_participants = int(re.search(r'\d+', participants_limit).group())
                events[activity_name]['max_participants'] = max_participants
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"活動「{activity_name}」已存在，已更新人數限制：{max_participants}人。"))
            except:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="人數格式錯誤，請重新輸入有效人數。"))
                return
        else:
            # 如果活動不存在，創建新活動
            try:
                max_participants = int(re.search(r'\d+', participants_limit).group())
                events[activity_name] = {'allowed_group': group_limit, 'max_participants': max_participants, 'participants': []}
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"活動「{activity_name}」已新增，限制人數：{max_participants}人。"))
            except:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="人數格式錯誤，請重新輸入有效人數。"))
                return
    
    elif message.startswith('更新'):
        parts = message.split()

        if len(parts) < 3:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="指令格式錯誤，請使用：更新 活動名稱 新人數"))
            return

        activity_name = parts[1].strip()  # 去掉空格，避免名稱錯誤
        new_participants_limit = parts[2]  # 新的人數限制

        if activity_name in events:
            try:
                new_max_participants = int(re.search(r'\d+', new_participants_limit).group())
                events[activity_name]['max_participants'] = new_max_participants

                # 確保名單不會丟失，並且會繼續從之前的報名者開始處理
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"活動「{activity_name}」已更新人數限制為：{new_max_participants}人。"))
            except:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="人數格式錯誤，請重新輸入有效人數。"))
                return
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="找不到該活動。"))

    elif message.startswith('報名'):
        activity_name = message[2:].split()[0].strip()  # 去掉空格，避免名稱錯誤
        if activity_name in events:
            allowed_group = events[activity_name].get('allowed_group')
            
            if allowed_group and group_id != allowed_group:
                return

            participants = parse_registration(message[len(activity_name)+3:].strip())
            group = events[activity_name]['participants']

            # 檢查重複報名
            for participant in participants:
                if participant[0] in [p[0] for p in group]:
                    existing_number = [p[0] for p in group].index(participant[0]) + 1
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"已重複報名 編號{existing_number} {participant[0]}"))
                    return

            # 只擷取到最大人數，若超過則停止報名並提供名單
            for i, participant in enumerate(participants):
                if len(group) >= events[activity_name]['max_participants']:
                    break
                group.append(participant)
            
            if len(group) >= events[activity_name]['max_participants']:
                participants_list = [f"{i+1}. {p[0]} ({p[1]})" if p[1] else f"{i+1}. {p[0]}" for i, p in enumerate(group)]
                participants_list_str = "\n".join(participants_list)
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"報名已達到最大人數。截止名單如下：\n{participants_list_str}"))
            
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="找不到該活動。"))

    elif message.startswith('截止'):
        activity_name = message[2:].strip()
        if activity_name in events:
            participants_list = []
            for i, (name, item) in enumerate(events[activity_name]['participants'], start=1):
                participants_list.append(f"{i}. {name} ({item})" if item else f"{i}. {name}")
            participants_list_str = "\n".join(participants_list)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"活動「{activity_name}」的報名名單如下：\n{participants_list_str}\n活動已結束。"))
            del events[activity_name]  # 活動截止後刪除活動
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="找不到該活動。"))

# 測試路徑：根路徑
@app.route('/')
def home():
    return "LINE Bot is running!"

if __name__ == "__main__":
    app.run(debug=True)
