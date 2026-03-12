import os

from config.settings import KNOWLEDGE_FILES
from core.agent import AISpiderAgent
from tools.subtitle_processor import SubtitleProcessor
from tools.subtitle_writer import SubtitleWriter
from tools.youtube_downloader import YouTubeDownloader


class TranslationPipeline:

    def __init__(self, model_path):

        self.downloader = YouTubeDownloader()
        self.processor = SubtitleProcessor()
        self.writer = SubtitleWriter()
        self.model_path = model_path  # 保存模型路径以便每次新建 Agent

    def run(self, url):

        # 1 下载字幕
        print("下载视频和字幕...")
        subtitle_file = self.downloader.download(url)

        if not subtitle_file:
            print("字幕下载失败")
            return

        # 2 清洗字幕
        print("清洗字幕...")
        subtitles = self.processor.process(subtitle_file)
        # 使用 Agent 整合翻译、上下文和知识检索

        agent = AISpiderAgent(self.model_path, KNOWLEDGE_FILES)

        translated = []

        # 3 使用 Agent 逐句翻译（自动管理上下文和知识检索）
        print("翻译字幕...")

        for s in subtitles:
            zh = agent.translate_sentence(s.text)
            translated.append(zh)

        # 4 输出路径
        base, ext = os.path.splitext(subtitle_file)

        bilingual_path = base + "_bilingual" + ext
        chinese_path = base + "_zh" + ext

        # 5 写入字幕
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
