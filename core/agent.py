from rag.rag_engine import RAGEngine  # 导入 RAGEngine
from .context import ContextManager
from .reasoning.translator_chain import TranslatorChain


class AISpiderAgent:

    def __init__(self, model_path, knowledge_files, rebuild=False):
        """
        :param model_path: 翻译模型路径
        :param knowledge_files: 知识文件列表（用于 RAGEngine 构建索引，仅当重建时需要）
        :param rebuild: 是否强制重建 RAG 索引
        """
        self.context = ContextManager(size=3)

        # 使用 RAGEngine 替代 LongTermMemory
        self.rag_engine = RAGEngine(rebuild=rebuild)  # RAGEngine 内部会读取 knowledge_files

        self.translator = TranslatorChain(model_path)

    def translate_sentence(self, text):
        context = self.context.get_context()

        # 从 RAGEngine 检索相关知识（直接返回拼接好的字符串）
        knowledge = self.rag_engine.search(text)

        result = self.translator.translate(
            text=text,
            context=context,
            knowledge=knowledge
        )

        self.context.add(text)

        return result
