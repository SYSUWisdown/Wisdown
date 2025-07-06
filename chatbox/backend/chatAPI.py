from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    # 返回 reply 字段
    return jsonify({
        "reply": "# 这是Python生成的Markdown内容\n支持markdown\n可以自定义输出"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001)