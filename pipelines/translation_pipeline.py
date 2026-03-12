import os

from core.agent import AISpiderAgent
from tools.subtitle_processor import SubtitleProcessor
from tools.subtitle_writer import SubtitleWriter
from tools.youtube_downloader import YouTubeDownloader


class TranslationPipeline:
    def __init__(self, model_path, context_size=3, knowledge_files=None):
        self.downloader = YouTubeDownloader()
        self.processor = SubtitleProcessor()
        self.writer = SubtitleWriter()
        self.model_path = model_path
        self.context_size = context_size
        self.knowledge_files = knowledge_files  # 保存，供 run 中使用

    def run(self, url):
        # 1 下载字幕和视频
        print("\n\n下载视频和字幕...")
        download_result = self.downloader.download(url)

        if not download_result:
            print("下载失败")
            return None

        subtitle_file = download_result['subtitle']
        video_file = download_result['video']

        # 2 清洗字幕
        print("\n\n清洗字幕...")
        subtitles = self.processor.process(subtitle_file)

        # 创建 Agent，传入上下文大小和知识文件列表（如果有）
        agent = AISpiderAgent(
            self.model_path,
            context_size=self.context_size,
            knowledge_files=self.knowledge_files,
            rebuild_lm=False,  # 可根据需要改为参数传递
            rebuild_rag=True  # 每次使用自定义知识库时建议重建
        )

        translated = []

        # 3 逐句翻译
        print("\n\n翻译字幕...")
        for s in subtitles:
            zh = agent.translate_sentence(s.text)
            translated.append(zh)

        # 4 输出路径
        base, ext = os.path.splitext(subtitle_file)
        bilingual_path = base + "_bilingual" + ext
        chinese_path = base + "_zh" + ext

        # 5 写入字幕
        print("\n\n写入字幕...")
        self.writer.write_bilingual(subtitles, translated, bilingual_path)
        self.writer.write_chinese(subtitles, translated, chinese_path)

        print("翻译完成")
        print("双语字幕:", bilingual_path)
        print("中文字幕:", chinese_path)
        print("视频文件:", video_file)

        # 返回结果字典
        return {
            'bilingual': bilingual_path,
            'chinese': chinese_path,
            'video': video_file
        }
