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

        print("下载字幕...")
        subtitle_file = self.downloader.download(url)

        print("清洗字幕...")
        subtitles = self.processor.process(subtitle_file)

        translated = []

        for s in subtitles:

            knowledge = self.rag.search(s.text)

            zh = self.translator.translate(
                text=s.text,
                knowledge=knowledge
            )

            translated.append((s, zh))

        print("写入字幕...")
        self.writer.write(translated)

        print("翻译完成")