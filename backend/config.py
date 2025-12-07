import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Device settings
DEVICE = os.getenv("DEVICE", "cpu")

# Data directories - all paths relative to project root
BASE_DIR = str(Path(__file__).resolve().parent.parent)  # Project root directory
# Note: Documents are now stored in memory, not on disk
VECTOR_DB_DIR = os.getenv("VECTOR_DB_DIR", os.path.join(BASE_DIR, "data", "vectordb"))

# LLM model settings
LLM_USE_OPENAI = os.getenv("LLM_USE_OPENAI", "true").lower() in ("true", "1", "yes")
LLM_OPENAI_API_KEY = os.environ.get("LLM_OPENAI_API_KEY", "")
LLM_OPENAI_MODEL = os.environ.get("LLM_OPENAI_MODEL", "gpt-4o")
LLM_OPENAI_API_BASE = os.environ.get("LLM_OPENAI_API_BASE", "")
LLM_LOCAL_MODEL = os.getenv("LLM_LOCAL_MODEL", "deepseek-r1:14b")
# Ollama base URL - use host.docker.internal in Docker environment
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
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

# Hybrid retrieval settings
SIMILARITY_WEIGHT = float(os.getenv("SIMILARITY_WEIGHT", "0.6"))  # 语义相似度权重
MMR_WEIGHT = float(os.getenv("MMR_WEIGHT", "0.4"))  # MMR多样性权重
MMR_LAMBDA = float(os.getenv("MMR_LAMBDA", "0.7"))  # MMR lambda参数，平衡相关性和多样性
