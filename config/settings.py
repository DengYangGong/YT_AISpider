import glob
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 数据目录
DATA_DIR = os.path.join(BASE_DIR, "data")

SUBTITLE_DIR = os.path.join(DATA_DIR, "subtitles")
VIDEO_DIR = os.path.join(DATA_DIR, "videos")
VECTOR_DB_DIR = os.path.join(DATA_DIR, "vector_db")

# 知识库目录
KNOWLEDGE_BASE_DIR = os.path.join(BASE_DIR, "rag", "knowledge_base")

# 获取该目录下所有 .txt 文件（可按需添加其他扩展名）
KNOWLEDGE_FILES = glob.glob(os.path.join(KNOWLEDGE_BASE_DIR, "*.txt"))

# RAG配置
TOP_K = 3
