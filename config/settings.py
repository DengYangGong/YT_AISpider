import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 数据目录
DATA_DIR = os.path.join(BASE_DIR, "data")

SUBTITLE_DIR = os.path.join(DATA_DIR, "subtitles")
VIDEO_DIR = os.path.join(DATA_DIR, "videos")
VECTOR_DB_DIR = os.path.join(DATA_DIR, "vector_db")

# 知识库
KNOWLEDGE_BASE_DIR = os.path.join(BASE_DIR, "rag", "knowledge_base")

TERMS_FILE = os.path.join(KNOWLEDGE_BASE_DIR, "terms.txt")
ROBOTICS_FILE = os.path.join(KNOWLEDGE_BASE_DIR, "robotics.txt")

# RAG配置
TOP_K = 3
