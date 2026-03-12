from langchain_huggingface import HuggingFaceEmbeddings

from config.model_config import EMBEDDING_MODEL_PATH


class EmbeddingModel:

    def __init__(self):
        self.model = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL_PATH
        )

    def get(self):
        return self.model
