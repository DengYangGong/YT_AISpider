from dataclasses import dataclass
from typing import List, Optional, Tuple
import os
import time
from deep_translator import GoogleTranslator


# =========================
# 数据结构
# =========================
@dataclass
class Subtitle:
    idx: int
    start: str
    end: str
    text: str


# =========================
# 中英字幕翻译器类
# =========================
class BilingualSRTTranslator:
    def __init__(self, source_lang: str = 'en', target_lang: str = 'zh-CN',
                 delay: float = 0.4, bilingual_suffix: str = "_bilingual",
                 chinese_suffix: str = "_zh"):
        """
        初始化中英字幕翻译器

        Args:
            source_lang: 源语言，默认为'en'
            target_lang: 目标语言，默认为'zh-CN'
            delay: 翻译请求之间的延迟（秒），防止被风控
            bilingual_suffix: 中英双语文件的后缀标识，默认为"_bilingual"
            chinese_suffix: 纯中文字幕文件的后缀标识，默认为"_zh"
        """
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.delay = delay
        self.bilingual_suffix = bilingual_suffix
        self.chinese_suffix = chinese_suffix

        # 初始化翻译器
        self.translator = GoogleTranslator(source=source_lang, target=target_lang)

    # =========================
    # 路径处理工具
    # =========================
    def _generate_output_paths(self, input_path: str) -> Tuple[str, str]:
        """
        根据输入路径自动生成两个输出路径

        Args:
            input_path: 输入文件路径

        Returns:
            (双语文件路径, 纯中文文件路径)
        """
        # 获取目录、文件名和扩展名
        dir_path = os.path.dirname(input_path)
        base_name = os.path.basename(input_path)

        # 分离文件名和扩展名
        name, ext = os.path.splitext(base_name)

        # 生成双语文件名
        bilingual_name = f"{name}{self.bilingual_suffix}{ext}"
        chinese_name = f"{name}{self.chinese_suffix}{ext}"

        # 组合成完整路径
        if dir_path:
            bilingual_path = os.path.join(dir_path, bilingual_name)
            chinese_path = os.path.join(dir_path, chinese_name)
        else:
            bilingual_path = bilingual_name
            chinese_path = chinese_name

        return bilingual_path, chinese_path

    # =========================
    # 解析 SRT
    # =========================
    @staticmethod
    def parse_srt(path: str) -> List[Subtitle]:
        """解析SRT文件"""
        subs = []
        with open(path, 'r', encoding='utf-8') as f:
            block = []
            for line in f:
                line = line.rstrip('\n')
                if not line.strip():
                    if len(block) >= 3:
                        idx = int(block[0])
                        start, end = block[1].split(' --> ')
                        text = ' '.join(block[2:])
                        subs.append(Subtitle(idx, start, end, text))
                    block = []
                else:
                    block.append(line)
        return subs

    # =========================
    # 翻译（带容错）
    # =========================
    def translate_safe(self, text: str) -> str:
        """
        安全翻译文本，遇到错误时返回原文

        Args:
            text: 要翻译的文本

        Returns:
            翻译后的文本（如果翻译失败则返回原文）
        """
        try:
            # 如果文本为空或只有空格，直接返回
            if not text.strip():
                return text

            # 使用Google翻译器翻译
            return self.translator.translate(text)
        except Exception as e:
            # 翻译失败时输出错误信息并返回原文
            print(f"翻译失败: {e}")
            print(f"\t原文: {text[:50]}...")  # 只显示前50个字符
            return text

    # =========================
    # 生成两种字幕
    # =========================
    def translate_subs(self, subs: List[Subtitle]) -> Tuple[List[Subtitle], List[Subtitle]]:
        """
        翻译字幕并生成两种版本

        Args:
            subs: 英文字幕列表

        Returns:
            (中英双语字幕列表, 纯中文字幕列表)
        """
        bilingual_subs = []
        chinese_subs = []
        total = len(subs)

        print(f"开始翻译 {total} 条字幕...")

        for i, s in enumerate(subs, 1):
            # 显示进度
            if i % 10 == 0 or i == total:
                print(f"\t进度: {i}/{total}")

            # 翻译英文文本
            zh_text = self.translate_safe(s.text)

            # 1. 创建中英双语字幕（英文在上，中文在下）
            bilingual_text = f"{s.text}\n{zh_text}"
            bilingual_subs.append(
                Subtitle(s.idx, s.start, s.end, bilingual_text)
            )

            # 2. 创建纯中文字幕
            chinese_subs.append(
                Subtitle(s.idx, s.start, s.end, zh_text)
            )

            # 延迟防止被风控
            if i < total:  # 最后一条不需要延迟
                time.sleep(self.delay)

        print("翻译完成！")
        return bilingual_subs, chinese_subs

    # =========================
    # 保存 SRT
    # =========================
    @staticmethod
    def save_srt(subs: List[Subtitle], path: str):
        """保存字幕到SRT文件"""
        with open(path, 'w', encoding='utf-8') as f:
            for s in subs:
                f.write(f"{s.idx}\n")
                f.write(f"{s.start} --> {s.end}\n")
                f.write(s.text + "\n\n")

    # =========================
    # 主流程
    # =========================
    def process(self, input_srt: str,
                bilingual_output: Optional[str] = None,
                chinese_output: Optional[str] = None):
        """
        处理SRT文件的主流程：解析 -> 翻译 -> 保存两份文件

        Args:
            input_srt: 输入SRT文件路径
            bilingual_output: 中英双语输出文件路径（可选）
            chinese_output: 纯中文输出文件路径（可选）
        """
        # 检查输入文件是否存在
        if not os.path.exists(input_srt):
            print(f"错误：输入文件不存在 - {input_srt}")
            return

        # 如果未指定输出路径，则自动生成
        if bilingual_output is None or chinese_output is None:
            auto_bilingual, auto_chinese = self._generate_output_paths(input_srt)

            if bilingual_output is None:
                bilingual_output = auto_bilingual

            if chinese_output is None:
                chinese_output = auto_chinese

        print(f"输入文件: {input_srt}")
        print("-" * 50)

        # 解析原始SRT
        subs = self.parse_srt(input_srt)
        print(f"解析到 {len(subs)} 条字幕")

        # 翻译并生成两种字幕
        bilingual_subs, chinese_subs = self.translate_subs(subs)

        # 保存处理后的SRT文件
        self.save_srt(bilingual_subs, bilingual_output)
        self.save_srt(chinese_subs, chinese_output)

        print(f"中英双语字幕生成完成：{bilingual_output}")
        print(f"纯中文字幕生成完成：{chinese_output}")
        print("-" * 50)

        # 显示统计信息
        print(f"统计信息:")
        print(f"  - 总字幕数: {len(bilingual_subs)}")
        print(f"  - 源语言: {self.source_lang}")
        print(f"  - 目标语言: {self.target_lang}")
        print(f"  - 翻译延迟: {self.delay}秒")

    # =========================
    # 批量处理
    # =========================
    def process_batch(self, input_paths: List[str]):
        """
        批量处理多个SRT文件

        Args:
            input_paths: 输入SRT文件路径列表
        """
        print(f"开始批量处理 {len(input_paths)} 个文件...")
        print("=" * 60)

        for i, input_path in enumerate(input_paths, 1):
            print(f"处理文件 {i}/{len(input_paths)}: {input_path}")
            print("-" * 40)

            # 检查文件是否存在
            if not os.path.exists(input_path):
                print(f"文件不存在，跳过: {input_path}")
                print()
                continue

            # 处理单个文件
            self.process(input_path)
            print()


# =========================
# 使用示例
# =========================
if __name__ == '__main__':
    translator = BilingualSRTTranslator()
    translator.process('./subtitle/Building a Walking Machine I can RIDE ON!.en_processed.srt')

