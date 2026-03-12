from config.settings import KNOWLEDGE_FILES
from rag.rag_engine import RAGEngine
from .context import ContextManager
from .memory.long_term import LongTermMemory
from .reasoning.translator_chain import TranslatorChain


class AISpiderAgent:

    def __init__(self, model_path, rebuild_lm=False, rebuild_rag=False):
        """
        :param model_path: 翻译模型路径
        :param rebuild: 是否强制重建两个记忆系统的索引
        """
        self.context = ContextManager(size=3)

        # 同时初始化两个记忆系统
        self.long_memory = LongTermMemory(KNOWLEDGE_FILES, rebuild=rebuild_lm)
        self.rag_engine = RAGEngine(rebuild=rebuild_rag)

        self.translator = TranslatorChain(model_path)

    def translate_sentence(self, text):
        context = self.context.get_context()

        # 从 LongTermMemory 检索（返回列表）
        long_knowledge_list = self.long_memory.retrieve(text)

        # 从 RAGEngine 检索（返回拼接字符串，按行分割成列表）
        rag_knowledge_str = self.rag_engine.search(text)
        rag_knowledge_list = rag_knowledge_str.split("\n") if rag_knowledge_str else []

        # 合并两个列表并去重
        combined = list(set(long_knowledge_list + rag_knowledge_list))
        knowledge = "\n".join(combined)

        # 调用翻译链
        result = self.translator.translate(
            text=text,
            context=context,
            knowledge=knowledge
        )

        # 更新短期上下文
        self.context.add(text)

        return result
