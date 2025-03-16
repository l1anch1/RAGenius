import os
from pathlib import Path

# Data directories
BASE_DIR = str(Path(__file__).resolve().parent.parent)
DATA_DIR = os.getenv("DATA_DIR", os.path.join(BASE_DIR, "data"))
DOCUMENTS_DIR = os.getenv("DOCUMENTS_DIR", os.path.join(DATA_DIR, "documents"))
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", os.path.join(DATA_DIR, "vectordb"))

# Model settings
DEFAULT_LLM_MODEL = os.getenv("DEFAULT_MODEL", "deepseek-r1:14b")
DEFAULT_EMBEDDING_MODEL = os.getenv(
    "DEFAULT_EMBEDDING_MODEL", "sentence-transformers/all-mpnet-base-v2"
)
MODEL_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", "0.1"))
MODEL_TOP_P = float(os.getenv("MODEL_TOP_P", "0.9"))
MODEL_NUM_CTX = int(os.getenv("MODEL_NUM_CTX", "8192"))
MODEL_NUM_PREDICT = int(os.getenv("MODEL_NUM_PREDICT", "2048"))
MODEL_NUM_THREAD = int(os.getenv("MODEL_NUM_THREAD", "4"))

# Chunking settings
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "600"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))

# Retrieval settings
SEARCH_K = int(
    os.getenv("SEARCH_K", "5")
)  # Number of documents to return during retrieval
