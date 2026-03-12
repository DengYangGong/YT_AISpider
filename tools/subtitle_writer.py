import os
from typing import List
from dataclasses import dataclass


@dataclass
class Subtitle:
    idx: int
    start: str
    end: str
    text: str


class SubtitleWriter:
    """
    字幕写入模块
    """

    @staticmethod
    def save_srt(subs: List[Subtitle], path: str):

        os.makedirs(os.path.dirname(path), exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:

            for s in subs:

                f.write(f"{s.idx}\n")
                f.write(f"{s.start} --> {s.end}\n")
                f.write(s.text + "\n\n")

    def write_bilingual(
        self,
        original_subs: List[Subtitle],
        translated: List[str],
        output_path: str
    ):

        bilingual = []

        for sub, zh in zip(original_subs, translated):

            bilingual.append(
                Subtitle(
                    sub.idx,
                    sub.start,
                    sub.end,
                    sub.text + "\n" + zh
                )
            )

        self.save_srt(bilingual, output_path)

    def write_chinese(
        self,
        original_subs: List[Subtitle],
        translated: List[str],
        output_path: str
    ):

        chinese = []

        for sub, zh in zip(original_subs, translated):

            chinese.append(
                Subtitle(
                    sub.idx,
                    sub.start,
                    sub.end,
                    zh
                )
            )

        self.save_srt(chinese, output_path)