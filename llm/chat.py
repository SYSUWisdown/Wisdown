import sqlite3
import os
import requests
import subprocess
import time
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import uvicorn

load_dotenv()

app = FastAPI()

class ChatRequest(BaseModel):
    action: str
    # 你可以根据需要添加更多字段

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    if req.action == "chat":
        # 复用原有 chat 逻辑
        DB_PATH = os.path.join(os.path.dirname(__file__), 'chat.db')
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        rows = cursor.execute("SELECT username, content FROM messages ORDER BY id").fetchall()
        conn.close()
        history = "\n".join([f"{u}: {c}" for u, c in rows])
        plugin_docs = """
当前可用插件名和相应的功能描述：
1. plugin-uml：根据聊天内容和情境，自动生成最有帮助的UML图来帮助聊天人（如流程图、结构图、时序图等）。适合会议、流程、协作、任务梳理等场景。
2. plugin-md：根据聊天内容和情境，自动生成最有帮助的markdown文档（如食谱、会议纪要、建议等），适合需要文档、总结、食谱、会议纪要等场景。
用法示例：
- 聊天内容涉及做饭、食谱等，可调用plugin-md生成食谱文档。
- 聊天内容涉及会议、讨论等，可调用plugin-md生成会议纪要，plugin-uml生成会议相关uml图。
- 聊天内容涉及流程、步骤等，可调用plugin-uml生成流程图。
- 如仅为闲聊、问好等等不需要协助的，则无需调用任何插件。
"""
        instruction = (
            "请根据聊天内容和插件功能资料，判断当前哪些插件可以帮助聊天人。"
            "如果需要调用插件，请严格按照如下格式输出，每个插件一行：\nplugin: <插件名>; reason: <简要理由>"
            "如果不需要任何插件，请严格回复：\nplugin: none"
            "不要输出其他内容。"
        )
        full_prompt = f"聊天历史：\n{history}\n\n插件功能资料：\n{plugin_docs}\n\n{instruction}"
        API_KEY = os.getenv("OPENROUTER_API_KEY")
        API_URL = "https://openrouter.ai/api/v1/chat/completions"
        HEADERS = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "qwen/qwq-32b:free",
            "messages": [
                {"role": "system", "content": "你是一个中文AI助手：你需要根据聊天记录和情境，决策当前哪些插件可以帮助聊天人。"},
                {"role": "user", "content": full_prompt}
            ]
        }
        resp = requests.post(API_URL, headers=HEADERS, json=data)
        if resp.status_code == 200:
            result = resp.json()
            reply = result["choices"][0]["message"]["content"]
            output_dir = os.path.join(os.path.dirname(__file__), 'plugin_outputs')
            os.makedirs(output_dir, exist_ok=True)
            timestamp = int(time.time())
            output_path = None
            for line in reply.strip().split('\n'):
                if line.startswith("plugin: plugin-uml"):
                    # output_path = os.path.join(output_dir, f"uml_{timestamp}.txt")
                    output_path = os.path.join(output_dir, "uml", f"uml_{timestamp}.txt")
                    plugin_path = os.path.join(os.path.dirname(__file__), 'plugin-uml.py')
                    try:
                        subprocess.check_output(['python3', plugin_path, output_path], text=True)
                    except Exception as e:
                        pass
                elif line.startswith("plugin: plugin-md"):
                    # output_path = os.path.join(output_dir, f"md_{timestamp}.md")
                    output_path = os.path.join(output_dir, "md", f"md_{timestamp}.md")
                    plugin_path = os.path.join(os.path.dirname(__file__), 'plugin-md.py')
                    try:
                        subprocess.check_output(['python3', plugin_path, output_path], text=True)
                    except Exception as e:
                        pass
            return JSONResponse({"reply": reply, "output_path": output_path})
        else:
            return JSONResponse({"error": resp.text}, status_code=resp.status_code)
    elif req.action == "list":
        output_dir = os.path.join(os.path.dirname(__file__), '/app/plugin_outputs')
        if not os.path.exists(output_dir):
            return JSONResponse({"files": []})
        files = os.listdir(output_dir)
        return JSONResponse({"files": files})
    else:
        return JSONResponse({"error": "Unknown action"}, status_code=400)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
