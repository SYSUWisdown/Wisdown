import sqlite3
import os
import sys
import requests
from dotenv import load_dotenv

print("[plugin-reasoner] 脚本开始执行")
load_dotenv()

DB_PATH = os.path.join(os.path.dirname(__file__), 'chat.db')
print(f"[plugin-reasoner] 读取数据库路径: {DB_PATH}")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
rows = cursor.execute("SELECT username, content FROM messages ORDER BY id").fetchall()
conn.close()
print(f"[plugin-reasoner] 读取聊天记录条数: {len(rows)}")

history = "\n".join([f"{u}: {c}" for u, c in rows])
print(f"[plugin-reasoner] 聊天历史长度: {len(history)} 字符")

api_key = os.getenv("OPENROUTER_API_KEY")
print(f"[plugin-reasoner] 读取 OPENROUTER_API_KEY: {'已设置' if api_key else '未设置'}")

api_url = "https://api.deepseek.com/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# 第一步：提取推理问题
extract_prompt = (
    "你是一个推理任务识别助手，擅长从对话中识别出需要推理、计算、逻辑分析或证明的问题。\n"
    "请从下面的聊天内容中，判断是否存在需要你进行推理、证明、复杂分析或数学计算的问题。\n"
    "如果有，请只提取那个完整问题本身（不要加入任何额外话语），如果没有，请仅返回空字符串。\n\n"
    f"聊天内容：\n{history}"
)
extract_payload = {
    "model": "deepseek-chat",
    "messages": [
        {"role": "system", "content": "你是一个推理任务识别助手。"},
        {"role": "user", "content": extract_prompt}
    ],
    "temperature": 0
}

print("[plugin-reasoner] 调用 DeepSeek API，提取推理问题...")
try:
    resp = requests.post(api_url, headers=headers, json=extract_payload, timeout=60)
    resp.raise_for_status()
    resp_json = resp.json()
    print(f"[plugin-reasoner] 提取问题接口返回 keys: {list(resp_json.keys())}")
    question = resp_json["choices"][0]["message"]["content"].strip()
    print(f"[plugin-reasoner] 提取到的推理问题: '{question}'")
except Exception as e:
    print(f"[plugin-reasoner] 提取推理问题失败: {e}")
    sys.exit(1)

if not question:
    markdown = "# 当前聊天未检测到需要推理的问题。"
    print("[plugin-reasoner] 无需推理，结束执行。")
else:
    print("[plugin-reasoner] 发现推理问题，开始链式推理...")
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
    cot_prompt = (
        "你是一个严谨的逻辑推理助手，擅长解决复杂问题并展示你的推理思路。你的回答将用于展示给用户阅读，请使用结构清晰的 Markdown 输出。\n\n"
        + few_shot_example +
        "请使用与上述完全一致的风格和格式，解决下面的问题：\n\n"
        f"## 推理问题\n{question}\n\n"
        "## 思维过程\n（请详细分步推理，展示你的逻辑分析或计算过程）\n\n"
        "## 回答\n（请总结你的最终结论）"
    )
    cot_payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一个严谨的逻辑推理助手。"},
            {"role": "user", "content": cot_prompt}
        ],
        "temperature": 0
    }

    print("[plugin-reasoner] 调用 DeepSeek API，执行链式推理...")
    try:
        resp2 = requests.post(api_url, headers=headers, json=cot_payload, timeout=120)
        resp2.raise_for_status()
        resp2_json = resp2.json()
        print(f"[plugin-reasoner] 链式推理接口返回 keys: {list(resp2_json.keys())}")
        markdown = resp2_json["choices"][0]["message"]["content"].strip()
        print(f"[plugin-reasoner] 推理结果长度: {len(markdown)} 字符")
    except Exception as e:
        markdown = f"# 错误\n\nDeepseek API 调用失败: {str(e)}"
        print(f"[plugin-reasoner] 链式推理调用失败: {e}")

# 输出到指定markdown文件或打印
if len(sys.argv) > 1:
    output_path = sys.argv[1]
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown)

    import time
    import sqlite3

    timestamp = time.strftime("%Y%m%d%H%M%S")
    name = f"{timestamp}.md"

    conn = sqlite3.connect("chat.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO md_messages (user_id, username, name, content) VALUES (?, ?, ?, ?)",
        (1, "admin", name, markdown)
    )
    conn.commit()
    conn.close()

    print(f"[plugin-reasoner] 已写入: {output_path}", flush=True)
    print("[plugin-reasoner] 内容预览:", flush=True)
    print("\n".join(markdown.splitlines()[:10]), flush=True)
else:
    print("[plugin-reasoner] 直接输出推理结果：\n")
    print(markdown)
