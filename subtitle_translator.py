from dataclasses import dataclass
from typing import List, Tuple
import os
import torch
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer


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
# 本地 HY-MT 批量翻译器
# =========================
class LocalHYMTBatchTranslator:
    def __init__(
        self,
        model_path="model/HY-MT1.5-1.8B",
        batch_size=20
    ):
        print("正在加载 HY-MT 本地模型...")

        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16
        ).cuda()

        self.model.eval()
        self.batch_size = batch_size

        print("模型加载完成")

    def translate_batch(self, texts: List[str]) -> List[str]:
        """
        批量翻译
        """

        # 构造编号文本
        numbered_text = ""
        for i, t in enumerate(texts, 1):
            numbered_text += f"[{i}] {t}\n"

        messages = [
            {
                "role": "user",
                "content":
                    "Translate the following sentences into Chinese.\n"
                    "Keep the numbering format exactly the same.\n"
                    "Do NOT merge lines.\n\n"
                    f"{numbered_text}"
            }
        ]

        inputs = self.tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt"
        ).cuda()

        with torch.no_grad():
            outputs = self.model.generate(
                inputs,
                max_new_tokens=2048,
                do_sample=False,
                temperature=0.0
            )

        generated = outputs[0][inputs.shape[-1]:]
        result = self.tokenizer.decode(generated, skip_special_tokens=True)

        # 解析编号
        translated_texts = []

        for i in range(1, len(texts) + 1):
            tag = f"[{i}]"
            start = result.find(tag)

            if start == -1:
                # 如果没找到编号，用原文兜底
                translated_texts.append(texts[i - 1])
                continue

            start += len(tag)
            next_tag = f"[{i+1}]"
            end = result.find(next_tag, start)

            if end == -1:
                end = len(result)

            translated_texts.append(result[start:end].strip())

        return translated_texts


# =========================
# 字幕翻译主类
# =========================
class BilingualSRTTranslator:
    def __init__(
        self,
        model_path="model/HY-MT1.5-1.8B",
        batch_size=20
    ):
        self.translator = LocalHYMTBatchTranslator(
            model_path=model_path,
            batch_size=batch_size
        )

    # -------------------------
    # 解析 SRT
    # -------------------------
    @staticmethod
    def parse_srt(path: str) -> List[Subtitle]:
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

    # -------------------------
    # 保存 SRT
    # -------------------------
    @staticmethod
    def save_srt(subs: List[Subtitle], path: str):
        with open(path, 'w', encoding='utf-8') as f:
            for s in subs:
                f.write(f"{s.idx}\n")
                f.write(f"{s.start} --> {s.end}\n")
                f.write(s.text + "\n\n")

    # -------------------------
    # 批量翻译字幕
    # -------------------------
    def translate_subs(self, subs: List[Subtitle]) -> Tuple[List[Subtitle], List[Subtitle]]:

        bilingual_subs = []
        chinese_subs = []

        total = len(subs)
        batch_size = self.translator.batch_size

        print(f"开始批量翻译 {total} 条字幕...")

        for i in tqdm(range(0, total, batch_size)):
            batch = subs[i:i + batch_size]
            texts = [s.text for s in batch]

            translated_texts = self.translator.translate_batch(texts)

            # 防止翻译数量不一致
            if len(translated_texts) != len(batch):
                print("⚠ 翻译数量不匹配，使用原文补齐")
                translated_texts = translated_texts[:len(batch)]
                while len(translated_texts) < len(batch):
                    translated_texts.append(
                        batch[len(translated_texts)].text
                    )

            for s, zh_text in zip(batch, translated_texts):

                bilingual_text = f"{s.text}\n{zh_text}"

                bilingual_subs.append(
                    Subtitle(s.idx, s.start, s.end, bilingual_text)
                )

                chinese_subs.append(
                    Subtitle(s.idx, s.start, s.end, zh_text)
                )

        print("翻译完成！")
        return bilingual_subs, chinese_subs

    # -------------------------
    # 主流程
    # -------------------------
    def process(self, input_srt: str):

        if not os.path.exists(input_srt):
            print(f"文件不存在: {input_srt}")
            return

        base, ext = os.path.splitext(input_srt)
        bilingual_output = base + "_bilingual" + ext
        chinese_output = base + "_zh" + ext

        print(f"输入文件: {input_srt}")
        print("-" * 50)

        subs = self.parse_srt(input_srt)
        print(f"解析到 {len(subs)} 条字幕")

        bilingual_subs, chinese_subs = self.translate_subs(subs)

        self.save_srt(bilingual_subs, bilingual_output)
        self.save_srt(chinese_subs, chinese_output)

        print("-" * 50)
        print(f"中英双语字幕已生成: {bilingual_output}")
        print(f"纯中文字幕已生成: {chinese_output}")


# =========================
# 入口
# =========================
if __name__ == '__main__':

    translator = BilingualSRTTranslator(
        model_path="model/HY-MT1.5-1.8B",
        batch_size=20   # 4060 8G 推荐 15~25
    )

    translator.process(
        "./subtitle/Building a better Star Wars AT-AT toy.en_processed.srt"
    )