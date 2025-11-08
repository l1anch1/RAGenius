"""
Vector Store Interface
定义向量存储的抽象接口
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class VectorStoreInterface(ABC):
    """向量存储接口"""
    
    @abstractmethod
    def get_store(self) -> Optional[Any]:
        """获取向量存储实例"""
        pass
    
    @abstractmethod
    def rebuild_store(self, documents_dir: str) -> bool:
        """重建向量存储（从文件系统）"""
        pass
    
    @abstractmethod
    def rebuild_store_from_memory(self, in_memory_documents: Dict[str, bytes]) -> bool:
        """从内存文档重建向量存储
        
        Args:
            in_memory_documents: 内存中的文档字典 {filename: file_content_bytes}
        """
        pass
    
    @abstractmethod
    def get_vectorized_documents(self) -> Dict[str, Any]:
        """获取已向量化的文档列表"""
        pass
    

    
    @abstractmethod
    def is_available(self) -> bool:
        """检查向量存储是否可用"""
        pass


class EmbeddingInterface(ABC):
    """嵌入模型接口"""
    
    @abstractmethod
    def get_embeddings(self) -> Optional[Any]:
        """获取嵌入模型"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """检查嵌入模型是否可用"""
        pass


class LLMInterface(ABC):
    """大语言模型接口"""
    
    @abstractmethod
    def get_llm(self) -> Optional[Any]:
        """获取LLM模型"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """检查LLM是否可用"""
        pass
