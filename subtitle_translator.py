import os
import re
import json
from dataclasses import dataclass
from typing import List, Optional, Dict
from difflib import SequenceMatcher

import torch
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer


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
# 翻译器（修正表完全外部化）
# ===============================
class LLMTranslator:
    def __init__(
        self,
        model_path: str = "./model/HY-MT1.5-1.8B",
        context_size: int = 0,
        target_language: str = "中文",
        device: Optional[str] = None,
        max_new_tokens: int = 200,
        # 官方推荐推理参数
        do_sample: bool = True,
        temperature: float = 0.7,
        top_p: float = 0.6,
        top_k: int = 20,
        repetition_penalty: float = 1.05,
        fixes_file: str = "my_fixes.json"          # 外部修正规则文件，默认文件名
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
        self.fixes_file = fixes_file

        # 存储上一句译文，用于重复检测
        self.last_translation = ""

        # 从文件加载修正规则（如果文件不存在则创建空字典）
        self.error_fixes: Dict[str, str] = self._load_fixes()

        print(f"模型加载完成，设备：{self.device}，上下文大小：{self.context_size}")
        print(f"当前错误修正规则数：{len(self.error_fixes)}")

    def _load_fixes(self) -> Dict[str, str]:
        """从 JSON 文件加载修正规则，如果文件不存在则返回空字典"""
        if os.path.exists(self.fixes_file):
            try:
                with open(self.fixes_file, 'r', encoding='utf-8') as f:
                    fixes = json.load(f)
                if isinstance(fixes, dict):
                    print(f"已从 {self.fixes_file} 加载 {len(fixes)} 条修正规则。")
                    return fixes
                else:
                    print(f"错误：{self.fixes_file} 内容不是字典，将使用空规则。")
                    return {}
            except Exception as e:
                print(f"读取修正文件出错：{e}，将使用空规则。")
                return {}
        else:
            print(f"修正文件 {self.fixes_file} 不存在，将创建空规则文件。")
            self._save_fixes({})  # 创建空文件
            return {}

    def _save_fixes(self, fixes: Dict[str, str]):
        """保存修正规则到 JSON 文件"""
        try:
            with open(self.fixes_file, 'w', encoding='utf-8') as f:
                json.dump(fixes, f, ensure_ascii=False, indent=2)
            print(f"修正规则已保存到 {self.fixes_file}")
        except Exception as e:
            print(f"保存修正文件出错：{e}")

    def add_fix_interactively(self):
        """交互式添加新的修正规则"""
        print("\n--- 添加新的错误修正规则 ---")
        print("输入规则时，请使用正则表达式模式（例如：\\\bat a tea\\\b）")
        print("规则将不区分大小写。直接回车可跳过添加。")
        while True:
            pattern = input("请输入要匹配的正则表达式（直接回车结束）：").strip()
            if not pattern:
                break
            replacement = input("请输入替换后的文本：").strip()
            if not replacement:
                print("替换文本不能为空，请重新输入。")
                continue
            # 添加到当前规则
            self.error_fixes[pattern] = replacement
            print(f"已添加规则：{pattern} -> {replacement}")
            # 立即保存到文件
            self._save_fixes(self.error_fixes)
        print("规则添加结束。")

    def _fix_text(self, text: str) -> str:
        """对原文应用所有修正规则"""
        if not self.error_fixes:
            return text
        for pattern, repl in self.error_fixes.items():
            try:
                text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
            except re.error as e:
                print(f"正则表达式错误 '{pattern}': {e}，已跳过该规则。")
        return text

    def build_messages(self, context: List[str], text: str):
        """根据官方模板构建消息，并加入强化指令"""
        # 先修正原文
        text = self._fix_text(text)

        if context and self.context_size > 0:
            context_str = "\n".join(context)
            user_content = (
                f"{context_str}\n"
                f"参考上面的信息，把下面的文本翻译成{self.target_language}。\n"
                f"重要规则：\n"
                f"1. 只翻译下面这一句，绝对不要引入上文未出现的内容。\n"
                f"2. 不要添加原文没有的信息。\n"
                f"3. 注意代词指代，确保逻辑准确。\n"
                f"4. 保持为一个完整句子。\n\n"
                f"{text}"
            )
        else:
            user_content = (
                f"将以下文本翻译为{self.target_language}，注意：\n"
                f"- 只输出翻译结果，不要解释\n"
                f"- 不要添加原文没有的内容\n"
                f"- 保持为一个完整句子\n\n"
                f"{text}"
            )

        return [{"role": "user", "content": user_content}]

    def _similarity(self, s1: str, s2: str) -> float:
        """计算两个字符串的相似度（0~1）"""
        if not s1 or not s2:
            return 0.0
        return SequenceMatcher(None, s1, s2).ratio()

    def clean_output(self, text: str) -> str:
        """清洗模型输出，移除多余前缀和换行"""
        text = text.strip()
        prefixes = ["Chinese:", "中文：", "Translation:", "翻译："]
        for p in prefixes:
            if text.startswith(p):
                text = text[len(p):].strip()
        text = text.split('\n')[0].strip()
        text = re.sub(r'\s+', ' ', text)
        return text

    def translate(self, context: List[str], text: str) -> str:
        """翻译单条字幕"""
        original_text = text
        messages = self.build_messages(context, text)

        inputs = self.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt",
            truncation=True,
            max_length=1024
        )
        # 自动匹配模型设备
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

        # 重复检测
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
    def parse_srt(path: str) -> List[Subtitle]:
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
    # 配置参数
    MODEL_PATH = "./model/HY-MT1.5-1.8B"      # 模型路径
    INPUT_SRT = "./subtitle/Building a better Star Wars AT-AT toy.en_processed.srt"  # 输入字幕文件
    CONTEXT_SIZE = 0                           # 上下文句子数量
    FIXES_FILE = "./my_fixes.json"                   # 修正表文件

    # 创建翻译器
    translator = LLMTranslator(
        model_path=MODEL_PATH,
        context_size=CONTEXT_SIZE,
        target_language="中文",
        max_new_tokens=200,
        do_sample=True,
        temperature=0.7,
        top_p=0.6,
        top_k=20,
        repetition_penalty=1.05,
        fixes_file=FIXES_FILE
    )

    # 询问是否添加新规则
    print("\n是否要向修正表添加新的错误修正规则？(y/n)")
    choice = input().strip().lower()
    if choice == 'y':
        translator.add_fix_interactively()

    # 执行翻译
    if not os.path.exists(INPUT_SRT):
        print(f"错误：文件 {INPUT_SRT} 不存在，请检查路径。")
    else:
        srt_translator = SRTTranslator(translator)
        srt_translator.translate_file(INPUT_SRT)