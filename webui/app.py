import os
import uuid
import threading
import time
from flask import Flask, render_template, request, jsonify, send_file, abort

# 导入项目核心模块
from config.model_config import TRANSLATION_MODEL_PATH
from pipelines.translation_pipeline import TranslationPipeline
from config.settings import SUBTITLE_DIR

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # 用于 session（可选）

# 存储任务状态的字典 {task_id: {'status': str, 'progress': str, 'result': dict, 'error': str}}
tasks = {}


def run_translation_task(url, task_id):
    """后台运行翻译任务，更新任务状态"""
    try:
        tasks[task_id]['status'] = 'running'
        tasks[task_id]['progress'] = '正在下载视频和字幕...'

        pipeline = TranslationPipeline(TRANSLATION_MODEL_PATH)

        # 此处需要修改 pipeline.run 方法，使其能够返回生成的文件路径而不是直接打印
        # 为了简单起见，我们假设 pipeline.run 返回一个字典包含生成的文件路径
        # 如果原 pipeline.run 没有返回，可以稍作修改让它返回结果

        # 临时方案：重定向 stdout 捕获输出，但更好的做法是修改 pipeline.run 返回结果
        # 这里我们假设已经修改了 pipeline.run，使其返回 {'bilingual': path, 'chinese': path}
        # 如果没有修改，需要自行修改 pipeline.py 添加返回值

        # 示例：假设 pipeline.run 返回字典
        result = pipeline.run(url)  # 需要修改 pipeline.run 使其返回结果

        tasks[task_id]['status'] = 'completed'
        tasks[task_id]['result'] = result
        tasks[task_id]['progress'] = '完成'
    except Exception as e:
        tasks[task_id]['status'] = 'failed'
        tasks[task_id]['error'] = str(e)
        tasks[task_id]['progress'] = '错误'


@app.route('/')
def index():
    """主页面，直接返回内嵌的HTML"""
    return INDEX_HTML


@app.route('/start', methods=['POST'])
def start():
    """启动翻译任务"""
    url = request.form.get('url')
    if not url:
        return jsonify({'error': '请提供 YouTube 链接'}), 400

    task_id = str(uuid.uuid4())
    tasks[task_id] = {'status': 'pending', 'progress': '等待中...'}

    # 启动后台线程
    thread = threading.Thread(target=run_translation_task, args=(url, task_id))
    thread.daemon = True
    thread.start()

    return jsonify({'task_id': task_id})


@app.route('/status/<task_id>')
def status(task_id):
    """查询任务状态"""
    task = tasks.get(task_id)
    if not task:
        return jsonify({'error': '任务不存在'}), 404

    response = {
        'status': task['status'],
        'progress': task.get('progress', ''),
    }
    if task['status'] == 'completed':
        response['result'] = task.get('result', {})
    elif task['status'] == 'failed':
        response['error'] = task.get('error', '未知错误')

    return jsonify(response)


@app.route('/download/<filename>')
def download(filename):
    """提供字幕文件下载"""
    file_path = os.path.join(SUBTITLE_DIR, filename)
    if not os.path.exists(file_path):
        abort(404)
    return send_file(file_path, as_attachment=True)


# 简单的 HTML 模板（直接嵌入字符串，也可单独放在 templates/index.html）
INDEX_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>YT_AISpider 字幕翻译</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        input[type=text] { width: 70%; padding: 10px; }
        button { padding: 10px 20px; }
        #progress { margin-top: 20px; }
        #result { margin-top: 20px; }
        .file-link { display: block; margin: 5px 0; }
        .error { color: red; }
    </style>
</head>
<body>
    <h1>YouTube 字幕翻译工具</h1>
    <form id="form">
        <input type="text" id="url" name="url" placeholder="输入 YouTube 视频链接" required>
        <button type="submit">开始翻译</button>
    </form>

    <div id="progress" style="display:none;">
        <h3>处理中...</h3>
        <p id="status-text"></p>
    </div>

    <div id="result" style="display:none;">
        <h3>翻译完成！</h3>
        <div id="files"></div>
    </div>

    <script>
        const form = document.getElementById('form');
        const progressDiv = document.getElementById('progress');
        const resultDiv = document.getElementById('result');
        const statusText = document.getElementById('status-text');
        const filesDiv = document.getElementById('files');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const url = document.getElementById('url').value;

            // 隐藏结果，显示进度
            resultDiv.style.display = 'none';
            progressDiv.style.display = 'block';
            statusText.innerText = '启动任务...';

            try {
                const response = await fetch('/start', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: 'url=' + encodeURIComponent(url)
                });
                const data = await response.json();
                if (data.error) {
                    statusText.innerText = '错误：' + data.error;
                    return;
                }
                const taskId = data.task_id;
                pollStatus(taskId);
            } catch (err) {
                statusText.innerText = '请求失败：' + err;
            }
        });

        async function pollStatus(taskId) {
            const interval = setInterval(async () => {
                try {
                    const resp = await fetch('/status/' + taskId);
                    const data = await resp.json();
                    statusText.innerText = data.progress || data.status;

                    if (data.status === 'completed') {
                        clearInterval(interval);
                        progressDiv.style.display = 'none';
                        resultDiv.style.display = 'block';

                        // 显示下载链接
                        filesDiv.innerHTML = '';
                        if (data.result) {
                            for (const [key, path] of Object.entries(data.result)) {
                                const filename = path.split('/').pop();
                                const link = document.createElement('a');
                                link.href = '/download/' + encodeURIComponent(filename);
                                link.innerText = filename + ' (' + key + ')';
                                link.className = 'file-link';
                                filesDiv.appendChild(link);
                            }
                        }
                    } else if (data.status === 'failed') {
                        clearInterval(interval);
                        statusText.innerText = '失败：' + (data.error || '未知错误');
                    }
                } catch (err) {
                    clearInterval(interval);
                    statusText.innerText = '查询状态失败：' + err;
                }
            }, 2000);  // 每2秒查询一次
        }
    </script>
</body>
</html>
'''


# 为了简化，直接将模板作为字符串返回，不创建 templates 目录
@app.route('/simple')
def simple_index():
    return INDEX_HTML


# 或者也可以使用模板文件，但这里为了省事，将根路由指向 simple_index
@app.route('/')
def home():
    return INDEX_HTML


if __name__ == '__main__':
    # 确保字幕目录存在
    os.makedirs(SUBTITLE_DIR, exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)