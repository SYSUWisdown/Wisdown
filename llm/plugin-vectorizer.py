import os
import re
import sqlite3
from dotenv import load_dotenv
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import WebBaseLoader, Document
from langchain.document_loaders import YoutubeLoader
# from some_bilibili_loader import BilibiliLoader

load_dotenv()

# 1. 读取聊天历史
DB_PATH = os.path.join(os.path.dirname(__file__), '../llm/chat.db')
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
rows = cursor.execute("SELECT content FROM messages ORDER BY id").fetchall()
conn.close()
history = "\n".join([c[0] for c in rows])

# 2. 提取网址
url_pattern = re.compile(r'(https?://[\w\-./?%&=:#]+)')
urls = set(url_pattern.findall(history))

# 3. 加载/初始化向量库
VECTOR_DB_PATH = os.path.join(os.path.dirname(__file__), "vector_db")
if os.path.exists(VECTOR_DB_PATH):
    vectordb = FAISS.load_local(VECTOR_DB_PATH, OpenAIEmbeddings())
else:
    vectordb = FAISS.from_texts([], OpenAIEmbeddings())

# 4. 检查已收录的网址（用metadata存url）
existing_urls = set()
if hasattr(vectordb, 'docstore'):
    for doc_id in vectordb.docstore._dict:
        meta = vectordb.docstore._dict[doc_id].metadata
        if meta and 'url' in meta:
            existing_urls.add(meta['url'])

# 5. 处理新网址
for url in urls - existing_urls:
    docs = []
    try:
        if 'bilibili.com' in url:
            # loader = BilibiliLoader(url)
            # docs = loader.load()
            docs = [Document(page_content=f"[B站视频] {url}", metadata={"url": url})]
        elif 'youtube.com' in url or 'youtu.be' in url:
            loader = YoutubeLoader.from_youtube_url(url)
            docs = loader.load()
            for d in docs:
                d.metadata["url"] = url
        else:
            loader = WebBaseLoader(url)
            docs = loader.load()
            for d in docs:
                d.metadata["url"] = url
    except Exception as e:
        docs = [Document(page_content=f"[内容抓取失败] {url}，原因：{e}", metadata={"url": url})]
    # 分块
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    split_docs = splitter.split_documents(docs)
    # 向量化并入库
    vectordb.add_documents(split_docs)

# 6. 持久化向量库
vectordb.save_local(VECTOR_DB_PATH)
