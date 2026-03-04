from subtitle_processor import SRTProcessor
from subtitle_translator import LLMTranslator,SRTTranslator
from video_downloader import YT_Downloader

if __name__ == '__main__':

    url = input("视频网址：")

    ytv_downloader = YT_Downloader()
    subtitle_path = ytv_downloader.download(url)

    srt_processor = SRTProcessor()
    subtitle_proc_path = srt_processor.process(subtitle_path)

    ai_translator = LLMTranslator(model_path="model/HY-MT1.5-7B", context_size=3)
    srt_translator = SRTTranslator(ai_translator)
    srt_translator.translate(subtitle_proc_path)
