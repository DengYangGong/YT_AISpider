from langchain_core.prompts import PromptTemplate

# 构造提示词
TRANSLATION_PROMPT = PromptTemplate(
    input_variables=["context", "knowledge", "text"],
    template="""
你是一个专业字幕翻译助手。

参考信息：
{knowledge}

上下文：
{context}

任务：
将下面的英文字幕翻译成中文。

要求：
1 只翻译当前句子
2 保持字幕自然
3 不要添加解释

英文：
{text}

中文：
"""
)