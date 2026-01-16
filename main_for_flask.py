from flask import Flask, render_template, request, jsonify
import threading
import time
import os
from flask import Flask, render_template_string

# 模拟剪贴板（实际安卓打包后需用原生接口，这里先用内存存储）
clipboard_content = ""
history_stack = []
history_index = -1

app = Flask(__name__)

# 简易 HTML 模板（内嵌到代码，避免额外文件）
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>剪贴板历史工具</title>
    <style>
        * {margin: 0; padding: 0; box-sizing: border-box;}
        body {padding: 20px; font-family: sans-serif; background: #fff;}
        .top-bar {display: flex; gap: 10px; margin-bottom: 15px; align-items: center;}
        .clipboard-label {flex: 1; font-size: 14px; color: #333;}
        .clear-clipboard-btn {padding: 8px 16px; background: #e63946; color: white; border: none; border-radius: 4px; cursor: pointer;}
        textarea {width: 100%; height: 300px; padding: 10px; border: 1px solid #ddd; border-radius: 4px; margin-bottom: 15px; resize: none;}
        .tip {height: 30px; line-height: 30px; text-align: center; color: #2a9d8f; margin-bottom: 15px;}
        .button-group {display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;}
        button {padding: 12px 0; border: none; border-radius: 4px; color: white; font-size: 16px; cursor: pointer;}
    </style>
</head>
<body>
    <div class="top-bar">
        <div class="clipboard-label">剪贴板内容：{{ clipboard }}</div>
        <button class="clear-clipboard-btn" onclick="clearClipboard()">清空剪贴板</button>
    </div>
    <textarea id="content" placeholder="请输入要处理的内容（支持多行）"></textarea>
    <div class="tip" id="tip"></div>
    <div class="button-group">
        <button style="background: #457b9d;" onclick="writeToClipboard()">写入</button>
        <button style="background: #7209b7;" onclick="writeAndClear()">写入并清空</button>
        <button style="background: #e63946;" onclick="clearOnly()">清空</button>
        <button style="background: #2a9d8f;" onclick="restorePrev()">恢复上一条</button>
        <button style="background: #f4a261;" onclick="restoreNext()">恢复下一条</button>
        <button style="background: #6c757d;" onclick="clearHistory()">清空历史</button>
    </div>

    <script>
        // 显示提示
        function showTip(text, isSuccess=true) {
            const tip = document.getElementById('tip');
            tip.style.color = isSuccess ? '#2a9d8f' : '#e63946';
            tip.textContent = text;
            setTimeout(() => tip.textContent = '', 3000);
        }

        // 获取剪贴板内容
        function getClipboard() {
            fetch('/api/clipboard')
                .then(res => res.json())
                .then(data => document.querySelector('.clipboard-label').textContent = `剪贴板内容：${data.content}`);
        }

        // 清空剪贴板
        function clearClipboard() {
            fetch('/api/clipboard/clear', {method: 'POST'})
                .then(res => res.json())
                .then(data => {
                    showTip(data.msg, data.success);
                    getClipboard();
                });
        }

        // 写入剪贴板
        function writeToClipboard() {
            const content = document.getElementById('content').value.trim();
            if (!content) {showTip('输入框为空', false); return;}
            fetch('/api/write', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({content: content})
            }).then(res => res.json()).then(data => {
                showTip(data.msg, data.success);
                getClipboard();
            });
        }

        // 写入并清空
        function writeAndClear() {
            const content = document.getElementById('content').value.trim();
            if (!content) {showTip('输入框为空', false); return;}
            fetch('/api/write-clear', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({content: content})
            }).then(res => res.json()).then(data => {
                showTip(data.msg, data.success);
                document.getElementById('content').value = '';
                getClipboard();
            });
        }

        // 仅清空输入框
        function clearOnly() {
            const content = document.getElementById('content').value.trim();
            if (!content) {showTip('输入框已空', false); return;}
            fetch('/api/clear-only', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({content: content})
            }).then(res => res.json()).then(data => {
                showTip(data.msg, data.success);
                document.getElementById('content').value = '';
            });
        }

        // 恢复上一条
        function restorePrev() {
            fetch('/api/restore-prev')
                .then(res => res.json())
                .then(data => {
                    showTip(data.msg, data.success);
                    if (data.content) document.getElementById('content').value = data.content;
                });
        }

        // 恢复下一条
        function restoreNext() {
            fetch('/api/restore-next')
                .then(res => res.json())
                .then(data => {
                    showTip(data.msg, data.success);
                    if (data.content) document.getElementById('content').value = data.content;
                });
        }

        // 清空历史
        function clearHistory() {
            fetch('/api/clear-history', {method: 'POST'})
                .then(res => res.json())
                .then(data => showTip(data.msg, data.success));
        }

        // 初始化
        window.onload = getClipboard;
    </script>
</body>
</html>
"""

# Flask 路由
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, clipboard=clipboard_content or "空")

@app.route('/api/clipboard')
def get_clipboard():
    global clipboard_content
    display_content = clipboard_content if clipboard_content else "空"
    if len(display_content) > 20:
        display_content = display_content[:20] + "..."
    return jsonify({"content": display_content})

@app.route('/api/clipboard/clear', methods=['POST'])
def clear_clipboard():
    global clipboard_content
    clipboard_content = ""
    return jsonify({"success": True, "msg": "✓ 剪贴板已清空"})

@app.route('/api/write', methods=['POST'])
def write_to_clipboard():
    global clipboard_content, history_stack, history_index
    content = request.json.get('content')
    clipboard_content = content
    history_stack.append(content)
    history_index = len(history_stack) - 1
    return jsonify({"success": True, "msg": f"✓ 已写入（共 {len(history_stack)} 条）"})

@app.route('/api/write-clear', methods=['POST'])
def write_and_clear():
    global clipboard_content, history_stack, history_index
    content = request.json.get('content')
    clipboard_content = content
    history_stack.append(content)
    history_index = len(history_stack) - 1
    return jsonify({"success": True, "msg": f"✓ 已写入并清空（共 {len(history_stack)} 条）"})

@app.route('/api/clear-only', methods=['POST'])
def clear_only():
    global history_stack, history_index
    content = request.json.get('content')
    history_stack.append(content)
    history_index = len(history_stack) - 1
    return jsonify({"success": True, "msg": f"✓ 已清空输入框（共 {len(history_stack)} 条）"})

@app.route('/api/restore-prev')
def restore_prev():
    global history_stack, history_index
    if not history_stack:
        return jsonify({"success": False, "msg": "暂无历史记录"})
    if history_index > 0:
        history_index -= 1
        content = history_stack[history_index]
        return jsonify({"success": True, "msg": f"已恢复上一条（{history_index+1}/{len(history_stack)}）", "content": content})
    else:
        return jsonify({"success": False, "msg": "已是第一条记录", "content": history_stack[0]})

@app.route('/api/restore-next')
def restore_next():
    global history_stack, history_index
    if not history_stack:
        return jsonify({"success": False, "msg": "暂无历史记录"})
    if history_index < len(history_stack)-1:
        history_index += 1
        content = history_stack[history_index]
        return jsonify({"success": True, "msg": f"已恢复下一条（{history_index+1}/{len(history_stack)}）", "content": content})
    else:
        return jsonify({"success": False, "msg": "已是最后一条记录"})

@app.route('/api/clear-history', methods=['POST'])
def clear_history():
    global history_stack, history_index
    history_stack.clear()
    history_index = -1
    return jsonify({"success": True, "msg": "✓ 历史记录已清空"})

# 启动 Flask 服务（后台线程）
def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

# if __name__ == '__main__':
#     # 打包后需注释此行，由安卓启动脚本触发
#     #run_flask()
#     pass

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy_garden.webview import WebView
import threading

class WebViewApp(App):
    def build(self):
        # 后台启动 Flask 服务
        threading.Thread(target=run_flask, daemon=True).start()
        # 创建 WebView 加载本地 Flask 页面
        webview = WebView(url='http://127.0.0.1:5000', enable_javascript=True)
        return webview

if __name__ == '__main__':
    WebViewApp().run()
