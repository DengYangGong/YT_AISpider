import os

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from config.settings import VECTOR_DB_DIR, KNOWLEDGE_FILES  # 导入新的配置
from .embedding_model import EmbeddingModel


class RAGEngine:

    def __init__(self, rebuild=False):
        """
        :param rebuild: 如果为 True，强制重新构建向量数据库
        """
        self.embedding = EmbeddingModel().get()
        self.index_path = os.path.join(VECTOR_DB_DIR, "rag.faiss")

        # 如果索引已存在且不强制重建，则直接加载
        if not rebuild and os.path.exists(self.index_path):
            print("加载已有向量数据库...")
            self.vector_db = FAISS.load_local(
                VECTOR_DB_DIR,
                self.embedding,
                allow_dangerous_deserialization=True
            )
        else:
            self._build_index()

    def _build_index(self):
        """构建新的向量数据库"""
        print("构建新的向量数据库...")
        docs = self._load_knowledge()

        if not docs:
            raise ValueError("没有加载到任何文档，无法构建索引。请检查知识库文件是否为空。")

        self.vector_db = FAISS.from_documents(docs, self.embedding)
        os.makedirs(VECTOR_DB_DIR, exist_ok=True)
        self.vector_db.save_local(VECTOR_DB_DIR)
        print(f"向量数据库构建完成，已保存至 {VECTOR_DB_DIR}")

    def _load_knowledge(self):
        """加载所有知识文件，每行作为一个文档"""
        docs = []
        for file_path in KNOWLEDGE_FILES:
            if not os.path.exists(file_path):
                print(f"警告：知识文件不存在，已跳过 {file_path}")
                continue
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            docs.append(Document(page_content=line))
            except Exception as e:
                print(f"读取文件 {file_path} 时出错：{e}")
                continue
        print(f"共加载 {len(docs)} 条知识片段")
        return docs

    def search(self, query, k=3):
        """
        检索最相似的 k 条知识，返回拼接字符串
        """
        if not hasattr(self, 'vector_db') or self.vector_db is None:
            raise RuntimeError("向量数据库未初始化，请先调用 __init__ 或检查构建过程。")
        results = self.vector_db.similarity_search(query, k=k)
        unique = []

        for r in results:

            if r.page_content not in unique:
                unique.append(r.page_content)

        return "\n".join(unique)

    # 可选：返回列表版本，方便上层处理
    def search_as_list(self, query, k=3):
        results = self.vector_db.similarity_search(query, k=k)
        return [r.page_content for r in results]
