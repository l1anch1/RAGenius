"""
Vector Store Manager
向量存储管理器实现
"""
import os
import shutil
import stat
import time
import threading
from typing import Optional, Dict, Any, List
import logging

from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader, CSVLoader, TextLoader

from interfaces.vector_store import VectorStoreInterface, EmbeddingInterface
from managers.cache_manager import CacheManager
from config import VECTOR_DB_DIR, DOCUMENTS_DIR, CHUNK_SIZE, CHUNK_OVERLAP

logger = logging.getLogger(__name__)


class ChromaVectorStoreManager(VectorStoreInterface):
    """ChromaDB向量存储管理器"""
    
    def __init__(self, embedding_interface: EmbeddingInterface, documents_dir: str = DOCUMENTS_DIR):
        """
        初始化向量存储管理器
        
        Args:
            embedding_interface: 嵌入模型接口
            documents_dir: 文档目录路径
        """
        self.embedding_interface = embedding_interface
        self.documents_dir = documents_dir
        
        # 使用内存存储，不持久化
        self._vector_store = None
        self._vectorized_documents = []
        self._total_chunks = 0
        self._last_build_time = None
        
        self._lock = threading.RLock()
        logger.info(f"ChromaVectorStoreManager initialized with documents_dir: {documents_dir} (memory-only mode)")
    
    def get_store(self) -> Optional[Chroma]:
        """获取向量存储实例"""
        with self._lock:
            return self._vector_store
    
    def rebuild_store(self, documents_dir: str = None) -> bool:
        """
        重建向量存储 - 内存模式，每次重新创建
        
        Args:
            documents_dir: 文档目录路径，如果为None则使用默认路径
        
        Returns:
            重建是否成功
        """
        if documents_dir is None:
            documents_dir = self.documents_dir
            
        with self._lock:
            try:
                logger.info("Starting vector store rebuild (memory mode)...")
                
                # 1. 清除旧的内存存储
                self._vector_store = None
                self._vectorized_documents = []
                self._total_chunks = 0
                
                # 2. 加载文档
                logger.info(f"Loading documents from directory: {documents_dir}")
                documents = self._load_documents(documents_dir)
                if not documents:
                    logger.warning("No documents found to process")
                    return False
                
                logger.info(f"Successfully loaded {len(documents)} documents")
                
                # 3. 处理文档为chunks
                logger.info("Processing documents into chunks...")
                chunks = self._process_documents(documents)
                if not chunks:
                    logger.warning("No chunks generated from documents")
                    return False
                
                logger.info(f"Generated {len(chunks)} chunks from {len(documents)} documents")
                
                # 4. 获取嵌入模型
                logger.info("Creating new in-memory vector store...")
                embedding_model = self.embedding_interface.get_embeddings()
                if not embedding_model:
                    logger.error("Embedding model not available")
                    return False
                
                # 5. 创建内存向量存储（不持久化）
                self._vector_store = Chroma.from_documents(
                    documents=chunks,
                    embedding=embedding_model,
                    collection_name="documents"
                    # 不设置persist_directory，使用内存存储
                )
                
                # 6. 记录向量化的文档信息
                document_set = set()
                for chunk in chunks:
                    if hasattr(chunk, 'metadata') and 'source' in chunk.metadata:
                        source = chunk.metadata['source']
                        filename = os.path.basename(source)
                        if filename:
                            document_set.add(filename)
                
                self._vectorized_documents = sorted(list(document_set))
                self._total_chunks = len(chunks)
                import time
                self._last_build_time = time.time()
                
                logger.info(f"Successfully created in-memory vector store with:")
                logger.info(f"  - {self._total_chunks} chunks")
                logger.info(f"  - {len(self._vectorized_documents)} documents: {self._vectorized_documents}")
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to rebuild vector store: {e}")
                import traceback
                traceback.print_exc()
                return False
    
    def get_vectorized_documents(self) -> Dict[str, Any]:
        """获取已向量化的文档列表 - 内存模式"""
        with self._lock:
            if not self._vector_store:
                logger.info("No vector store available (memory mode)")
                return {"status": "success", "documents": [], "total_chunks": 0}
            
            logger.info(f"Returning cached vectorized documents: {len(self._vectorized_documents)} documents, {self._total_chunks} chunks")
            
            return {
                "status": "success", 
                "documents": self._vectorized_documents.copy(),
                "total_chunks": self._total_chunks
            }
    

    
    def is_available(self) -> bool:
        """检查向量存储是否可用"""
        with self._lock:
            return self._vector_store is not None
    

    

    
    def _load_documents(self, documents_dir: str) -> List[Any]:
        """加载文档"""
        documents = []
        
        if not os.path.exists(documents_dir):
            logger.error(f"Documents directory does not exist: {documents_dir}")
            return documents
        
        for filename in os.listdir(documents_dir):
            # 过滤系统文件
            if filename.startswith('.') or filename.startswith('~') or filename in ['.DS_Store', 'Thumbs.db', 'desktop.ini']:
                continue
            
            file_path = os.path.join(documents_dir, filename)
            if not os.path.isfile(file_path):
                continue
            
            try:
                logger.info(f"Processing file: {filename}")
                
                if filename.lower().endswith('.pdf'):
                    loader = PyPDFLoader(file_path)
                elif filename.lower().endswith('.csv'):
                    loader = CSVLoader(file_path)
                elif filename.lower().endswith(('.txt', '.md')):
                    loader = TextLoader(file_path)
                else:
                    logger.warning(f"Unsupported file type: {filename}")
                    continue
                
                docs = loader.load()
                documents.extend(docs)
                logger.info(f"Successfully loaded {len(docs)} pages from {filename}")
                
            except Exception as e:
                logger.error(f"Error loading {filename}: {e}")
                continue
        
        return documents
    
    def _process_documents(self, documents: List[Any]) -> List[Any]:
        """处理文档为chunks"""
        try:
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=CHUNK_SIZE,
                chunk_overlap=CHUNK_OVERLAP,
                length_function=len,
            )
            
            chunks = text_splitter.split_documents(documents)
            logger.info(f"Generated {len(chunks)} chunks")
            
            # 打印前几个chunks的信息用于调试
            for i, chunk in enumerate(chunks[:5]):
                logger.debug(f"Chunk #{i+1} (length {len(chunk.page_content)}):")
                logger.debug(chunk.page_content[:200] + "..." if len(chunk.page_content) > 200 else chunk.page_content)
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error processing documents: {e}")
            return []
    

