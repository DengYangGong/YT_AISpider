import os
from typing import Union, List
from langchain_huggingface import HuggingFaceEmbeddings  # 新导入
from langchain_community.vectorstores import FAISS

from config.model_config import EMBEDDING_MODEL_PATH


class VectorStore:
    def __init__(
        self,
        knowledge_paths: Union[str, List[str]],
        index_path: str = None
    ):
        """
        初始化向量存储
        :param knowledge_paths: 知识文件路径（单个字符串或字符串列表）
        :param index_path: 可选，FAISS 索引的保存/加载路径
        """
        self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_PATH)

        # 统一转换为列表
        if isinstance(knowledge_paths, str):
            knowledge_paths = [knowledge_paths]

        # 如果提供了索引路径且存在，则直接加载
        if index_path and os.path.exists(index_path):
            self.vector_db = FAISS.load_local(index_path, self.embeddings)
            return

        # 否则从文件构建索引
        texts = []
        for path in knowledge_paths:
            if not os.path.exists(path):
                raise FileNotFoundError(f"Knowledge file not found: {path}")
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        texts.append(line)

        self.vector_db = FAISS.from_texts(texts, embedding=self.embeddings)

        # 如果指定了索引路径，保存索引以便下次快速加载
        if index_path:
            self.vector_db.save_local(index_path)

    def search(self, query: str, k: int = 3) -> List[str]:
        """
        搜索最相似的 k 条文本
        :return: 文本列表
        """
        docs = self.vector_db.similarity_search(query, k=k)
        return [doc.page_content for doc in docs]