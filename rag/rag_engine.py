import os

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from config.settings import VECTOR_DB_DIR, TERMS_FILE, ROBOTICS_FILE
from .embedding_model import EmbeddingModel


class RAGEngine:

    def __init__(self):

        self.embedding = EmbeddingModel().get()

        if os.path.exists(VECTOR_DB_DIR):

            self.vector_db = FAISS.load_local(
                VECTOR_DB_DIR,
                self.embedding,
                allow_dangerous_deserialization=True
            )

        else:

            docs = self._load_knowledge()

            self.vector_db = FAISS.from_documents(
                docs,
                self.embedding
            )

            self.vector_db.save_local(VECTOR_DB_DIR)

    def _load_knowledge(self):

        docs = []

        for file in [TERMS_FILE, ROBOTICS_FILE]:

            with open(file, "r", encoding="utf-8") as f:

                for line in f:

                    line = line.strip()

                    if line:
                        docs.append(Document(page_content=line))

        return docs

    def search(self, query, k=3):

        results = self.vector_db.similarity_search(query, k=k)

        return "\n".join([r.page_content for r in results])