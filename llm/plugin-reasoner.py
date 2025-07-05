import sqlite3
import os
import sys
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

# 加载环境变量
load_dotenv()

# 读取聊天历史
DB_PATH = os.path.join(os.path.dirname(__file__), 'chat.db')
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
rows = cursor.execute("SELECT username, content FROM messages ORDER BY id").fetchall()
conn.close()
history = "\n".join([f"{u}: {c}" for u, c in rows])

# 初始化langchain大模型
llm = ChatOpenAI(
    temperature=0,
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    openai_api_base="https://openrouter.ai/api/v1"
)

# 第一步：用大模型自动提取当前需要推理的问题
extract_template = ChatPromptTemplate.from_messages([
    ("system", "你是一个推理任务识别助手，擅长从对话中识别出需要推理、计算、逻辑分析或证明的问题。"),
    ("user", 
     "请从下面的聊天内容中，判断是否存在需要你进行推理、证明、复杂分析或数学计算的问题。\
如果有，请只提取那个完整问题本身（不要加入任何额外话语），如果没有，请仅返回空字符串。\n\n聊天内容：\n{history}")
])
extract_chain = extract_template | llm
extract_result = extract_chain.invoke({"history": history})
question = extract_result.content.strip()

# 如果没有检测到推理问题，输出提示
if not question:
    markdown = "# 当前聊天未检测到需要推理的问题。"
else:
    # 第二步：用同一个大模型进行思维链推理，输出markdown

    few_shot_example = (
        "下面是几个推理问题的示范，请学习其结构与推理方式：\n\n"
        "### 示例 1：证明 √2 是无理数\n"
        "```\n"
        "## 推理问题\n"
        "证明：√2 是无理数。\n\n"
        "## 思维过程\n"
        "Step 1: 假设 √2 是有理数，可以写成最简分数 a/b（a 和 b 互质，b ≠ 0）。\n"
        "Step 2: 则 √2 = a/b ⇒ 2 = a² / b² ⇒ a² = 2b²。\n"
        "Step 3: a² 是偶数 ⇒ a 是偶数，设 a = 2k，则 a² = 4k²。\n"
        "Step 4: 代入得 4k² = 2b² ⇒ b² = 2k² ⇒ b 也是偶数。\n"
        "Step 5: a 和 b 都是偶数，与“互质”矛盾 ⇒ 假设不成立。\n"
        "Step 6: 所以 √2 不是有理数，它是无理数。\n\n"
        "## 回答\n"
        "√2 是无理数。\n"
        "```\n\n"

        "### 示例 2：归纳法证明数列求和公式\n"
        "```\n"
        "## 推理问题\n"
        "证明：1 + 2 + ... + n = n(n + 1)/2 对所有正整数 n 成立。\n\n"
        "## 思维过程\n"
        "Step 1: 使用数学归纳法。首先验证 n = 1 的情形。\n"
        "Step 2: 当 n = 1，左边 = 1，右边 = 1(1+1)/2 = 1，成立。\n"
        "Step 3: 假设当 n = k 时成立，即 1 + 2 + ... + k = k(k+1)/2。\n"
        "Step 4: 需要证明当 n = k+1 时也成立。\n"
        "Step 5: 左边变为 (1 + 2 + ... + k) + (k+1)，根据归纳假设得：\n"
        "(k(k+1)/2) + (k+1) = [(k(k+1) + 2(k+1))]/2 = (k+1)(k+2)/2。\n"
        "Step 6: 右边为 (k+1)(k+2)/2，等式成立。\n\n"
        "## 回答\n"
        "1 + 2 + ... + n = n(n + 1)/2 对所有正整数 n 成立。\n"
        "```\n\n"

        "### 示例 3：单位换算与速算\n"
        "```\n"
        "## 推理问题\n"
        "一辆汽车以60千米/小时的速度行驶2.5小时，行驶了多少米？\n\n"
        "## 思维过程\n"
        "Step 1: 先计算总路程，60千米/小时 × 2.5小时 = 150千米。\n"
        "Step 2: 将千米换算成米，150千米 × 1000 = 150000米。\n\n"
        "## 回答\n"
        "这辆汽车行驶了150000米。\n"
        "```\n\n"
    )

    cot_template = ChatPromptTemplate.from_messages([
    ("system", "你是一个严谨的逻辑推理助手，擅长解决复杂问题并展示你的推理思路。你的回答将用于展示给用户阅读，请使用结构清晰的 Markdown 输出。"),
    ("user", 
         few_shot_example +
         "请使用与上述完全一致的风格和格式，解决下面的问题：\n\n"
         "## 推理问题\n"
         "{question}\n\n"
         "## 思维过程\n"
         "（请详细分步推理，展示你的逻辑分析或计算过程）\n\n"
         "## 回答\n"
         "（请总结你的最终结论）")
    ])
    cot_chain = cot_template | llm
    cot_result = cot_chain.invoke({"question": question})
    markdown = cot_result.content.strip()

# 输出到指定markdown文件
if len(sys.argv) > 1:
    output_path = sys.argv[1]
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown)
    # 新增：执行后输出关键信息
    print(f"[plugin-reasoner] 已写入: {output_path}", flush=True)
    print("[plugin-reasoner] 内容预览:", flush=True)
    print("\n".join(markdown.splitlines()[:10]), flush=True)
else:
    print(markdown)