print('111')
import sqlite3
import os
import sys
import requests
import json
import subprocess

# 读取历史聊天内容
DB_PATH = os.path.join(os.path.dirname(__file__), 'chat.db')
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
rows = cursor.execute("SELECT username, content FROM messages ORDER BY id").fetchall()
conn.close()
history = "\n".join([f"{u}: {c}" for u, c in rows])

print('222')

# 构造 prompt
prompt = (
    "你是一个UML图生成助手。请根据所有聊天内容，生成最有帮助的PlantUML流程图代码块。"
    "要求："
    "1. 只输出标准PlantUML流程图代码，必须以@startuml开头、@enduml结尾。"
    "2. 每一步用 :步骤内容; 表示，步骤之间用箭头连接（start、stop）。"
    "3. 不要输出多余内容。"
    "只能在图中使用英语.只能在图中使用英语.只能在图中使用英语.只能在图中使用英语."
    f"【所有聊天内容】\n{history}\n"
)

# 调用 OpenRouter API
api_key = os.getenv("OPENROUTER_API_KEY")
api_url = "https://api.deepseek.com/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
data = {
    "model": "deepseek-chat",
    "messages": [
        {"role": "system", "content": "你是一个UML图生成助手。"},
        {"role": "user", "content": prompt}
    ],
    "temperature": 0
}
response = requests.post(api_url, headers=headers, data=json.dumps(data))


try:
    result = response.json()
    print('✅ DeepSeek 返回内容如下：')
    print("HTTP 状态码:", response.status_code)
    print("返回数据类型:", type(result))
    print("完整返回 keys:", result.keys())
    print(json.dumps(result, indent=2))
except Exception as e:
    print("❌ 无法解析 DeepSeek 返回的 JSON，原因如下：")
    print(e)
    print("🔁 响应原始内容如下（response.text）：")
    print(response.text)
    sys.exit(1)

if "choices" not in result:
    print("deepseek API 返回异常，没有choices字段！")
    sys.exit(1)
uml_text = result['choices'][0]['message']['content']

print('333')

# 只保留代码块内容
if '```' in uml_text:
    uml_text = uml_text.split('```')[1].replace('plantuml', '').strip()

print('444')

# 输出到指定文件
if len(sys.argv) > 1:
    output_path = sys.argv[1]
    if not output_path.lower().endswith('.png'):
        output_path += '.png'
    temp_uml_path = output_path + '.temp.puml'
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        print(f"输出目录 {output_dir} 不存在，正在创建...")
        os.makedirs(output_dir, exist_ok=True)
    print(f"写入UML到临时文件: {temp_uml_path}")
    with open(temp_uml_path, 'w') as f:
        f.write(uml_text)
    try:
        print(f"调用PlantUML渲染图片...")
        subprocess.run(["plantuml", "-tpng", temp_uml_path], check=True)
        png_path = temp_uml_path.replace('.puml', '.png')
        print(f"渲染完成，图片路径: {png_path}")
        os.replace(png_path, output_path)
        print(f"图片已保存到: {output_path}")
    except Exception as e:
        print("PlantUML 渲染失败：", e)
        print(f"临时PUML文件保留在: {temp_uml_path}")
        if os.path.exists(temp_uml_path.replace('.puml', '.png')):
            print(f"渲染失败但生成了图片: {temp_uml_path.replace('.puml', '.png')}")

print('555')