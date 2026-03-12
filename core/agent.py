from .context import ContextManager
from .memory.long_term import LongTermMemory
from .reasoning.translator_chain import TranslatorChain


class AISpiderAgent:

    def __init__(self, model_path, knowledge_files):
        self.context = ContextManager(size=3)

        self.long_memory = LongTermMemory(knowledge_files)

        self.translator = TranslatorChain(model_path)

    def translate_sentence(self, text):
        context = self.context.get_context()

        # 从长时记忆检索相关知识（返回字符串列表，需拼接）
        knowledge_list = self.long_memory.retrieve(text)
        knowledge = "\n".join(knowledge_list)

        result = self.translator.translate(
            text=text,
            context=context,
            knowledge=knowledge
        )

        self.context.add(text)

        return result
