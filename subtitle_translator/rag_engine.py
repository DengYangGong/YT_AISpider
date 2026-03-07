import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


class RAGEngine:

    def __init__(
        self,
        knowledge_dir="knowledge",
        model_name="./models/all-MiniLM-L6-v2",
        top_k=3
    ):

        print("初始化 RAG 引擎...")

        self.top_k = top_k

        # 路径键修复
        base_dir = os.path.dirname(os.path.abspath(__file__))
        knowledge_dir = os.path.join(base_dir, knowledge_dir)

        print("知识库路径:", knowledge_dir)

        # 加载 embedding 模型
        self.embed_model = SentenceTransformer(model_name)

        self.documents = []

        if not os.path.exists(knowledge_dir):
            raise FileNotFoundError(f"知识库目录不存在: {knowledge_dir}")

        # 读取知识库
        for file in os.listdir(knowledge_dir):

            path = os.path.join(knowledge_dir, file)

            if not path.endswith(".txt"):
                continue

            with open(path, "r", encoding="utf-8") as f:

                for line in f:

                    line = line.strip()

                    if line:
                        self.documents.append(line)

        print(f"知识库加载完成，共 {len(self.documents)} 条知识")

        # 生成 embedding
        embeddings = self.embed_model.encode(
            self.documents,
            convert_to_numpy=True,
            show_progress_bar=True
        )

        dim = embeddings.shape[1]

        # 建立 FAISS index
        self.index = faiss.IndexFlatL2(dim)

        self.index.add(embeddings)

        print("RAG 向量索引建立完成")

    def search(self, query):

        query_embedding = self.embed_model.encode(
            [query],
            convert_to_numpy=True
        )

        distances, indices = self.index.search(query_embedding, self.top_k)

        results = []

        for idx in indices[0]:

            if idx < len(self.documents):
                results.append(self.documents[idx])

        return results