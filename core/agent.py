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

        knowledge = self.long_memory.retrieve(text)

        result = self.translator.translate(
            text=text,
            context=context,
            knowledge=knowledge
        )

        self.context.add(text)

        return result