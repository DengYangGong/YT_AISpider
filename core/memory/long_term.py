from .vector_store import VectorStoreMemory


class LongTermMemory:

    def __init__(self, knowledge_files):

        docs = []

        for file in knowledge_files:

            with open(file, "r", encoding="utf-8") as f:
                docs.extend(f.readlines())

        self.vector_memory = VectorStoreMemory(docs)

    def retrieve(self, query):

        return self.vector_memory.search(query)