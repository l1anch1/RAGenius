"""
Interfaces Package
接口层 - 定义抽象接口
"""

from .services import QueryServiceInterface, DocumentServiceInterface, SystemServiceInterface
from .vector_store import VectorStoreInterface, EmbeddingInterface, LLMInterface

__all__ = [
    "QueryServiceInterface",
    "DocumentServiceInterface", 
    "SystemServiceInterface",
    "VectorStoreInterface",
    "EmbeddingInterface",
    "LLMInterface",
]
