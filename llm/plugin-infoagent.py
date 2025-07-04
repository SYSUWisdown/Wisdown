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

# 3. 天气工具
weather = OpenWeatherMapAPIWrapper(openweathermap_api_key=os.getenv("OPENWEATHER_API_KEY"))

# 4. 时间工具
@tool
def get_current_time(_input=""):
    """获取当前时间和日期"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 5. 新闻工具
news = NewsAPIToolWrapper(newsapi_api_key=os.getenv("NEWSAPI_KEY"))

# 6. 体育工具
sports = SportsDataAPIWrapper(sportsdata_api_key=os.getenv("SPORTSDATA_API_KEY"))

# 注册工具
tools = [
    Tool(name="Search", func=ddg_search.run, description="用于搜索实时网络信息"),
    Tool(name="Wikipedia", func=wikipedia.run, description="查询百科信息，如术语、人物、事件等"),
    Tool(name="Weather", func=weather.run, description="获取某地当前天气，输入地名"),
    Tool(name="Time", func=get_current_time, description="获取当前日期和时间"),
    Tool(name="News", func=news.run, description="获取最新新闻摘要"),
    Tool(name="Sports", func=sports.run, description="获取最新体育赛事信息")
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

输出内容请使用 Markdown 格式，清晰展示：
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

# ===================== 保存 Markdown 文件 =====================
if len(sys.argv) > 1:
    output_path = sys.argv[1]
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(response)
else:
    print(response)