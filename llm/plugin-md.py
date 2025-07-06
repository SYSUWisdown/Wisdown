import sqlite3
import os
import sys
import re
import requests
from dotenv import load_dotenv

load_dotenv()

# 取所有聊天内容
# history = "\n".join([f"{u}: {c}" for u, c in rows])
# 取最近N轮聊天内容
# N = 6
# recent_msgs = rows[-N:]
# recent_chat = "\n".join([f"{u}: {c}" for u, c in recent_msgs])

# 提取最近N轮中提及的网址
# url_pattern = re.compile(r'(https?://[\w\-./?%&=:#]+)')
# urls_in_recent = set(url_pattern.findall(recent_chat))

# 检索向量库，辅助内容
# VECTOR_DB_PATH = os.path.join(os.path.dirname(__file__), "vector_db")
web_content = ""
# if os.path.exists(VECTOR_DB_PATH):
#     try:
#         from langchain.embeddings import OpenAIEmbeddings
#         from langchain.vectorstores import FAISS
#         vectordb = FAISS.load_local(VECTOR_DB_PATH, OpenAIEmbeddings())
#         related_docs = []
#         if urls_in_recent:
#             for url in urls_in_recent:
#                 docs = [doc for doc in vectordb.docstore._dict.values() if doc.metadata and doc.metadata.get("url") == url]
#                 related_docs.extend(docs)
#         else:
#             related_docs = vectordb.similarity_search(recent_chat, k=2)
#         web_content = "\n\n".join([doc.page_content[:500] for doc in related_docs[:2]])
#     except Exception:
#         web_content = ""

# 主次分明的prompt内容

print("[1] 脚本开始执行")

DB_PATH = os.path.join(os.path.dirname(__file__), 'chat.db')
print(f"[2] 数据库路径: {DB_PATH}")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
rows = cursor.execute("SELECT username, content FROM messages ORDER BY id").fetchall()
conn.close()
print(f"[3] 读取聊天记录条数: {len(rows)}")

history = "\n".join([f"{u}: {c}" for u, c in rows])
print(f"[4] 聊天历史内容长度: {len(history)}")

# 省略未用的变量和代码

system_content = (
    "你是一个markdown文档生成助手。请根据所有聊天内容，来判断其中当前或者说最新的聊天的情境和话题。再通过当前聊天，来判断当前需要生成什么样的markdown文档最能帮助当前的聊天人。同时下面还给出了可能被当前聊天提及的网页内容或者和当前聊天相关的数据库内容，作为辅助参考，但要以当前聊天话题为准。注意返回结果时，只输出完整的markdown文档内容。"
)
human_content = (
    "请根据所有聊天内容，来判断当前或者说最新的聊天情境和话题。再通过当前聊天，来判断当前需要生成什么样的markdown文档最能帮助当前的聊天人。"
    "同时下面还给出了可能被当前聊天提及的网页内容或者和当前聊天相关的数据库内容，作为辅助参考，但要以当前聊天话题为准。\n\n"
    "情境示例:"
    "如果聊天内容涉及做饭、食谱等，请生成详细的食谱markdown文档；"
    "如果涉及会议、讨论等，请生成会议纪要markdown文档；"
    "如有其他合适的文档类型，也可自动生成。"
    f"【所有聊天内容】\n{history}\n\n"
    "【辅助参考内容。可能含相关网页内容（可选）】\n{web_content}\n\n"
    "请只输出完整的markdown内容，不要有任何解释或多余内容。\n\n"
    "请注意，markdown格式中的换行只能用两个空格加换行符（\\n）来表示，不能用单个换行符。\n\n"
    "这是一个输出示例：'# 测试MD文件2\n这是第二个测试内容'"
)

api_key = os.getenv("OPENROUTER_API_KEY")
print(f"[5] 读取 OPENROUTER_API_KEY: {'已设置' if api_key else '未设置'}")

api_url = "https://api.deepseek.com/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
payload = {
    "model": "deepseek-chat",
    "messages": [
        {"role": "system", "content": system_content},
        {"role": "user", "content": human_content}
    ],
    "temperature": 0
}

print("[6] 调用 DeepSeek API...")
try:
    resp = requests.post(api_url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    resp_json = resp.json()
    print(f"[7] HTTP 状态码: {resp.status_code}")
    print(f"[8] DeepSeek 返回数据 keys: {list(resp_json.keys())}")

    md_text = resp_json["choices"][0]["message"]["content"]
    print(f"[9] 成功获取内容，长度: {len(md_text)}")

except Exception as e:
    md_text = f"# 错误\n\nDeepseek API 调用失败: {str(e)}"
    print(f"[9] 调用失败: {str(e)}")

print("\n[10] 生成的 Markdown 内容预览：\n")
print(md_text[:500])  # 打印前500字符预览

import time
import sqlite3

timestamp = time.strftime("%Y%m%d%H%M%S")
name = f"{timestamp}.md"

conn = sqlite3.connect("chat.db")
cursor = conn.cursor()
cursor.execute(
    "INSERT INTO md_messages (user_id, username, name, content) VALUES (?, ?, ?, ?)",
    (1, "admin", name, md_text)
)
conn.commit()
conn.close()

if len(sys.argv) > 1:
    output_path = sys.argv[1]
    print(f"[11] 指定输出文件路径: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(md_text)
    print(f"[12] 文件已写入: {output_path}")
else:
    print("[11] 未指定输出文件，跳过写文件步骤")

print("[13] 脚本执行完毕")
