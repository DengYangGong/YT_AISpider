import os
import re
from dataclasses import dataclass
from typing import List, Optional


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
# SRT处理器类
# =========================
class SRTProcessor:
    def __init__(self, max_words: int = 23, processed_suffix: str = "_processed"):
        """
        初始化SRT处理器

        Args:
            max_words: 每条字幕最大英文词数，默认为23
            processed_suffix: 处理后文件的后缀标识，默认为"_processed"
        """
        self.max_words = max_words
        self.processed_suffix = processed_suffix

    # =========================
    # 时间工具（静态方法）
    # =========================
    @staticmethod
    def time_to_ms(t: str) -> int:
        """将时间字符串转换为毫秒"""
        h, m, rest = t.split(':')
        s, ms = rest.split(',')
        return (
                int(h) * 3600000
                + int(m) * 60000
                + int(s) * 1000
                + int(ms)
        )

    @staticmethod
    def ms_to_time(ms: int) -> str:
        """将毫秒转换为时间字符串"""
        h = ms // 3600000
        ms %= 3600000
        m = ms // 60000
        ms %= 60000
        s = ms // 1000
        ms %= 1000
        return f"{h:02}:{m:02}:{s:02},{ms:03}"

    # =========================
    # 路径处理工具
    # =========================
    def _generate_output_path(self, input_path: str, suffix: str = None, extension: str = None) -> str:
        """
        根据输入路径自动生成输出路径

        Args:
            input_path: 输入文件路径
            suffix: 自定义后缀（如果为None则使用self.processed_suffix）
            extension: 自定义扩展名（如果为None则使用原扩展名）

        Returns:
            自动生成的输出文件路径
        """
        # 获取目录、文件名和扩展名
        dir_path = os.path.dirname(input_path)
        base_name = os.path.basename(input_path)

        # 分离文件名和扩展名
        name, original_ext = os.path.splitext(base_name)

        # 使用指定的后缀或默认后缀
        processed_suffix = suffix if suffix is not None else self.processed_suffix

        # 使用指定的扩展名或原扩展名
        final_extension = extension if extension is not None else original_ext

        # 生成新的文件名（添加处理标识）
        new_name = f"{name}{processed_suffix}{final_extension}"

        # 组合成完整路径
        if dir_path:
            return os.path.join(dir_path, new_name)
        else:
            return new_name

    # =========================
    # 解析 SRT
    # =========================
    def parse_srt(self, path: str) -> List[Subtitle]:
        """解析SRT文件"""
        subs = []
        with open(path, 'r', encoding='utf-8') as f:
            block = []

            for line in f:
                line = line.strip()
                if not line:
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
    # 合并重叠 ASR 字幕
    # =========================
    def merge_overlapping(self, subs: List[Subtitle]) -> List[Subtitle]:
        """合并时间重叠的字幕"""
        if not subs:
            return []

        merged = []
        cur = subs[0]

        for nxt in subs[1:]:
            if self.time_to_ms(nxt.start) <= self.time_to_ms(cur.end):
                # 合并文本 & 扩展时间
                cur.text += ' ' + nxt.text
                if self.time_to_ms(nxt.end) > self.time_to_ms(cur.end):
                    cur.end = nxt.end
            else:
                merged.append(cur)
                cur = nxt

        merged.append(cur)
        return merged

    # =========================
    # 文本切割（字幕级）
    # =========================
    def split_text(self, text: str) -> List[str]:
        """将长文本切割为适合字幕显示的片段"""
        # 1 先按强句界符切
        parts = re.split(r'(?<=[.!?])\s+', text)

        results = []

        for part in parts:
            words = part.split()

            # 2 过长 → 按弱连接词切（避免 that's 被切）
            if len(words) > self.max_words:
                chunks = re.split(
                    r'\b(and|which|because|so|that)\b(?!\')',
                    part
                )
                buf = ''
                for c in chunks:
                    if len((buf + ' ' + c).split()) > self.max_words:
                        if buf.strip():
                            results.append(buf.strip())
                        buf = c
                    else:
                        buf += ' ' + c
                if buf.strip():
                    results.append(buf.strip())
            else:
                results.append(part.strip())

        # 3 合并过短残句（≤3 词）
        merged = []
        for r in results:
            if merged and len(r.split()) <= 3:
                merged[-1] += ' ' + r
            else:
                merged.append(r)

        # 4 最终兜底：按词数硬切（理论上几乎不会触发）
        final = []
        for r in merged:
            words = r.split()
            while len(words) > self.max_words:
                final.append(' '.join(words[:self.max_words]))
                words = words[self.max_words:]
            if words:
                final.append(' '.join(words))

        return final

    # =========================
    # 在原时间段内分配时间（不重叠）
    # =========================
    def split_time(self, sub: Subtitle, texts: List[str]) -> List[Subtitle]:
        """在原始时间范围内为分割后的文本分配时间"""
        start_ms = self.time_to_ms(sub.start)
        end_ms = self.time_to_ms(sub.end)
        total_ms = end_ms - start_ms

        lengths = [len(t) for t in texts]
        total_len = sum(lengths)

        result = []
        cursor = start_ms

        for i, (t, l) in enumerate(zip(texts, lengths)):
            if i == len(texts) - 1:
                nxt = end_ms
            else:
                dur = int(total_ms * l / total_len)
                nxt = cursor + max(dur, 300)  # 最少 300ms，避免闪字幕

            result.append(
                Subtitle(0, self.ms_to_time(cursor), self.ms_to_time(nxt), t)
            )
            cursor = nxt

        return result

    # =========================
    # 保存 SRT
    # =========================
    @staticmethod
    def save_srt(subs: List[Subtitle], path: str):
        """保存字幕到SRT文件"""
        with open(path, 'w', encoding='utf-8') as f:
            for i, s in enumerate(subs, 1):
                f.write(f"{i}\n")
                f.write(f"{s.start} --> {s.end}\n")
                f.write(s.text + "\n\n")

    # =========================
    # 提取完整句子
    # =========================
    def extract_full_sentences(self, subs: List[Subtitle]) -> List[str]:
        """
        从字幕中提取完整的句子（以标点结尾）

        Args:
            subs: 字幕列表

        Returns:
            完整句子列表
        """
        # 将所有文本合并成一个字符串
        full_text = ' '.join([s.text for s in subs])

        # 使用正则表达式分割句子
        # 匹配以 . ! ? 结尾，后面可能有空格的情况
        sentences = re.split(r'(?<=[.!?])\s+', full_text)

        # 过滤空字符串，并确保每个句子以标点结尾
        filtered_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                # 如果句子不以标点结尾，补上句号
                if sentence and sentence[-1] not in '.!?':
                    sentence += '.'
                filtered_sentences.append(sentence)

        return filtered_sentences

    # =========================
    # 保存纯文本文件（一句一行）
    # =========================
    @staticmethod
    def save_as_text(sentences: List[str], path: str):
        """
        将完整句子保存为纯文本文件，一句一行

        Args:
            sentences: 完整句子列表
            path: 文本文件保存路径
        """
        with open(path, 'w', encoding='utf-8') as f:
            for sentence in sentences:
                # 只写入完整句子，每句一行
                f.write(sentence + "\n")

    # =========================
    # 主流程
    # =========================
    def process(self, input_srt: str, output_srt: Optional[str] = None, save_txt: bool = True):
        """
        处理SRT文件的主流程

        Args:
            input_srt: 输入SRT文件路径
            output_srt: 输出SRT文件路径（可选，如果为None则自动生成）
            save_txt: 是否同时保存为纯文本文件，默认为True
        """
        # 如果未指定输出路径，则自动生成
        if output_srt is None:
            output_srt = self._generate_output_path(input_srt)

        print(f"输入字幕文件: {input_srt}")
        print(f"输出字幕文件: {output_srt}")

        # 解析原始SRT
        subs = self.parse_srt(input_srt)

        # 合并 ASR 碎时间轴
        merged = self.merge_overlapping(subs)

        new_subs = []
        idx = 1

        for sub in merged:
            # 在干净时间块中切句
            pieces = self.split_text(sub.text)

            # 在该时间块内重新分配时间
            timed = self.split_time(sub, pieces)

            for t in timed:
                t.idx = idx
                new_subs.append(t)
                idx += 1

        # 保存处理后的SRT
        self.save_srt(new_subs, output_srt)
        print(f"SRT文件处理完成！共生成 {len(new_subs)} 条字幕")

        # 保存为纯文本文件（如果需要）
        if save_txt:
            # 使用通用函数生成文本文件路径
            txt_path = self._generate_output_path(
                input_path=input_srt,
                suffix=self.processed_suffix + "_text",  # 添加_text后缀
                extension=".txt"  # 使用.txt扩展名
            )

            # 从最终的字幕中提取完整句子
            full_sentences = self.extract_full_sentences(new_subs)

            # 保存完整句子到文本文件
            self.save_as_text(full_sentences, txt_path)

            print(f"文本文件生成完成：{txt_path}")
            print(f"  - 共 {len(full_sentences)} 个完整句子")

        print("-" * 50)

        return output_srt


# =========================
# 使用示例
# =========================
if __name__ == '__main__':
    # 使用默认参数
    processor = SRTProcessor(max_words=23, processed_suffix="_processed")

    # 只传入输入路径，输出路径会自动生成
    processor.process('./subtitle/Building a Walking Machine I can RIDE ON!.en.srt')

    # # 示例2：不生成文本文件
    # print("\n" + "=" * 50)
    # print("示例2：仅生成SRT文件，不生成文本文件")
    # print("=" * 50)
    # processor2 = SRTProcessor(processed_suffix="_clean")
    # processor2.process(
    #     './subtitle/Building a Walking Machine I can RIDE ON!.en.srt',
    #     save_txt=False  # 不生成文本文件
    # )
    #
    # # 示例3：手动指定输出路径
    # print("\n" + "=" * 50)
    # print("示例3：手动指定输出路径")
    # print("=" * 50)
    # processor3 = SRTProcessor(max_words=20)
    # processor3.process(
    #     input_srt='./subtitle/Building a Walking Machine I can RIDE ON!.en.srt',
    #     output_srt='./subtitle/manual_output.srt',  # 手动指定输出路径
    #     save_txt=True  # 仍然生成文本文件
    # )
    #
    # # 示例4：查看生成的文本文件内容
    # print("\n" + "=" * 50)
    # print("示例4：查看文本文件内容")
    # print("=" * 50)
    # processor4 = SRTProcessor(max_words=20)
    # processor4.process(
    #     input_srt='./subtitle/Building a Walking Machine I can RIDE ON!.en.srt',
    #     output_srt='./subtitle/example_output.srt',
    #     save_txt=True
    # )
    #
    # # 读取并显示生成的文本文件前5行
    # txt_path = processor4._generate_output_path(
    #     './subtitle/Building a Walking Machine I can RIDE ON!.en.srt',
    #     suffix='_processed_text',
    #     extension='.txt'
    # )
    #
    # if os.path.exists(txt_path):
    #     print(f"\n文本文件前5行内容：")
    #     with open(txt_path, 'r', encoding='utf-8') as f:
    #         for i, line in enumerate(f, 1):
    #             print(f"{i}: {line.strip()}")
    #             if i >= 5:
    #                 break
    #
    # # 示例5：使用 _generate_output_path 函数的灵活性
    # print("\n" + "=" * 50)
    # print("示例5：使用通用路径生成函数")
    # print("=" * 50)
    #
    # # 生成不同类型的输出路径
    # test_path = './subtitle/video.en.srt'
    #
    # # 1. 默认SRT输出
    # srt_output = processor._generate_output_path(test_path)
    # print(f"SRT输出路径: {srt_output}")
    #
    # # 2. 文本文件输出
    # txt_output = processor._generate_output_path(test_path, suffix='_processed_text', extension='.txt')
    # print(f"文本输出路径: {txt_output}")
    #
    # # 3. 自定义后缀和扩展名
    # custom_output = processor._generate_output_path(test_path, suffix='_custom', extension='.ass')
    # print(f"自定义输出路径: {custom_output}")
    #
    # # 4. 只改变后缀
    # suffix_only = processor._generate_output_path(test_path, suffix='_sentence')
    # print(f"只改后缀: {suffix_only}")
    #
    # # 5. 只改变扩展名
    # ext_only = processor._generate_output_path(test_path, extension='.vtt')
    # print(f"只改扩展名: {ext_only}")
