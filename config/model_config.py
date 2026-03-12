import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")

EMBEDDING_MODEL_PATH = os.path.join(MODELS_DIR, "all-MiniLM-L6-v2")
TRANSLATION_MODEL_PATH = os.path.join(MODELS_DIR, "HY-MT1.5-1.8B")