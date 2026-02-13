from subtitle_processor import SRTProcessor
from subtitle_translator import BilingualSRTTranslator
from video_downloader import YT_Downloader

if __name__ == '__main__':

    url = input("视频网址：")

    ytv_downloader = YT_Downloader()
    subtitle_path = ytv_downloader.download(url)

    srt_processor = SRTProcessor()
    subtitle_proc_path = srt_processor.process(subtitle_path)

    srt_translator = BilingualSRTTranslator()
    srt_translator.process(subtitle_proc_path)
