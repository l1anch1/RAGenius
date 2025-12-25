"""
Model Manager
模型管理器实现
"""
import os
from typing import Optional, Any
import logging

from interfaces.vector_store import EmbeddingInterface, LLMInterface
from managers.cache_manager import CacheManager
from config import (
    LLM_USE_OPENAI, LLM_OPENAI_MODEL, LLM_OPENAI_API_KEY, LLM_OPENAI_API_BASE,
    EMBEDDING_MODEL, DEVICE, LLM_TEMPERATURE, LLM_LOCAL_MODEL, OLLAMA_BASE_URL,
    LLM_NUM_CTX, LLM_NUM_PREDICT
)

logger = logging.getLogger(__name__)


class EmbeddingManager(EmbeddingInterface):
    """嵌入模型管理器"""
    
    def __init__(self):
        self._cache_manager = CacheManager(
            ttl=3600,  # 1小时TTL
            name="embedding_model"
        )
    
    def get_embeddings(self) -> Optional[Any]:
        """获取嵌入模型"""
        return self._cache_manager.get_or_create(self._create_embedding_model)
    
    def is_available(self) -> bool:
        """检查嵌入模型是否可用"""
        try:
            model = self.get_embeddings()
            return model is not None
        except Exception as e:
            logger.error(f"Embedding model availability check failed: {e}")
            return False
    
    def _create_embedding_model(self) -> Optional[Any]:
        """创建嵌入模型"""
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
            
            model_name = EMBEDDING_MODEL
            model_kwargs = {"device": DEVICE}
            encode_kwargs = {"normalize_embeddings": True}
            
            logger.info(f"Loading embedding model: {model_name}")
            
            # 添加超时和错误处理
            import time
            start_time = time.time()
            
            try:
                embedding_model = HuggingFaceEmbeddings(
                    model_name=model_name,
                    model_kwargs=model_kwargs,
                    encode_kwargs=encode_kwargs,
                    cache_folder="./models_cache"
                )
                
                elapsed_time = time.time() - start_time
                logger.info(f"Embedding model loaded successfully: {model_name} (took {elapsed_time:.2f} seconds)")
                return embedding_model
                
            except Exception as load_error:
                logger.error(f"Error during model loading: {load_error}")
                logger.error("This might be due to:")
                logger.error("1. Network issues (model download)")
                logger.error("2. Insufficient memory")
                logger.error("3. Model cache corruption")
                raise
            
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            import traceback
            traceback.print_exc()
            return None


class QueryExpansionLLMManager:
    """
    Query Expansion 专用 LLM 管理器
    
    使用轻量模型（如 gpt-4o-mini）进行查询扩展，
    与主 LLM（如 gpt-4o）分开管理。
    """
    
    def __init__(self):
        from config import QUERY_EXPANSION_MODEL, QUERY_EXPANSION_TEMPERATURE
        
        self._cache_manager = CacheManager(
            ttl=3600,
            name="query_expansion_llm"
        )
        self.model = QUERY_EXPANSION_MODEL
        self.temperature = QUERY_EXPANSION_TEMPERATURE
    
    def get_llm(self) -> Optional[Any]:
        """获取 Query Expansion LLM"""
        return self._cache_manager.get_or_create(self._create_llm)
    
    def _create_llm(self) -> Optional[Any]:
        """创建轻量 LLM"""
        try:
            from langchain_openai import ChatOpenAI
            
            api_key = os.environ.get("LLM_OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
            api_base = os.environ.get("LLM_OPENAI_API_BASE", "")
            
            kwargs = {
                "model": self.model,
                "temperature": self.temperature,
                "api_key": api_key
            }
            if api_base:
                kwargs["base_url"] = api_base
            
            logger.info(f"Loading Query Expansion LLM: {self.model}")
            return ChatOpenAI(**kwargs)
            
        except Exception as e:
            logger.error(f"Failed to create Query Expansion LLM: {e}")
            return None


class RerankingModelManager:
    """
    Cross-Encoder Reranking 模型管理器
    
    使用 sentence-transformers 的 CrossEncoder 进行重排。
    模型较大，需要统一管理和缓存。
    """
    
    def __init__(self):
        from config import RERANKING_MODEL
        
        self._cache_manager = CacheManager(
            ttl=3600,
            name="reranking_model"
        )
        self.model_name = RERANKING_MODEL
    
    def get_model(self) -> Optional[Any]:
        """获取 Reranking 模型"""
        return self._cache_manager.get_or_create(self._create_model)
    
    def _create_model(self) -> Optional[Any]:
        """创建 CrossEncoder 模型"""
        try:
            from sentence_transformers import CrossEncoder
            
            logger.info(f"Loading Cross-Encoder model: {self.model_name}")
            model = CrossEncoder(self.model_name, max_length=512)
            logger.info(f"Cross-Encoder model loaded: {self.model_name}")
            return model
            
        except ImportError:
            logger.error("sentence-transformers not installed. Run: pip install sentence-transformers")
            return None
        except Exception as e:
            logger.error(f"Failed to create Cross-Encoder model: {e}")
            return None


class LLMManager(LLMInterface):
    """大语言模型管理器（主 LLM，用于生成回答）"""
    
    def __init__(self):
        self._cache_manager = CacheManager(
            ttl=3600,  # 1小时TTL
            name="llm_model"
        )
    
    def get_llm(self) -> Optional[Any]:
        """获取LLM模型"""
        return self._cache_manager.get_or_create(self._create_llm_model)
    
    def is_available(self) -> bool:
        """检查LLM是否可用"""
        try:
            model = self.get_llm()
            return model is not None
        except Exception as e:
            logger.error(f"LLM availability check failed: {e}")
            return False
    
    def _create_llm_model(self) -> Optional[Any]:
        """创建LLM模型"""
        try:
            if LLM_USE_OPENAI:
                return self._create_openai_model()
            else:
                return self._create_ollama_model()
        except Exception as e:
            logger.error(f"Failed to create LLM model: {e}")
            return None
    
    def _create_openai_model(self) -> Optional[Any]:
        """创建OpenAI模型"""
        try:
            from langchain_openai import ChatOpenAI
            
            # 检查API密钥
            api_key = os.environ.get("LLM_OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
            if not api_key:
                # 设置一个dummy key以允许应用启动，但会在使用时失败
                logger.warning("OpenAI API key not set, using dummy key")
                os.environ["OPENAI_API_KEY"] = "sk-dummy-key-for-testing"
                api_key = "sk-dummy-key-for-testing"
            
            model_kwargs = {
                "model": LLM_OPENAI_MODEL,
                "temperature": LLM_TEMPERATURE,
                "api_key": api_key,
                "streaming": True
            }
            
            # 如果设置了自定义API base URL
            if LLM_OPENAI_API_BASE:
                model_kwargs["base_url"] = LLM_OPENAI_API_BASE
            
            logger.info(f"Loading OpenAI model: {LLM_OPENAI_MODEL}")
            llm = ChatOpenAI(**model_kwargs)
            
            logger.info(f"OpenAI model loaded successfully: {LLM_OPENAI_MODEL}")
            return llm
            
        except Exception as e:
            logger.error(f"Failed to load OpenAI model: {e}")
            return None
    
    def _create_ollama_model(self) -> Optional[Any]:
        """创建Ollama模型"""
        try:
            from langchain_ollama import ChatOllama
            
            logger.info(f"Loading Ollama model: {LLM_LOCAL_MODEL}")
            logger.info(f"Ollama base URL: {OLLAMA_BASE_URL}")
            logger.info(f"Context window: {LLM_NUM_CTX}, Max predict: {LLM_NUM_PREDICT}")
            
            llm = ChatOllama(
                model=LLM_LOCAL_MODEL,
                base_url=OLLAMA_BASE_URL,
                temperature=LLM_TEMPERATURE,
                num_ctx=LLM_NUM_CTX,
                num_predict=LLM_NUM_PREDICT,
            )
            
            logger.info(f"Ollama model loaded successfully: {LLM_LOCAL_MODEL}")
            return llm
            
        except Exception as e:
            logger.error(f"Failed to load Ollama model: {e}")
            return None
