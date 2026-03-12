from langchain_huggingface import HuggingFacePipeline
from transformers import pipeline

from .prompt_templates import TRANSLATION_PROMPT


class TranslatorChain:

    def __init__(self, model_path):
        pipe = pipeline(
            "text-generation",
            model=model_path,
            device=0,
            max_new_tokens=200,
        )

        self.llm = HuggingFacePipeline(pipeline=pipe)

        self.chain = TRANSLATION_PROMPT | self.llm

    def translate(self, text, context="", knowledge=""):
        result = self.chain.invoke({
            "text": text,
            "context": context,
            "knowledge": knowledge
        })

        output = result.strip()

        # 只提取翻译部分
        if "翻译：" in output:
            output = output.split("翻译：")[-1]

        # # 只取第一行（防止模型继续生成）
        # output = output.strip().split("\n")[0]

        return output.strip()
