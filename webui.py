import os
import gradio as gr

from subtitle_processor import SRTProcessor
from subtitle_translator import LLMTranslator, SRTTranslator
from video_downloader import YT_Downloader


# ============================
# 初始化模型（只加载一次）
# ============================

translator = LLMTranslator(
    target_language="中文",
    max_new_tokens=200,
    do_sample=True,
    temperature=0.7,
    top_p=0.6,
    top_k=20,
    repetition_penalty=1.05,
)

srt_translator = SRTTranslator(translator)


# ============================
# 添加翻译修正规则
# ============================

def add_fix(pattern, replacement):

    if not pattern or not replacement:
        return "请输入完整规则"

    translator.error_fixes[pattern] = replacement
    translator._save_fixes(translator.error_fixes)

    return f"规则已添加: {pattern} -> {replacement}"


# ============================
# 主翻译流程
# ============================

def process_video(url, progress=gr.Progress()):

    if not url:
        return "请输入视频网址", None

    progress(0.1, desc="下载字幕中...")

    ytv_downloader = YT_Downloader()
    subtitle_path = ytv_downloader.download(url)

    if not subtitle_path:
        return "字幕下载失败", None

    progress(0.3, desc="字幕预处理中...")

    srt_processor = SRTProcessor()
    subtitle_proc_path = srt_processor.process(subtitle_path)

    progress(0.5, desc="开始翻译...")

    srt_translator.translate_file(subtitle_proc_path)

    base, ext = os.path.splitext(subtitle_proc_path)

    zh_file = base + "_zh" + ext

    progress(1.0, desc="完成")

    return "翻译完成", zh_file


# ============================
# WebUI
# ============================

with gr.Blocks(title="AI 字幕翻译工具") as demo:

    gr.Markdown("# 🎬 AI 视频字幕翻译工具")

    with gr.Tab("视频翻译"):

        url_input = gr.Textbox(
            label="YouTube 视频网址",
            placeholder="https://youtube.com/..."
        )

        run_btn = gr.Button("开始翻译")

        status = gr.Textbox(label="状态")

        output_file = gr.File(label="下载翻译字幕")

        run_btn.click(
            process_video,
            inputs=url_input,
            outputs=[status, output_file]
        )

    with gr.Tab("翻译修正规则"):

        gr.Markdown("添加翻译修正规则 (正则表达式)")

        pattern = gr.Textbox(label="匹配规则 (regex)")
        replacement = gr.Textbox(label="替换内容")

        add_btn = gr.Button("添加规则")

        fix_status = gr.Textbox(label="状态")

        add_btn.click(
            add_fix,
            inputs=[pattern, replacement],
            outputs=fix_status
        )


demo.launch(server_port=7860)