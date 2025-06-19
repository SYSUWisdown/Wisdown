import sqlite3
import os
import requests
import sys
import time
import subprocess
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.path.join(os.path.dirname(__file__), 'chat.db')
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
rows = cursor.execute("SELECT username, content FROM messages ORDER BY id").fetchall()
conn.close()

history = "\n".join([f"{u}: {c}" for u, c in rows])

# 新prompt：根据聊天内容和情境，自动判断是否有必要生成uml图，有则输出最有帮助的PlantUML代码块，无则输出空uml代码块
uml_prompt = (
    "请根据以下聊天内容和情境，判断当前是否有必要生成某个UML图来帮助聊天人。"
    "如果有，请只输出最有帮助的PlantUML代码，且只输出代码块，不要有多余解释。"
    "如果没有相关需求，则只输出空的PlantUML代码块（@startuml\n@enduml）。"
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
        {"role": "system", "content": "你是一个UML图生成助手。根据聊天内容和情境，判断是否有必要生成uml图，只输出PlantUML格式的代码块。"},
        {"role": "user", "content": uml_prompt}
    ]
}

resp = requests.post(API_URL, headers=HEADERS, json=data)
if resp.status_code == 200:
    result = resp.json()
    uml_text = result["choices"][0]["message"]["content"]
    # 只保留代码块内容
    if '```' in uml_text:
        uml_text = uml_text.split('```')[1].replace('plantuml', '').strip()
    # 输出到指定文件（不再创建文件夹，由chat.py负责）
    if len(sys.argv) > 1:
        output_path = sys.argv[1]
        with open(output_path, 'w') as f:
            f.write(uml_text)
        # 自动调用PlantUML渲染图片
        try:
            subprocess.run(["plantuml", output_path], check=True)
        except Exception as e:
            print("PlantUML 渲染失败：", e)
else:
    print("Error：", resp.status_code, resp.text)