import os
import gradio as gr

from subtitle_processor import SRTProcessor
from subtitle_translator import subtitle_translator
from video_downloader import YT_Downloader


# ============================
# 初始化模型
# ============================

translator = subtitle_translator.LLMTranslator(
    target_language="中文",
    context_size=0,
    max_new_tokens=200,
    do_sample=True,
    temperature=0.7,
    top_p=0.6,
    top_k=20,
    repetition_penalty=1.05,
)

srt_translator = subtitle_translator.SRTTranslator(translator)


# ============================
# 翻译流程
# ============================

def process_video(url, context_size, progress=gr.Progress()):

    if not url:
        return "请输入视频网址", None, None, ""

    try:

        # 更新上下文参数
        translator.context_size = int(context_size)

        progress(0.1, desc="下载字幕中...")

        ytv_downloader = YT_Downloader()
        subtitle_path = ytv_downloader.download(url)

        if not subtitle_path:
            return "字幕下载失败", None, None, ""

        progress(0.3, desc="字幕预处理中...")

        srt_processor = SRTProcessor()
        subtitle_proc_path = srt_processor.process(subtitle_path)

        progress(0.5, desc="开始翻译字幕...")

        srt_translator.translate_file(subtitle_proc_path)

        base, ext = os.path.splitext(subtitle_proc_path)

        zh_file = base + "_zh" + ext
        bilingual_file = base + "_bilingual" + ext

        progress(0.9, desc="读取字幕文件...")

        # 读取双语字幕内容用于显示
        bilingual_text = ""
        if os.path.exists(bilingual_file):
            with open(bilingual_file, "r", encoding="utf-8") as f:
                bilingual_text = f.read()

        progress(1.0, desc="翻译完成")

        return "翻译完成", zh_file, bilingual_file, bilingual_text

    except Exception as e:
        return f"发生错误: {str(e)}", None, None, ""


# ============================
# WebUI
# ============================

with gr.Blocks(title="AI 字幕翻译工具") as demo:

    gr.Markdown("# 🎬 AI 视频字幕翻译工具")

    gr.Markdown(
        """
输入 YouTube 视频链接，系统将自动：

1️⃣ 下载字幕  
2️⃣ 清洗字幕  
3️⃣ 使用本地 AI 翻译  
4️⃣ 生成字幕文件
"""
    )

    with gr.Row():

        url_input = gr.Textbox(
            label="YouTube 视频网址",
            placeholder="https://youtube.com/..."
        )

        context_size = gr.Slider(
            minimum=0,
            maximum=5,
            value=0,
            step=1,
            label="上下文关联句子数 (0 = 不使用上下文)"
        )

    run_btn = gr.Button("开始翻译")

    status = gr.Textbox(label="状态")

    with gr.Row():

        zh_file = gr.File(label="下载中文字幕")

        bilingual_file = gr.File(label="下载双语字幕")

    gr.Markdown("## 📄 双语字幕预览")

    subtitle_preview = gr.Textbox(
        lines=20,
        label="字幕内容",
    )

    run_btn.click(
        process_video,
        inputs=[url_input, context_size],
        outputs=[status, zh_file, bilingual_file, subtitle_preview]
    )


demo.launch(server_port=7860)