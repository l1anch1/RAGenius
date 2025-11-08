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
    EMBEDDING_MODEL, DEVICE, LLM_TEMPERATURE
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
            from langchain_community.embeddings import HuggingFaceBgeEmbeddings
            
            model_name = EMBEDDING_MODEL
            model_kwargs = {"device": DEVICE}
            encode_kwargs = {"normalize_embeddings": True}
            
            logger.info(f"Loading embedding model: {model_name}")
            logger.info("This may take a few minutes on first run (downloading model)...")
            logger.info("Please wait, the model is being loaded into memory...")
            
            # 添加超时和错误处理
            import time
            start_time = time.time()
            
            try:
                embedding_model = HuggingFaceBgeEmbeddings(
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


class LLMManager(LLMInterface):
    """大语言模型管理器"""
    
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
            from langchain_community.llms import Ollama
            
            logger.info("Loading Ollama model")
            llm = Ollama(model="llama2")
            
            logger.info("Ollama model loaded successfully")
            return llm
            
        except Exception as e:
            logger.error(f"Failed to load Ollama model: {e}")
            return None
