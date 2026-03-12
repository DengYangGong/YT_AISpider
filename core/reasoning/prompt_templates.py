from langchain_core.prompts import PromptTemplate

TRANSLATION_PROMPT = PromptTemplate(
    input_variables=["text", "context", "knowledge"],
    template="""
你是一个专业的技术字幕翻译助手。

参考术语：
{knowledge}

上下文：
{context}

任务：
将下面字幕翻译成中文。

要求：
- 只输出翻译
- 不要解释
- 保持口语化
- 保留符号

字幕：
{text}

翻译：
"""
)