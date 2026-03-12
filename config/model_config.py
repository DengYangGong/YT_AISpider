import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")

# 模型路径
EMBEDDING_MODEL_PATH = os.path.join(MODELS_DIR, "all-MiniLM-L6-v2")
TRANSLATION_MODEL_PATH = os.path.join(MODELS_DIR, "HY-MT1.5-1.8B")

# 推理参数
MAX_NEW_TOKENS = 200

TEMPERATURE = 0.7
TOP_P = 0.6
TOP_K = 20
REPETITION_PENALTY = 1.05
