"""
Application Configuration
应用配置 - 统一使用 .env + 代码默认值
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================
# 基础设置
# ============================================

# Device settings
DEVICE = os.getenv("DEVICE", "cpu")

# ============================================
# LLM 设置
# ============================================

LLM_USE_OPENAI = os.getenv("LLM_USE_OPENAI", "true").lower() in ("true", "1", "yes")
LLM_OPENAI_API_KEY = os.environ.get("LLM_OPENAI_API_KEY", "")
LLM_OPENAI_MODEL = os.environ.get("LLM_OPENAI_MODEL", "gpt-4o")
LLM_OPENAI_API_BASE = os.environ.get("LLM_OPENAI_API_BASE", "https://api.openai-proxy.org/v1")
LLM_LOCAL_MODEL = os.getenv("LLM_LOCAL_MODEL", "deepseek-r1:14b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))
LLM_NUM_THREAD = int(os.getenv("LLM_NUM_THREAD", "12"))  # 用于系统信息显示

# Ollama 特有参数
LLM_NUM_CTX = int(os.getenv("LLM_NUM_CTX", "8192"))       # 上下文窗口大小
LLM_NUM_PREDICT = int(os.getenv("LLM_NUM_PREDICT", "2048"))  # 最大生成 token 数

# ============================================
# Embedding 设置
# ============================================

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-base-zh-v1.5")

# ============================================
# Chunking 设置
# ============================================

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "600"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))

# ============================================
# 检索流水线设置 - Query Expansion
# ============================================

QUERY_EXPANSION_ENABLED = os.getenv("QUERY_EXPANSION_ENABLED", "true").lower() in ("true", "1", "yes")
QUERY_EXPANSION_N_SUBQUERIES = int(os.getenv("QUERY_EXPANSION_N_SUBQUERIES", "2"))
QUERY_EXPANSION_MODEL = os.getenv("QUERY_EXPANSION_MODEL", "gpt-4o-mini")
QUERY_EXPANSION_TEMPERATURE = float(os.getenv("QUERY_EXPANSION_TEMPERATURE", "0.7"))
QUERY_EXPANSION_INCLUDE_ORIGINAL = os.getenv("QUERY_EXPANSION_INCLUDE_ORIGINAL", "true").lower() in ("true", "1", "yes")

# ============================================
# 检索流水线设置 - Hybrid Retrieval
# ============================================

HYBRID_TOP_K_PER_QUERY = int(os.getenv("HYBRID_TOP_K_PER_QUERY", "15"))

# ============================================
# 检索流水线设置 - RRF Fusion
# ============================================

RRF_K = int(os.getenv("RRF_K", "60"))
RRF_TOP_K = int(os.getenv("RRF_TOP_K", "12"))

# ============================================
# 检索流水线设置 - Reranking
# ============================================

RERANKING_ENABLED = os.getenv("RERANKING_ENABLED", "true").lower() in ("true", "1", "yes")
RERANKING_MODEL = os.getenv("RERANKING_MODEL", "cross-encoder/ms-marco-MiniLM-L-2-v2")
RERANKING_TOP_K = int(os.getenv("RERANKING_TOP_K", "8"))
RERANKING_BATCH_SIZE = int(os.getenv("RERANKING_BATCH_SIZE", "32"))

# ============================================
# 检索流水线设置 - Score Truncation (智能分数截断)
# ============================================

SCORE_TRUNCATION_ENABLED = os.getenv("SCORE_TRUNCATION_ENABLED", "true").lower() in ("true", "1", "yes")
SCORE_GAP_THRESHOLD = float(os.getenv("SCORE_GAP_THRESHOLD", "5.0"))  # 相邻分数差阈值
SCORE_MIN_THRESHOLD = float(os.getenv("SCORE_MIN_THRESHOLD", "-6.0"))  # 绝对最低分数阈值

# ============================================
# 检索流水线设置 - MMR Post-processing
# ============================================

MMR_MODE = os.getenv("MMR_MODE", "auto")  # auto | always | never
MMR_SIMILARITY_THRESHOLD = float(os.getenv("MMR_SIMILARITY_THRESHOLD", "0.8"))
MMR_LAMBDA = float(os.getenv("MMR_LAMBDA", "0.7"))
MMR_FINAL_K = int(os.getenv("MMR_FINAL_K", "5"))

# ============================================
# 检索流水线设置 - 全局
# ============================================

SEARCH_K = int(os.getenv("SEARCH_K", "8"))

# ============================================
# 时间监控设置
# ============================================

TIMING_ENABLED = os.getenv("TIMING_ENABLED", "true").lower() in ("true", "1", "yes")
TIMING_SHOW_IN_TERMINAL = os.getenv("TIMING_SHOW_IN_TERMINAL", "true").lower() in ("true", "1", "yes")
TIMING_MIN_DURATION_MS = float(os.getenv("TIMING_MIN_DURATION_MS", "0.0"))  # 最小显示阈值(ms)

