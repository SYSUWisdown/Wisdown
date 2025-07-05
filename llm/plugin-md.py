import sqlite3
import os
import sys
import re
from dotenv import load_dotenv
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
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
            docs = [doc for doc in vectordb.docstore._dict.values() if doc.metadata and doc.metadata.get("url") == url]
            related_docs.extend(docs)
    else:
        related_docs = vectordb.similarity_search(recent_chat, k=2)
    web_content = "\n\n".join([doc.page_content[:500] for doc in related_docs[:2]])

# 主次分明的prompt内容
system_msg = SystemMessage(
    content="你是一个markdown文档生成助手。请根据所有聊天内容，来判断其中当前或者说最新的聊天的情境和话题。再通过当前聊天，来判断当前需要生成什么样的markdown文档最能帮助当前的聊天人。同时下面还给出了可能被当前聊天提及的网页内容或者和当前聊天相关的数据库内容，作为辅助参考，但要以当前聊天话题为准。注意返回结果时，只输出完整的markdown文档内容。"
)
human_msg = HumanMessage(
    content=(
        "请根据所有聊天内容，来判断当前或者说最新的聊天情境和话题。再通过当前聊天，来判断当前需要生成什么样的markdown文档最能帮助当前的聊天人。"
        "同时下面还给出了可能被当前聊天提及的网页内容或者和当前聊天相关的数据库内容，作为辅助参考，但要以当前聊天话题为准。\n\n"

        "情境示例:"
        "如果聊天内容涉及做饭、食谱等，请生成详细的食谱markdown文档；"
        "如果涉及会议、讨论等，请生成会议纪要markdown文档；"
        "如有其他合适的文档类型，也可自动生成。"
        
        f"【所有聊天内容】\n{history}\n\n"
        f"【辅助参考内容。可能含相关网页内容（可选）】\n{web_content}\n\n"
        "请只输出完整的markdown内容，不要有任何解释或多余内容。\n\n"
    )
)

llm = ChatOpenAI(
    temperature=0,
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    openai_api_base="https://openrouter.ai/api/v1",
    model="qwen/qwq-32b:free"
)

response = llm([system_msg, human_msg])
md_text = response.content

# 将生成的markdown内容写入数据库
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute(
    "INSERT INTO md_messages (user_id, username, name, content) VALUES (?, ?, ?, ?)",
    (1, 'admin', 'md-test.md', md_text)
)
conn.commit()
conn.close()

if len(sys.argv) > 1:
    output_path = sys.argv[1]
    with open(output_path, 'w') as f:
        f.write(md_text)