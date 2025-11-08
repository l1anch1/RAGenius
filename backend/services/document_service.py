"""
Document Service
文档服务实现
"""
import os
import io
from typing import Dict, Any
import logging
import threading

from interfaces.services import DocumentServiceInterface
from interfaces.vector_store import VectorStoreInterface

logger = logging.getLogger(__name__)


class DocumentService(DocumentServiceInterface):
    """文档服务实现 - 内存模式"""
    
    def __init__(self, vector_store_manager: VectorStoreInterface):
        """
        初始化文档服务
        
        Args:
            vector_store_manager: 向量存储管理器
        """
        self.vector_store_manager = vector_store_manager
        
        # 内存中的文档存储：{filename: file_content_bytes}
        self._in_memory_documents: Dict[str, bytes] = {}
        self._lock = threading.RLock()
        
        logger.info("DocumentService initialized (memory mode)")
    
    def get_documents(self) -> Dict[str, Any]:
        """获取文档列表（从内存）"""
        try:
            with self._lock:
                documents = sorted(list(self._in_memory_documents.keys()))
                logger.info(f"Found {len(documents)} documents in memory: {documents}")
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
    
    def upload_document(self, file) -> Dict[str, Any]:
        """上传文档到内存
        
        Args:
            file: Flask上传的文件对象
        
        Returns:
            上传结果
        """
        try:
            # 检查文件是否为空
            if not file or not file.filename:
                return {
                    "status": "error",
                    "message": "No file provided"
                }
            
            # 检查文件类型
            allowed_extensions = {'.pdf', '.txt', '.md', '.csv', '.docx', '.doc'}
            filename = file.filename
            file_ext = os.path.splitext(filename)[1].lower()
            
            if file_ext not in allowed_extensions:
                return {
                    "status": "error",
                    "message": f"Unsupported file type. Allowed types: {', '.join(sorted(allowed_extensions))}"
                }
            
            # 读取文件内容到内存
            # 重置文件指针到开头（以防之前被读取过）
            file.seek(0)
            file_content = file.read()
            
            # 验证文件内容不为空
            if not file_content:
                return {
                    "status": "error",
                    "message": "File is empty or could not be read"
                }
            
            with self._lock:
                # 检查文件是否已存在
                if filename in self._in_memory_documents:
                    return {
                        "status": "error",
                        "message": f"File '{filename}' already exists"
                    }
                
                # 保存到内存
                self._in_memory_documents[filename] = file_content
                logger.info(f"File uploaded to memory: {filename} ({len(file_content)} bytes)")
                logger.info(f"Total documents in memory: {len(self._in_memory_documents)}")
            
            return {
                "status": "success",
                "message": f"File '{filename}' uploaded successfully",
                "filename": filename
            }
            
        except Exception as e:
            logger.error(f"Failed to upload document: {e}")
            return {
                "status": "error",
                "message": f"Failed to upload document: {str(e)}"
            }
    
    def get_in_memory_documents(self) -> Dict[str, bytes]:
        """获取内存中的文档（供向量存储管理器使用）"""
        with self._lock:
            return self._in_memory_documents.copy()
    
    def rebuild_knowledge_base(self) -> Dict[str, Any]:
        """重建知识库（从内存中的文档）"""
        try:
            logger.info("Starting knowledge base rebuild from memory...")
            
            # 从内存获取文档
            in_memory_docs = self.get_in_memory_documents()
            
            logger.info(f"Found {len(in_memory_docs)} documents in memory: {list(in_memory_docs.keys())}")
            
            if not in_memory_docs:
                logger.warning("No documents in memory to rebuild")
                return {
                    "status": "error",
                    "message": "No documents in memory to rebuild. Please upload documents first."
                }
            
            # 使用内存文档重建向量存储
            success = self.vector_store_manager.rebuild_store_from_memory(in_memory_docs)
            
            if success:
                logger.info("Knowledge base rebuild completed successfully")
                return {
                    "status": "success",
                    "message": "Knowledge base rebuilt successfully"
                }
            else:
                logger.error("Knowledge base rebuild failed")
                import traceback
                logger.error(f"Rebuild traceback: {traceback.format_exc()}")
                return {
                    "status": "error",
                    "message": "Failed to rebuild knowledge base. Please check the logs for details."
                }
                
        except Exception as e:
            logger.error(f"Failed to rebuild knowledge base: {e}")
            import traceback
            logger.error(f"Exception traceback: {traceback.format_exc()}")
            return {
                "status": "error",
                "message": f"Failed to rebuild knowledge base: {str(e)}"
            }
