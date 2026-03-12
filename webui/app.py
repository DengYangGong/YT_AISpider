import os
import threading
import uuid

from flask import Flask, request, jsonify, send_file, abort, url_for
from flask import render_template
from werkzeug.utils import secure_filename

# 导入项目配置和核心模块
from config.model_config import TRANSLATION_MODEL_PATH
from config.settings import SUBTITLE_DIR, VIDEO_DIR
from pipelines.translation_pipeline import TranslationPipeline

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yt-aispider-secret-key'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 限制上传文件最大 50MB
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 确保数据目录存在
os.makedirs(SUBTITLE_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# 存储任务状态 {task_id: {...}}
tasks = {}


# ==================== 后台任务函数 ====================
def run_translation_task(url, context_size, knowledge_files, task_id):
    """后台运行翻译任务"""
    try:
        tasks[task_id]['status'] = 'running'
        tasks[task_id]['progress'] = '正在下载字幕...'

        # 保存上传的知识库文件到临时目录
        kb_paths = []
        if knowledge_files:
            kb_dir = os.path.join(app.config['UPLOAD_FOLDER'], task_id)
            os.makedirs(kb_dir, exist_ok=True)
            for file in knowledge_files:
                # 注意：file 是 Werkzeug FileStorage 对象
                filename = secure_filename(file.filename)
                save_path = os.path.join(kb_dir, filename)
                file.save(save_path)
                kb_paths.append(save_path)

        # 初始化翻译流水线（需已修改支持 context_size 和 knowledge_files）
        pipeline = TranslationPipeline(
            model_path=TRANSLATION_MODEL_PATH,
            context_size=context_size,
            knowledge_files=kb_paths if kb_paths else None
        )

        # 运行翻译，获取结果字典
        result = pipeline.run(url)

        # 将文件路径转换为下载链接（相对路径或文件名）
        if result:
            # 假设返回的路径是绝对路径，我们需要提取文件名用于 url_for
            bilingual_file = os.path.basename(result.get('bilingual', ''))
            chinese_file = os.path.basename(result.get('chinese', ''))
            video_file = os.path.basename(result.get('video', ''))

            tasks[task_id]['result'] = {
                'bilingual': url_for('download', filename=bilingual_file, _external=True),
                'chinese': url_for('download', filename=chinese_file, _external=True),
                'video': url_for('video', filename=video_file, _external=True) if video_file else None
            }
        tasks[task_id]['status'] = 'completed'
        tasks[task_id]['progress'] = '完成'
    except Exception as e:
        tasks[task_id]['status'] = 'failed'
        tasks[task_id]['error'] = str(e)
        tasks[task_id]['progress'] = '错误'
    finally:
        # 可选：清理临时知识库文件
        # 这里暂不自动清理，可添加定时任务
        pass


# ==================== Flask 路由 ====================
@app.route('/')
def index():
    return render_template('index.html')


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
        response['result'] = task.get('result', {})
    elif task['status'] == 'failed':
        response['error'] = task.get('error', '未知错误')

    return jsonify(response)


@app.route('/download/<filename>')
def download(filename):
    """提供字幕文件下载"""
    # 防止路径遍历
    safe_filename = os.path.basename(filename)
    file_path = os.path.join(SUBTITLE_DIR, safe_filename)
    if not os.path.exists(file_path):
        abort(404)
    return send_file(file_path, as_attachment=True)


@app.route('/video/<filename>')
def video(filename):
    """提供视频文件流（用于播放）"""
    safe_filename = os.path.basename(filename)
    file_path = os.path.join(VIDEO_DIR, safe_filename)
    if not os.path.exists(file_path):
        abort(404)
    return send_file(file_path, mimetype='video/mp4')


if __name__ == '__main__':
    # 确保上传目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
