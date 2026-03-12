from config.settings import KNOWLEDGE_FILES
from rag.rag_engine import RAGEngine
from .context import ContextManager
from .memory.long_term import LongTermMemory
from .reasoning.translator_chain import TranslatorChain


class AISpiderAgent:
    def __init__(self, model_path, context_size=3, knowledge_files=None, rebuild_lm=False, rebuild_rag=False):
        """
        :param model_path: 翻译模型路径
        :param context_size: 上下文窗口大小
        :param knowledge_files: 自定义知识文件列表（如果为 None，则使用默认 KNOWLEDGE_FILES）
        :param rebuild_lm: 是否强制重建 LongTermMemory 索引
        :param rebuild_rag: 是否强制重建 RAGEngine 索引
        """
        self.context = ContextManager(size=context_size)

        # 确定知识文件列表
        kb_files = knowledge_files if knowledge_files is not None else KNOWLEDGE_FILES

        # 同时初始化两个记忆系统
        self.long_memory = LongTermMemory(kb_files, rebuild=rebuild_lm)
        self.rag_engine = RAGEngine(rebuild=rebuild_rag, knowledge_files=kb_files)

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

        result = self.translator.translate(
            text=text,
            context=context,
            knowledge=knowledge
        )

        self.context.add(text)
        return result
