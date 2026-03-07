import os
import re
import time
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import List, Optional

import torch
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer

from .rag_engine import RAGEngine


# ===============================
# 字幕结构
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
    def __init__(
            self,
            model_path: str = "../models/HY-MT1.5-1.8B",
            context_size: int = 0,
            target_language: str = "中文",
            device: Optional[str] = None,
            max_new_tokens: int = 200,
            do_sample: bool = True,
            temperature: float = 0.7,
            top_p: float = 0.6,
            top_k: int = 20,
            repetition_penalty: float = 1.05
    ):
        print("加载 HY-MT 模型中...")
        self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")

        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True
        )
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        torch_dtype = torch.bfloat16 if self.device == "cuda" else torch.float32
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            dtype=torch_dtype,
            trust_remote_code=True,
            device_map="auto" if self.device == "cuda" else None
        )
        self.model.eval()

        self.context_size = context_size
        self.target_language = target_language
        self.max_new_tokens = max_new_tokens
        self.do_sample = do_sample
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.repetition_penalty = repetition_penalty

        # 存储上一句译文，用于重复检测
        self.last_translation = ""

        # 初始化 RAG
        print("加载 RAG 引擎...")
        self.rag = RAGEngine()
        print("RAG 初始化完成")

        print(f"模型加载完成，设备：{self.device}，上下文大小：{self.context_size}")

    def build_messages(self, context: List[str], text: str):
        # 构建 Prompt
        rag_results = self.rag.search(text)

        rag_block = ""

        if rag_results:

            rag_block = "翻译术语表（仅供参考）:\n"

            for r in rag_results:
                rag_block += f"{r}\n"

            rag_block += "\n"

        if context and self.context_size > 0:
            context_str = "\n".join(context)
            user_content = (
                f"{rag_block}"
                f"上下文：\n{context_str}\n\n"
                f"任务：把下面字幕翻译成{self.target_language}。\n\n"
                f"规则：\n"
                f"1 只翻译最后这一句\n"
                f"2 不要输出术语表内容\n"
                f"3 不要添加解释\n"
                f"4 保持自然口语\n\n"
                f"字幕：\n{text}"
            )
        else:
            user_content = (
                f"{rag_block}"
                f"任务：把下面字幕翻译成{self.target_language}。\n\n"
                f"规则：\n"
                f"1 只输出翻译\n"
                f"2 不要输出术语表内容\n"
                f"3 不要解释\n\n"
                f"字幕：\n{text}"
            )

        return [{"role": "user", "content": user_content}]

    def _similarity(self, s1: str, s2: str):
        # 计算两个字符串的相似度（0~1）
        if not s1 or not s2:
            return 0.0
        return SequenceMatcher(None, s1, s2).ratio()

    def clean_output(self, text: str):
        # 清洗模型输出，移除多余前缀和换行
        text = text.strip()
        prefixes = ["Chinese:", "中文：", "Translation:", "翻译："]
        for p in prefixes:
            if text.startswith(p):
                text = text[len(p):].strip()
        text = text.split('\n')[0].strip()
        text = re.sub(r'\s+', ' ', text)
        return text

    def translate(self, context: List[str], text: str):
        # 单句翻译
        original_text = text
        messages = self.build_messages(context, text)

        inputs = self.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt",
            truncation=True,
            max_length=1024
        )

        inputs = inputs.to(self.model.device)

        with torch.no_grad():
            outputs = self.model.generate(
                inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=self.do_sample,
                temperature=self.temperature,
                top_p=self.top_p,
                top_k=self.top_k,
                repetition_penalty=self.repetition_penalty,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )

        generated = outputs[0][inputs.shape[-1]:]
        result = self.tokenizer.decode(generated, skip_special_tokens=True)
        result = self.clean_output(result)

        if self.last_translation and self._similarity(result, self.last_translation) > 0.9:
            result = f"{result} (⚠️ 可能与上句重复)"

        self.last_translation = result

        if not result:
            return f"[翻译失败] {original_text}"

        return result


# ===============================
# SRT 处理器
# ===============================
class SRTTranslator:
    def __init__(self, translator: LLMTranslator):
        self.translator = translator

    @staticmethod
    def parse_srt(path: str):
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
            if block and len(block) >= 3:
                idx = int(block[0])
                start, end = block[1].split(" --> ")
                text = " ".join(block[2:])
                subs.append(Subtitle(idx, start, end, text))
        return subs

    @staticmethod
    def save_srt(subs: List[Subtitle], path: str):
        with open(path, "w", encoding="utf-8") as f:
            for s in subs:
                f.write(f"{s.idx}\n")
                f.write(f"{s.start} --> {s.end}\n")
                f.write(s.text + "\n\n")

    def translate_file(self, input_srt: str):
        subs = self.parse_srt(input_srt)
        bilingual = []
        chinese = []

        print(f"开始翻译 {len(subs)} 条字幕...\n")
        time.sleep(1)
        for i in tqdm(range(len(subs))):
            current = subs[i]
            context_start = max(0, i - self.translator.context_size)
            context_texts = [subs[j].text for j in range(context_start, i)]

            zh = self.translator.translate(context_texts, current.text)

            bilingual.append(
                Subtitle(
                    current.idx,
                    current.start,
                    current.end,
                    current.text + "\n" + zh
                )
            )
            chinese.append(
                Subtitle(
                    current.idx,
                    current.start,
                    current.end,
                    zh
                )
            )

        base, ext = os.path.splitext(input_srt)
        self.save_srt(bilingual, base + "_bilingual" + ext)
        self.save_srt(chinese, base + "_zh" + ext)

        print("\n翻译完成！")


if __name__ == "__main__":
    MODEL_PATH = "../models/HY-MT1.5-1.8B"
    INPUT_SRT = "../subtitle/Building a better Star Wars AT-AT toy.en_processed.srt"
    CONTEXT_SIZE = 0
    translator = LLMTranslator(
        model_path=MODEL_PATH,
        context_size=CONTEXT_SIZE,
        target_language="中文",
        max_new_tokens=200,
        do_sample=True,
        temperature=0.7,
        top_p=0.6,
        top_k=20,
        repetition_penalty=1.05
    )

    if not os.path.exists(INPUT_SRT):
        print(f"错误：文件 {INPUT_SRT} 不存在，请检查路径。")
    else:
        srt_translator = SRTTranslator(translator)
        srt_translator.translate_file(INPUT_SRT)