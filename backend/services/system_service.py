"""
System Service
系统服务实现
"""
from typing import Dict, Any
import logging

from interfaces.services import SystemServiceInterface
from interfaces.vector_store import VectorStoreInterface, LLMInterface
from config import (
    LLM_LOCAL_MODEL,
    EMBEDDING_MODEL,
    LLM_NUM_THREAD,
    LLM_USE_OPENAI,
    LLM_OPENAI_API_KEY,
    LLM_OPENAI_MODEL,
)

logger = logging.getLogger(__name__)


class SystemService(SystemServiceInterface):
    """系统服务实现"""
    
    def __init__(self, vector_store_manager: VectorStoreInterface, llm_manager: LLMInterface):
        """
        初始化系统服务
        
        Args:
            vector_store_manager: 向量存储管理器
            llm_manager: LLM管理器
        """
        self.vector_store_manager = vector_store_manager
        self.llm_manager = llm_manager
        logger.info("SystemService initialized")
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        try:
            # 检查各组件状态
            vector_store_available = self.vector_store_manager.is_available()
            llm_available = self.llm_manager.is_available()
            initialized = vector_store_available and llm_available
            
            # 获取向量化文档信息
            vectorized_info = self.vector_store_manager.get_vectorized_documents()
            
            # 确定当前使用的模型
            model = (
                LLM_OPENAI_MODEL
                if LLM_USE_OPENAI and LLM_OPENAI_API_KEY
                else LLM_LOCAL_MODEL
            )
            
            # 构建系统信息 - 兼容旧版本API格式
            system_info = {
                "status": "success",
                "model": model,
                "embedding_model": EMBEDDING_MODEL,
                "threads": LLM_NUM_THREAD,
                "initialized": initialized,
                # 新架构的详细信息
                "components": {
                    "vector_store": {
                        "available": vector_store_available,
                        "documents_count": len(vectorized_info.get("documents", [])),
                        "total_chunks": vectorized_info.get("total_chunks", 0)
                    },
                    "llm": {
                        "available": llm_available,
                        "model_type": "OpenAI" if LLM_USE_OPENAI else "Ollama",
                        "model_name": model
                    },
                    "embedding": {
                        "available": vector_store_available,  # 嵌入模型与向量存储相关
                        "model_name": EMBEDDING_MODEL
                    }
                },
                "version": "1.0.0"
            }
            
            logger.debug(f"System info: {system_info}")
            return system_info
            
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            return {
                "status": "error",
                "message": str(e),
                "initialized": False,
                "model": "unknown",
                "embedding_model": "unknown", 
                "threads": 0
            }
    
    def is_initialized(self) -> bool:
        """检查系统是否已初始化"""
        try:
            return (self.vector_store_manager.is_available() and 
                    self.llm_manager.is_available())
        except Exception as e:
            logger.error(f"Initialization check failed: {e}")
            return False
