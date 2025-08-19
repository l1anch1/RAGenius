import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Device settings
DEVICE = os.getenv("DEVICE", "cpu")

# Data directories - all paths relative to project root
BASE_DIR = str(Path(__file__).resolve().parent.parent)  # Project root directory
DATA_DIR = os.getenv("DATA_DIR", os.path.join(BASE_DIR, "data"))
DOCUMENTS_DIR = os.getenv("DOCUMENTS_DIR", os.path.join(DATA_DIR, "documents"))
VECTOR_DB_DIR = os.getenv("VECTOR_DB_DIR", os.path.join(DATA_DIR, "vectordb"))

# LLM model settings
LLM_USE_OPENAI = True
LLM_OPENAI_API_KEY = os.environ.get("LLM_OPENAI_API_KEY", "")
LLM_OPENAI_MODEL = os.environ.get("LLM_OPENAI_MODEL", "gpt-4o")
LLM_OPENAI_API_BASE = os.environ.get("LLM_OPENAI_API_BASE", "")
LLM_LOCAL_MODEL = os.getenv("LLM_LOCAL_MODEL", "deepseek-r1:14b")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))
LLM_TOP_P = float(os.getenv("LLM_TOP_P", "0.6"))
LLM_NUM_CTX = int(os.getenv("LLM_NUM_CTX", "8192"))
LLM_NUM_PREDICT = int(os.getenv("LLM_NUM_PREDICT", "2048"))
LLM_NUM_THREAD = int(os.getenv("LLM_NUM_THREAD", "12"))

# Embedding settings
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-base-zh-v1.5")


# Chunking settings
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "600"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))

# Retrieval settings
SEARCH_K = int(
    os.getenv("SEARCH_K", "8")
)  # Number of documents to return during retrieval
