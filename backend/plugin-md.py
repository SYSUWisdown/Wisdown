import sqlite3
import os
import requests
import sys
import time
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.path.join(os.path.dirname(__file__), 'chat.db')
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
rows = cursor.execute("SELECT username, content FROM messages ORDER BY id").fetchall()
conn.close()

history = "\n".join([f"{u}: {c}" for u, c in rows])

# 优化prompt，要求大模型根据聊天内容和情境，自动判断并生成最有帮助的markdown文档（如食谱、会议纪要、建议等），只输出markdown内容，无多余解释
md_prompt = (
    "请根据以下聊天内容和情境，判断当前最适合生成什么markdown文档来帮助聊天人。"
    "如果聊天内容涉及做饭、食谱等，请生成详细的食谱markdown文档；"
    "如果涉及会议、讨论等，请生成会议纪要markdown文档；"
    "如有其他合适的文档类型，也可自动生成。"
    "请只输出完整的markdown内容，不要有任何解释或多余内容。"
    f"\n聊天内容：\n{history}"
)

API_KEY = os.getenv("OPENROUTER_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

data = {
    "model": "qwen/qwq-32b:free",
    "messages": [
        {"role": "system", "content": "你是一个markdown文档生成助手。你被调用时，需根据聊天内容和情境，生成最能帮助聊天人的markdown文档。只输出完整的markdown文档内容。"},
        {"role": "user", "content": md_prompt}
    ]
}

resp = requests.post(API_URL, headers=HEADERS, json=data)
if resp.status_code == 200:
    result = resp.json()
    md_text = result["choices"][0]["message"]["content"]
    # 只写入传入路径，不再创建文件夹
    if len(sys.argv) > 1:
        output_path = sys.argv[1]
        with open(output_path, 'w') as f:
            f.write(md_text)
else:
    print("Error：", resp.status_code, resp.text)