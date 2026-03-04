import os
import torch
import re
from dataclasses import dataclass
from typing import List
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer


# ===============================
# 字幕数据结构
# ===============================
@dataclass
class Subtitle:
    idx: int
    start: str
    end: str
    text: str


# ===============================
# 翻译器
# ===============================
class LLMTranslator:

    def __init__(self,model_path="model/HY-MT1.5-1.8B",context_size=3):
        print("加载 HY-MT 模型中...")

        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(model_path,torch_dtype=torch.float16).cuda()
        self.model.eval()
        self.context_size = context_size
        print("模型加载完成")

    # ===============================
    # 构造强结构Prompt
    # ===============================
    def build_prompt(self, context_texts: List[str], text: str):

        background = ""
        if context_texts:
            background = "BACKGROUND (DO NOT TRANSLATE):\n"
            for t in context_texts:
                background += f"- {t}\n"
            background += "\n"

        prompt = (
            background +
            "TASK:\n"
            "Translate ONLY the quoted sentence into Chinese.\n\n"
            "STRICT RULES:\n"
            "1. Do NOT repeat the background.\n"
            "2. Do NOT summarize.\n"
            "3. Do NOT add extra content.\n"
            "4. Only translate the quoted sentence.\n"
            "5. Output Chinese only.\n\n"
            f'SENTENCE:\n"{text}"\n'
        )

        return prompt

    # ===============================
    # 单句翻译
    # ===============================
    def translate(self, context_texts: List[str], text: str):

        prompt = self.build_prompt(context_texts, text)

        messages = [{"role": "user", "content": prompt}]

        inputs = self.tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt"
        ).cuda()

        with torch.no_grad():
            outputs = self.model.generate(
                inputs,
                max_new_tokens=100,   # 强限制
                do_sample=False,
                temperature=0.0
            )

        generated = outputs[0][inputs.shape[-1]:]
        result = self.tokenizer.decode(
            generated,
            skip_special_tokens=True
        ).strip()

        result = self.clean_output(result)

        return result

    # ===============================
    # 输出清洗
    # ===============================
    def clean_output(self, text):

        # 删除可能的引号
        text = text.strip('"').strip()

        # 删除多余英文
        text = re.sub(r'[A-Za-z]{8,}', '', text)

        # 防止重复句
        sentences = re.split(r'[。！？]', text)
        if len(sentences) >= 2 and sentences[0] == sentences[1]:
            text = sentences[0] + "。"

        return text.strip()


# ===============================
# SRT 处理器
# ===============================
class SRTTranslator:

    def __init__(self, translator):
        self.translator = translator

    @staticmethod
    def parse_srt(path):

        subs = []

        with open(path, "r", encoding="utf-8") as f:
            block = []

            for line in f:
                line = line.rstrip("\n")

                if not line.strip():
                    if len(block) >= 3:
                        idx = int(block[0])
                        start, end = block[1].split(" --> ")
                        text = " ".join(block[2:])
                        subs.append(Subtitle(idx, start, end, text))
                    block = []
                else:
                    block.append(line)

        return subs

    @staticmethod
    def save_srt(subs, path):

        with open(path, "w", encoding="utf-8") as f:
            for s in subs:
                f.write(f"{s.idx}\n")
                f.write(f"{s.start} --> {s.end}\n")
                f.write(s.text + "\n\n")

    def translate(self, input_srt):

        subs = self.parse_srt(input_srt)

        bilingual = []
        chinese = []

        total = len(subs)

        print(f"开始翻译 {total} 条字幕...\n")

        for i in tqdm(range(total)):

            current_sub = subs[i]

            context_start = max(0, i - self.translator.context_size)
            context_texts = [
                subs[j].text for j in range(context_start, i)
            ]

            zh = self.translator.translate(
                context_texts,
                current_sub.text
            )

            bilingual.append(
                Subtitle(
                    current_sub.idx,
                    current_sub.start,
                    current_sub.end,
                    current_sub.text + "\n" + zh
                )
            )

            chinese.append(
                Subtitle(
                    current_sub.idx,
                    current_sub.start,
                    current_sub.end,
                    zh
                )
            )

        base, ext = os.path.splitext(input_srt)

        self.save_srt(bilingual, base + "_bilingual" + ext)
        self.save_srt(chinese, base + "_zh" + ext)

        print("\n翻译完成!")


if __name__ == "__main__":

    translator = LLMTranslator(model_path="model/HY-MT1.5-7B",context_size=3)
    processor = SRTTranslator(translator)
    processor.translate("./subtitle/Building a better Star Wars AT-AT toy.en_processed.srt")