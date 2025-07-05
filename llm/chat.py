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
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

# 加载环境变量
load_dotenv()

app = FastAPI()

class ChatRequest(BaseModel):
    action: str
    # 你可以根据需要添加更多字段

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    # 每次调用都先执行 vectorizer
    vectorizer_path = os.path.join(os.path.dirname(__file__), 'plugin-vectorizer.py')
    try:
        subprocess.check_output(['python3', vectorizer_path], text=True)
    except Exception as e:
        pass
    if req.action == "chat":
        # 读取聊天历史
        DB_PATH = os.path.join(os.path.dirname(__file__), 'chat.db')
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        rows = cursor.execute("SELECT username, content FROM messages ORDER BY id").fetchall()
        conn.close()
        history = "\n".join([f"{u}: {c}" for u, c in rows])
        plugin_docs = """
            当前可用插件名和相应的功能描述：
            1. plugin-uml：根据聊天内容，自动生成最有帮助的UML图来帮助聊天人（如流程图、结构图、时序图等）。适合会议、流程、协作、任务梳理等场景。
            2. plugin-md：根据聊天内容和情境，自动生成最有帮助的markdown文档（如食谱、会议纪要、建议等），适合需要文档、总结、食谱、会议纪要等场景。
            3. plugin-reasoner：当聊天内容涉及需要推理、分析、证明、复杂计算等问题时，自动识别并梳理出当前需要推理的问题，并用思维链（Chain-of-Thought）方式给出详细推理过程和最终答案。
            4. plugin-infoagent：实时信息助手，能够根据当前聊天内容和情境，判断并获取实时的、外部的、网络的信息。
            用法示例：
            - 聊天内容显示，当前聊天人可能需要文档的总结和帮助时，调用plugin-md：
                比方说涉及做饭、食谱等，可调用plugin-md生成食谱文档。
                比方说会议、讨论等，可调用plugin-md生成会议纪要，plugin-uml生成会议相关uml图。
            - 聊天内容涉及流程、步骤等，可调用plugin-uml生成流程图。
            - 聊天内容涉及数学题、证明题、推理分析等，则优先调用plugin-reasoner生成推理过程和答案，而非总结文档或者uml图。
            - 聊天内容如果显示，当前需要获取实时信息、网络信息、无法单纯总结只能联网搜索的信息等，则调用plugin-infoagent获取相关信息。而此时其他待选插件一律不选择。
                比方说当前聊天人需要获取天气、新闻、体育赛事等信息，则调用plugin-infoagent获取相关信息。
            - 如仅为闲聊、问好等等不需要协助的，则无需调用任何插件。
        """
        instruction = (
            "请根据聊天内容和插件功能资料，判断当前的聊天中，哪些插件可以帮助聊天人。"
            "注意不需要聊天中直接提及对插件的需要你才选择这个插件，而是你要思考当前聊天情境下，哪些插件可以用来帮助聊天人更好地解决问题或者是聊天人所可能用得上的。"
            "如果需要调用插件，请严格按照如下格式输出，每个插件一行：\nplugin: <插件名>; reason: <简要理由>"
            "如果不需要任何插件(当你判断当前聊天情境下，聊天人不需要上面提到的插件的帮助时)，请严格回复：\nplugin: none"
            "不要输出其他内容。"
        )
        full_prompt = f"聊天历史：\n{history}\n\n插件功能资料：\n{plugin_docs}\n\n{instruction}"
        human_msg = HumanMessage(content=full_prompt)
        system_msg = SystemMessage(content="你是一个智能插件调度助手：你将接收到全部聊天历史和插件功能资料。根据所有聊天内容，来判断当前的聊天情境和话题。再据此，来判断当前调用什么插件(可以是0个到多个)，可能可以帮助当前的聊天人。")
        
        llm = ChatOpenAI(
            temperature=0,
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1",
            model="qwen/qwq-32b:free"
        )
        response = llm([system_msg, human_msg])
        reply = response.content
        output_dir = os.path.join(os.path.dirname(__file__), 'plugin_outputs')
        os.makedirs(output_dir, exist_ok=True)
        timestamp = int(time.time())
        output_path = None
        print(f"000000")
        for line in reply.strip().split('\n'):      # 目前都是在chat.py中指定文件夹，插件只负责输出到文件夹
            if line.startswith("plugin: plugin-uml"):
                print(f"444444")
                output_path = os.path.join(output_dir, "uml", f"uml_{timestamp}.png")
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                plugin_path = os.path.join(os.path.dirname(__file__), 'plugin-uml.py')
                try:
                    subprocess.check_output(['python3', plugin_path, output_path], text=True)
                except Exception as e:
                    pass
            elif line.startswith("plugin: plugin-md"):
                print(f"333333")
                output_path = os.path.join(output_dir, "md", f"md_{timestamp}.md")
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                plugin_path = os.path.join(os.path.dirname(__file__), 'plugin-md.py')
                try:
                    subprocess.check_output(['python3', plugin_path, output_path], text=True)
                except Exception as e:
                    pass
            elif line.startswith("plugin: plugin-reasoner"):
                output_path = os.path.join(output_dir, "reasoner", f"reasoner_{timestamp}.md")
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                plugin_path = os.path.join(os.path.dirname(__file__), 'plugin-reasoner.py')
                try:
                    subprocess.check_output(['python3', plugin_path, output_path], text=True)
                except Exception as e:
                    pass
            elif line.startswith("plugin: plugin-infoagent"):
                output_path = os.path.join(output_dir, "infoagent", f"infoagent_{timestamp}.md")
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                plugin_path = os.path.join(os.path.dirname(__file__), 'plugin-infoagent.py')
                try:
                    subprocess.check_output(['python3', plugin_path, output_path], text=True)
                except Exception as e:
                    pass
        return JSONResponse({"reply": reply, "output_path": output_path})
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
