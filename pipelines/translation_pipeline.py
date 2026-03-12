import os

from tools.youtube_downloader import YouTubeDownloader
from tools.subtitle_processor import SubtitleProcessor
from tools.subtitle_writer import SubtitleWriter

from core.reasoning.translator_chain import TranslatorChain
from rag.rag_engine import RAGEngine


class TranslationPipeline:

    def __init__(self, model_path):

        self.downloader = YouTubeDownloader()
        self.processor = SubtitleProcessor()
        self.writer = SubtitleWriter()

        self.rag = RAGEngine()
        self.translator = TranslatorChain(model_path)

    def run(self, url):

        # 1 下载字幕
        print("下载字幕...")
        subtitle_file = self.downloader.download(url)

        if not subtitle_file:
            print("字幕下载失败")
            return

        # 2 清洗字幕
        print("清洗字幕...")
        subtitles = self.processor.process(subtitle_file)

        translated = []

        # 3 翻译
        print("翻译字幕...")

        for s in subtitles:

            knowledge = self.rag.search(s.text)

            zh = self.translator.translate(
                text=s.text,
                knowledge=knowledge
            )

            translated.append(zh)

        # 4 输出路径
        base, ext = os.path.splitext(subtitle_file)

        bilingual_path = base + "_bilingual" + ext
        chinese_path = base + "_zh" + ext

        # 5 写字幕
        print("写入字幕...")

        self.writer.write_bilingual(
            subtitles,
            translated,
            bilingual_path
        )

        self.writer.write_chinese(
            subtitles,
            translated,
            chinese_path
        )

        print("翻译完成")
        print("双语字幕:", bilingual_path)
        print("中文字幕:", chinese_path)