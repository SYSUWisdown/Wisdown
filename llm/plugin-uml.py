import sqlite3
import os
import requests
import sys
import time
import subprocess
import re
from dotenv import load_dotenv
# 向量库相关
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import Document
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

load_dotenv()

DB_PATH = os.path.join(os.path.dirname(__file__), 'chat.db')
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
rows = cursor.execute("SELECT username, content FROM messages ORDER BY id").fetchall()
conn.close()

# 取所有聊天内容
history = "\n".join([f"{u}: {c}" for u, c in rows])
# 取最近N轮聊天内容
N = 6
recent_msgs = rows[-N:]
recent_chat = "\n".join([f"{u}: {c}" for u, c in recent_msgs])

# 提取最近N轮中提及的网址
url_pattern = re.compile(r'(https?://[\w\-./?%&=:#]+)')
urls_in_recent = set(url_pattern.findall(recent_chat))

# 检索向量库，辅助内容
VECTOR_DB_PATH = os.path.join(os.path.dirname(__file__), "vector_db")
web_content = ""
if os.path.exists(VECTOR_DB_PATH):
    vectordb = FAISS.load_local(VECTOR_DB_PATH, OpenAIEmbeddings())
    related_docs = []
    if urls_in_recent:
        for url in urls_in_recent:
            # 只取metadata["url"]为该url的内容
            docs = [doc for doc in vectordb.docstore._dict.values() if doc.metadata and doc.metadata.get("url") == url]
            related_docs.extend(docs)
    else:
        # 用当前聊天内容做向量检索
        related_docs = vectordb.similarity_search(recent_chat, k=2)
    # 控制网页内容长度
    web_content = "\n\n".join([doc.page_content[:500] for doc in related_docs[:2]])

# 主次分明的prompt内容
system_msg = SystemMessage(
    content="你是一个UML图生成助手。请根据所有聊天内容，来判断当前或者说最新的聊天情境和话题。再通过当前聊天，来判断当前需要生成什么样的uml图最能帮助当前的聊天人。同时下面还给出了可能被当前聊天提及的网页内容或者和当前聊天相关的数据库内容，作为辅助参考，但要以当前聊天话题为准。"
)
human_msg = HumanMessage(
    content=(
        "请根据所有聊天内容，来判断当前或者说最新的聊天情境和话题。再通过当前聊天，来判断当前需要生成什么样的uml图最能帮助当前的聊天人。"
        "同时下面还给出了可能被当前聊天提及的网页内容或者和当前聊天相关的数据库内容，作为辅助参考，但要以当前聊天话题为准。\n\n"
        f"【所有聊天内容】\n{history}\n\n"
        f"【辅助参考内容。可能含相关网页内容（可选）】\n{web_content}\n\n"
        "请只输出最有帮助的PlantUML代码块（@startuml\n@enduml）。"
    )
)

llm = ChatOpenAI(
    temperature=0,
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    openai_api_base="https://openrouter.ai/api/v1",
    model="qwen/qwq-32b:free"
)

response = llm([system_msg, human_msg])
uml_text = response.content

# 只保留代码块内容
if '```' in uml_text:
    uml_text = uml_text.split('```')[1].replace('plantuml', '').strip()

# 输出到指定文件（不再创建文件夹，由chat.py负责）
if len(sys.argv) > 1:
    output_path = sys.argv[1]
    temp_uml_path = output_path + '.temp.puml'
    with open(temp_uml_path, 'w') as f:
        f.write(uml_text)
    try:
        subprocess.run(["plantuml", "-tpng", temp_uml_path], check=True)
        png_path = temp_uml_path.replace('.puml', '.png')
        os.replace(png_path, output_path)
    except Exception as e:
        print("PlantUML 渲染失败：", e)
    finally:
        if os.path.exists(temp_uml_path):
            os.remove(temp_uml_path)