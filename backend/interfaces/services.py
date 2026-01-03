"""
Service Interfaces
定义服务层的抽象接口
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class DocumentServiceInterface(ABC):
    """文档服务接口"""
    
    @abstractmethod
    def get_documents(self) -> Dict[str, Any]:
        """获取文档列表"""
        pass
    
    @abstractmethod
    def get_vectorized_documents(self) -> Dict[str, Any]:
        """获取已向量化的文档列表"""
        pass
    
    @abstractmethod
    def upload_document(self, file: Any) -> Dict[str, Any]:
        """上传文档
        
        Args:
            file: 上传的文件对象
        """
        pass
    
    @abstractmethod
    def rebuild_knowledge_base(self) -> Dict[str, Any]:
        """重建知识库"""
        pass
    
    @abstractmethod
    def delete_document(self, filename: str) -> Dict[str, Any]:
        """删除单个文档
        
        Args:
            filename: 要删除的文件名
        """
        pass
    
    @abstractmethod
    def clear_all_documents(self) -> Dict[str, Any]:
        """清空所有文档"""
        pass


class QueryServiceInterface(ABC):
    """查询服务接口"""
    
    @abstractmethod
    def process_query(self, query: str) -> Dict[str, Any]:
        """处理查询请求"""
        pass
    
    @abstractmethod
    def process_stream_query(self, query: str):
        """处理流式查询请求"""
        pass


class SystemServiceInterface(ABC):
    """系统服务接口"""
    
    @abstractmethod
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        pass
    
    @abstractmethod
    def is_initialized(self) -> bool:
        """检查系统是否已初始化"""
        pass
