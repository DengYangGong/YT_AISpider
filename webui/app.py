import os
import threading
import uuid

from flask import Flask, render_template, request, jsonify, send_file, abort, url_for
from werkzeug.utils import secure_filename

# 导入项目核心模块
from config.model_config import TRANSLATION_MODEL_PATH
from config.settings import SUBTITLE_DIR, VIDEO_DIR
from pipelines.translation_pipeline import TranslationPipeline

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 限制上传文件最大 50MB
app.config['UPLOAD_FOLDER'] = 'webui/uploads'  # 临时存放上传的知识库文件
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 存储任务状态 {task_id: {...}}
tasks = {}


def run_translation_task(url, context_size, knowledge_files, task_id):
    """后台运行翻译任务（支持自定义上下文大小和知识库文件）"""
    try:
        tasks[task_id]['status'] = 'running'
        tasks[task_id]['progress'] = '正在下载字幕...'

        # 将上传的知识库文件保存到临时目录，并构建文件列表
        # 保存上传文件到临时目录，获得路径列表
        kb_paths = []
        if knowledge_files:
            kb_dir = os.path.join(app.config['UPLOAD_FOLDER'], task_id)
            os.makedirs(kb_dir, exist_ok=True)
            for file in knowledge_files:
                filename = secure_filename(file.filename)
                save_path = os.path.join(kb_dir, filename)
                file.save(save_path)
                kb_paths.append(save_path)

        pipeline = TranslationPipeline(
            model_path=TRANSLATION_MODEL_PATH,
            context_size=context_size,
            knowledge_files=kb_paths if kb_paths else None
        )
        result = pipeline.run(url)

        tasks[task_id]['status'] = 'completed'
        tasks[task_id]['result'] = result
        tasks[task_id]['progress'] = '完成'
    except Exception as e:
        tasks[task_id]['status'] = 'failed'
        tasks[task_id]['error'] = str(e)
        tasks[task_id]['progress'] = '错误'


@app.route('/')
def index():
    return INDEX_HTML


@app.route('/start', methods=['POST'])
def start():
    """启动翻译任务"""
    url = request.form.get('url')
    context_size = request.form.get('context_size', 3, type=int)
    knowledge_files = request.files.getlist('knowledge_files')  # 多文件上传

    if not url:
        return jsonify({'error': '请提供 YouTube 链接'}), 400

    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        'status': 'pending',
        'progress': '等待中...',
        'context_size': context_size,
        'knowledge_files': knowledge_files  # 保存文件对象供后台线程使用
    }

    # 启动后台线程
    thread = threading.Thread(
        target=run_translation_task,
        args=(url, context_size, knowledge_files, task_id)
    )
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
        # 返回文件下载链接和视频播放信息
        result = task.get('result', {})
        response['result'] = {
            'bilingual': url_for('download', filename=os.path.basename(result.get('bilingual', ''))),
            'chinese': url_for('download', filename=os.path.basename(result.get('chinese', ''))),
            'video': url_for('video', filename=os.path.basename(result.get('video', ''))) if result.get(
                'video') else None
        }
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


@app.route('/video/<filename>')
def video(filename):
    """提供视频文件流（用于播放）"""
    file_path = os.path.join(VIDEO_DIR, filename)
    if not os.path.exists(file_path):
        abort(404)
    return send_file(file_path, mimetype='video/mp4')  # 假设视频为 mp4 格式


# 简单的 HTML 模板（使用 Jinja2 模板）
INDEX_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>YT_AISpider 字幕翻译增强版</title>
    <style>
        body { font-family: Arial; max-width: 900px; margin: 50px auto; padding: 20px; }
        input[type=text], input[type=number] { width: 70%; padding: 10px; margin: 5px 0; }
        input[type=file] { margin: 5px 0; }
        button { padding: 10px 20px; }
        #progress { margin-top: 20px; }
        #result { margin-top: 20px; }
        .file-link { display: block; margin: 5px 0; }
        video { width: 100%; max-height: 500px; margin-top: 20px; }
        .error { color: red; }
    </style>
</head>
<body>
    <h1>YouTube 字幕翻译工具（增强版）</h1>
    <form id="form" enctype="multipart/form-data">
        <div>
            <label>YouTube 视频链接：</label><br>
            <input type="text" id="url" name="url" required>
        </div>
        <div>
            <label>上下文参考数量（默认3）：</label><br>
            <input type="number" id="context_size" name="context_size" value="3" min="1" max="10">
        </div>
        <div>
            <label>上传自定义知识库文件（txt格式，多选）：</label><br>
            <input type="file" id="knowledge_files" name="knowledge_files" multiple accept=".txt">
        </div>
        <button type="submit">开始翻译</button>
    </form>

    <div id="progress" style="display:none;">
        <h3>处理中...</h3>
        <p id="status-text"></p>
    </div>

    <div id="result" style="display:none;">
        <h3>翻译完成！</h3>
        <div id="files"></div>
        <div id="video-container" style="display:none;">
            <h4>视频预览（带双语字幕）：</h4>
            <video id="video-player" controls>
                <track id="subtitle-track" kind="subtitles" srclang="zh" label="双语">
            </video>
        </div>
    </div>

    <script>
        const form = document.getElementById('form');
        const progressDiv = document.getElementById('progress');
        const resultDiv = document.getElementById('result');
        const statusText = document.getElementById('status-text');
        const filesDiv = document.getElementById('files');
        const videoContainer = document.getElementById('video-container');
        const videoPlayer = document.getElementById('video-player');
        const subtitleTrack = document.getElementById('subtitle-track');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(form);

            // 隐藏结果，显示进度
            resultDiv.style.display = 'none';
            videoContainer.style.display = 'none';
            progressDiv.style.display = 'block';
            statusText.innerText = '启动任务...';

            try {
                const response = await fetch('/start', {
                    method: 'POST',
                    body: formData
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
                            if (data.result.bilingual) {
                                const link = document.createElement('a');
                                link.href = data.result.bilingual;
                                link.innerText = '下载双语字幕';
                                link.className = 'file-link';
                                filesDiv.appendChild(link);
                            }
                            if (data.result.chinese) {
                                const link = document.createElement('a');
                                link.href = data.result.chinese;
                                link.innerText = '下载中文字幕';
                                link.className = 'file-link';
                                filesDiv.appendChild(link);
                            }
                        }

                        // 如果有视频，显示播放器
                        if (data.result && data.result.video) {
                            videoContainer.style.display = 'block';
                            videoPlayer.src = data.result.video;
                            // 设置字幕轨道（需要将字幕文件转换为 WebVTT 或直接使用 SRT？浏览器支持 SRT 有限）
                            // 这里假设我们生成了 WebVTT 版本的双语字幕，或者浏览器支持 SRT
                            // 简单起见，我们可以将双语字幕文件的 URL 作为 track 的 src
                            // 但浏览器通常只支持 WebVTT，需要转换。我们暂时不实现，留待扩展。
                            // 或者直接提示用户下载字幕后用本地播放器加载。
                            subtitleTrack.src = data.result.bilingual;  // 尝试加载 SRT，不一定有效
                        }
                    } else if (data.status === 'failed') {
                        clearInterval(interval);
                        statusText.innerText = '失败：' + (data.error || '未知错误');
                    }
                } catch (err) {
                    clearInterval(interval);
                    statusText.innerText = '查询状态失败：' + err;
                }
            }, 2000);
        }
    </script>
</body>
</html>
'''


# 为了简化，直接将模板作为字符串返回（也可以使用 templates/index.html）
@app.route('/')
def home():
    return INDEX_HTML


if __name__ == '__main__':
    os.makedirs(SUBTITLE_DIR, exist_ok=True)
    os.makedirs(VIDEO_DIR, exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
