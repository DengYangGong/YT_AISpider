from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings


class VectorStore:

    def __init__(self, knowledge_path):

        self.embeddings = HuggingFaceEmbeddings(
            model_name="../models/all-MiniLM-L6-v2"
        )

        texts = []

        with open(knowledge_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    texts.append(line)

        self.vector_db = FAISS.from_texts(
            texts,
            embedding=self.embeddings
        )

    def search(self, query, k=3):

        docs = self.vector_db.similarity_search(query, k=k)

        return "\n".join([doc.page_content for doc in docs])