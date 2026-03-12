import os
import re
from dataclasses import dataclass
from typing import List

from config.settings import SUBTITLE_DIR


@dataclass
class Subtitle:
    idx: int
    start: str
    end: str
    text: str


class SubtitleProcessor:
    """
    字幕预处理模块
    """

    def __init__(self, max_words: int = 23, processed_suffix: str = "_processed"):

        self.max_words = max_words
        self.processed_suffix = processed_suffix

        os.makedirs(SUBTITLE_DIR, exist_ok=True)

    # =========================
    # 时间转换
    # =========================

    @staticmethod
    def time_to_ms(t: str) -> int:

        h, m, rest = t.split(":")
        s, ms = rest.split(",")

        return (
                int(h) * 3600000 +
                int(m) * 60000 +
                int(s) * 1000 +
                int(ms)
        )

    @staticmethod
    def ms_to_time(ms: int) -> str:

        h = ms // 3600000
        ms %= 3600000

        m = ms // 60000
        ms %= 60000

        s = ms // 1000
        ms %= 1000

        return f"{h:02}:{m:02}:{s:02},{ms:03}"

    # =========================
    # SRT解析
    # =========================

    def parse_srt(self, path: str) -> List[Subtitle]:

        subs = []

        with open(path, "r", encoding="utf-8") as f:

            block = []

            for line in f:

                line = line.strip()

                if not line:

                    if len(block) >= 3:
                        idx = int(block[0])
                        start, end = block[1].split(" --> ")
                        text = " ".join(block[2:])

                        subs.append(Subtitle(idx, start, end, text))

                    block = []

                else:

                    block.append(line)

        return subs

    # =========================
    # 合并重叠字幕
    # =========================

    def merge_overlapping(self, subs: List[Subtitle]) -> List[Subtitle]:

        if not subs:
            return []

        merged = []
        cur = subs[0]

        for nxt in subs[1:]:

            if self.time_to_ms(nxt.start) <= self.time_to_ms(cur.end):

                cur.text += " " + nxt.text

                if self.time_to_ms(nxt.end) > self.time_to_ms(cur.end):
                    cur.end = nxt.end

            else:

                merged.append(cur)
                cur = nxt

        merged.append(cur)

        return merged

    # =========================
    # 文本切割
    # =========================

    def split_text(self, text: str) -> List[str]:

        parts = re.split(r'(?<=[.!?])\s+', text)

        results = []

        for part in parts:

            words = part.split()

            if len(words) > self.max_words:

                chunks = re.split(
                    r'\b(and|which|because|so|that)\b(?!\')',
                    part
                )

                buf = ""

                for c in chunks:

                    if len((buf + " " + c).split()) > self.max_words:

                        if buf.strip():
                            results.append(buf.strip())

                        buf = c

                    else:

                        buf += " " + c

                if buf.strip():
                    results.append(buf.strip())

            else:

                results.append(part.strip())

        return results

    # =========================
    # 时间分配
    # =========================

    def split_time(self, sub: Subtitle, texts: List[str]) -> List[Subtitle]:

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
                nxt = cursor + max(dur, 300)

            result.append(
                Subtitle(0, self.ms_to_time(cursor), self.ms_to_time(nxt), t)
            )

            cursor = nxt

        return result

    # =========================
    # 保存SRT
    # =========================

    @staticmethod
    def save_srt(subs: List[Subtitle], path: str):

        with open(path, "w", encoding="utf-8") as f:
            for i, s in enumerate(subs, 1):
                f.write(f"{i}\n")
                f.write(f"{s.start} --> {s.end}\n")
                f.write(s.text + "\n\n")

    # =========================
    # 主处理流程
    # =========================

    def process(self, input_srt: str) -> List[Subtitle]:

        print("解析字幕...")

        subs = self.parse_srt(input_srt)

        print("合并ASR碎片...")

        merged = self.merge_overlapping(subs)

        new_subs = []

        idx = 1

        for sub in merged:

            pieces = self.split_text(sub.text)

            timed = self.split_time(sub, pieces)

            for t in timed:
                t.idx = idx
                new_subs.append(t)

                idx += 1

        print(f"字幕处理完成，共 {len(new_subs)} 条")

        return new_subs
