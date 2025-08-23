"""
Document Service
文档服务实现
"""
import os
from typing import Dict, Any
import logging

from interfaces.services import DocumentServiceInterface
from interfaces.vector_store import VectorStoreInterface
from config import DOCUMENTS_DIR

logger = logging.getLogger(__name__)


class DocumentService(DocumentServiceInterface):
    """文档服务实现"""
    
    def __init__(self, vector_store_manager: VectorStoreInterface):
        """
        初始化文档服务
        
        Args:
            vector_store_manager: 向量存储管理器
        """
        self.vector_store_manager = vector_store_manager
        self.documents_dir = DOCUMENTS_DIR
        logger.info("DocumentService initialized")
    
    def get_documents(self) -> Dict[str, Any]:
        """获取文档列表"""
        try:
            if not os.path.exists(self.documents_dir):
                logger.warning(f"Documents directory does not exist: {self.documents_dir}")
                return {"status": "success", "documents": []}
            
            documents = []
            for filename in os.listdir(self.documents_dir):
                # 过滤系统文件和隐藏文件
                if (filename.startswith('.') or 
                    filename.startswith('~') or 
                    filename in ['.DS_Store', 'Thumbs.db', 'desktop.ini']):
                    continue
                
                file_path = os.path.join(self.documents_dir, filename)
                if os.path.isfile(file_path):
                    # 为了与前端兼容，只返回文件名字符串
                    documents.append(filename)
            
            logger.debug(f"Found {len(documents)} documents")
            return {"status": "success", "documents": documents}
            
        except Exception as e:
            logger.error(f"Failed to get documents: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_vectorized_documents(self) -> Dict[str, Any]:
        """获取已向量化的文档列表"""
        try:
            return self.vector_store_manager.get_vectorized_documents()
        except Exception as e:
            logger.error(f"Failed to get vectorized documents: {e}")
            return {"status": "error", "message": str(e)}
    
    def rebuild_knowledge_base(self) -> Dict[str, Any]:
        """重建知识库"""
        try:
            logger.info("Starting knowledge base rebuild...")
            
            success = self.vector_store_manager.rebuild_store(self.documents_dir)
            
            if success:
                logger.info("Knowledge base rebuild completed successfully")
                return {
                    "status": "success",
                    "message": "Knowledge base rebuilt successfully"
                }
            else:
                logger.error("Knowledge base rebuild failed")
                return {
                    "status": "error",
                    "message": "Failed to rebuild knowledge base"
                }
                
        except Exception as e:
            logger.error(f"Failed to rebuild knowledge base: {e}")
            return {
                "status": "error",
                "message": f"Failed to rebuild knowledge base: {str(e)}"
            }
