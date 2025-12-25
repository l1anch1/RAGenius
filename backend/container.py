"""
Dependency Injection Container
依赖注入容器
"""
import logging
from typing import Dict, Any

from managers.model_manager import EmbeddingManager, LLMManager
from managers.vector_store_manager import ChromaVectorStoreManager
from services.retrieval import RetrievalOrchestrator
from services.document_service import DocumentService
from services.query_service import QueryService
from services.system_service import SystemService

logger = logging.getLogger(__name__)


class DIContainer:
    """依赖注入容器"""
    
    def __init__(self):
        self._instances: Dict[str, Any] = {}
        self._initialized = False
        logger.info("DIContainer initialized")
    
    def initialize(self):
        """初始化所有依赖"""
        if self._initialized:
            return
        
        try:
            logger.info("Initializing dependencies...")
            
            # 1. 创建模型管理器
            self._instances['embedding_manager'] = EmbeddingManager()
            self._instances['llm_manager'] = LLMManager()
            
            # 2. 创建向量存储管理器
            self._instances['vector_store_manager'] = ChromaVectorStoreManager(
                embedding_interface=self._instances['embedding_manager']
            )
            
            # 3. 创建检索编排器
            self._instances['retrieval_orchestrator'] = RetrievalOrchestrator()
            
            # 4. 创建服务
            self._instances['document_service'] = DocumentService(
                vector_store_manager=self._instances['vector_store_manager']
            )
            
            self._instances['query_service'] = QueryService(
                vector_store_manager=self._instances['vector_store_manager'],
                llm_manager=self._instances['llm_manager'],
                retrieval_orchestrator=self._instances['retrieval_orchestrator']
            )
            
            self._instances['system_service'] = SystemService(
                vector_store_manager=self._instances['vector_store_manager'],
                llm_manager=self._instances['llm_manager']
            )
            
            self._initialized = True
            logger.info("All dependencies initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize dependencies: {e}")
            raise
    
    def get_document_service(self) -> DocumentService:
        """获取文档服务"""
        if not self._initialized:
            self.initialize()
        return self._instances['document_service']
    
    def get_query_service(self) -> QueryService:
        """获取查询服务"""
        if not self._initialized:
            self.initialize()
        return self._instances['query_service']
    
    def get_system_service(self) -> SystemService:
        """获取系统服务"""
        if not self._initialized:
            self.initialize()
        return self._instances['system_service']
    
    def get_vector_store_manager(self) -> ChromaVectorStoreManager:
        """获取向量存储管理器"""
        if not self._initialized:
            self.initialize()
        return self._instances['vector_store_manager']
    
    def get_embedding_manager(self) -> EmbeddingManager:
        """获取嵌入管理器"""
        if not self._initialized:
            self.initialize()
        return self._instances['embedding_manager']
    
    def get_llm_manager(self) -> LLMManager:
        """获取LLM管理器"""
        if not self._initialized:
            self.initialize()
        return self._instances['llm_manager']
    
    def get_retrieval_orchestrator(self) -> RetrievalOrchestrator:
        """获取检索编排器"""
        if not self._initialized:
            self.initialize()
        return self._instances['retrieval_orchestrator']


# 全局容器实例
container = DIContainer()
