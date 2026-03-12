from .vector_store import VectorStore


class LongTermMemory:
    def __init__(self, knowledge_files, index_dir="data/vector_db/long_term", rebuild=False):
        """
        :param knowledge_files: 知识文件路径列表（或单个文件路径）
        :param index_dir: 向量库索引保存/加载的目录
        """
        # 确保 knowledge_files 是列表（如果不是，转为列表）
        if isinstance(knowledge_files, str):
            knowledge_files = [knowledge_files]

        self.index_dir = index_dir
        # 传给 VectorStore
        self.vector_memory = VectorStore(knowledge_files, index_path=index_dir, rebuild=rebuild)

    def retrieve(self, query, k=3):
        """检索最相关的 k 条知识"""
        return self.vector_memory.search(query, k=k)
