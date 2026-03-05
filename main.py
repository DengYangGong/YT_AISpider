from subtitle_processor import SRTProcessor
from subtitle_translator import LLMTranslator,SRTTranslator
from video_downloader import YT_Downloader

if __name__ == '__main__':

    url = input("视频网址：")

    ytv_downloader = YT_Downloader()
    subtitle_path = ytv_downloader.download(url)

    srt_processor = SRTProcessor()
    subtitle_proc_path = srt_processor.process(subtitle_path)

    # 创建翻译器
    translator = LLMTranslator(
        target_language="中文",
        max_new_tokens=200,
        do_sample=True,
        temperature=0.7,
        top_p=0.6,
        top_k=20,
        repetition_penalty=1.05,
    )

    # 询问是否添加新规则
    print("\n是否要向修正表添加新的错误修正规则？(y/n)")
    choice = input().strip().lower()
    if choice == 'y':
        translator.add_fix_interactively()


    srt_translator = SRTTranslator(translator)
    srt_translator.translate_file(subtitle_proc_path)
