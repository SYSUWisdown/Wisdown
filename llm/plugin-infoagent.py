import os
import sys
import sqlite3
from dotenv import load_dotenv
from datetime import datetime
from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, Tool, AgentType
from langchain.tools import tool
from langchain.utilities import WikipediaAPIWrapper
from langchain_community.utilities import (
    OpenWeatherMapAPIWrapper,
    DuckDuckGoSearchAPIWrapper,
    NewsAPIToolWrapper,
    SportsDataAPIWrapper
)

# ===================== 加载环境变量 =====================
load_dotenv()

# ===================== 读取聊天历史 =====================
DB_PATH = os.path.join(os.path.dirname(__file__), '../llm/chat.db')
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
rows = cursor.execute("SELECT username, content FROM messages ORDER BY id").fetchall()
conn.close()
history = "\n".join([f"{u}: {c}" for u, c in rows])

# ===================== 定义工具 =====================

# 1. 搜索引擎工具
ddg_search = DuckDuckGoSearchAPIWrapper()

# 2. 百科工具
wikipedia = WikipediaAPIWrapper()

# 3. 天气工具（DuckDuckGo替代）
# @tool
# def search_weather(location: str) -> str:
#     """获取某地天气信息（基于搜索，无需API）"""
#     return ddg_search.run(f"weather in {location}")

# 4. 时间工具
@tool
def get_current_time(_input=""):
    """获取当前时间和日期"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 5. 新闻工具（DuckDuckGo替代）
# @tool
# def search_news(topic: str) -> str:
#     """获取新闻摘要（基于搜索，无需API）"""
#     return ddg_search.run(f"latest news about {topic}")

# 注册工具
tools = [
    Tool(name="Search", func=ddg_search.run, description="用于搜索实时网络信息"),
    Tool(name="Wikipedia", func=wikipedia.run, description="查询百科信息，如术语、人物、事件等"),
    # Tool(name="WeatherSearch", func=search_weather, description="获取某地天气信息（无需API）"),
    Tool(name="Time", func=get_current_time, description="获取当前日期和时间"),
    # Tool(name="NewsSearch", func=search_news, description="获取新闻摘要（无需API）")
]



# ===================== 初始化 Agent =====================
llm = ChatOpenAI(
    temperature=0,
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    openai_api_base="https://openrouter.ai/api/v1"
)

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# ===================== 构造 Agent 提示 =====================
prompt = f"""
你是一个智能助手，负责根据完整的聊天内容判断当前聊天人在什么情境下，最需要获取什么信息。

请根据下方完整聊天记录，从中判断当前聊天人最可能关心的**一个具体问题**，并主动使用合适的工具（搜索、百科、天气、时间、新闻、体育）获取并解答这个问题。

输出内容请严格使用 Markdown 格式，清晰展示：
## 问题（你判断出的需要的信息）
...

## 获取的信息
...

## 简明回答
...

完整聊天记录如下：
{history}
"""

# ===================== 调用 Agent 并获取 Markdown =====================
response = agent.run(prompt)
md_text = response.content

if len(sys.argv) > 1:
    output_path = sys.argv[1]
    with open(output_path, 'w') as f:
        f.write(md_text)
else:
    print(response)