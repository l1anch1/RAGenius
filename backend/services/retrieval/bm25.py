"""
BM25 Retriever
BM25 关键词检索器

这是一个底层工具类，被 services/retrieval/stages.py 使用。
"""
import logging
import threading
from typing import Any, Dict, List

from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class BM25Retriever:
    """
    BM25 关键词检索器
    
    基于 rank_bm25 实现的关键词检索，支持中英文分词。
    """
    
    def __init__(self, documents: List[Document] = None):
        """
        初始化 BM25 检索器
        
        Args:
            documents: 初始文档列表
        """
        self._documents: List[Document] = documents or []
        self._bm25 = None
        self._tokenized_corpus = None
        self._lock = threading.Lock()
        
        if documents:
            self._build_index()
    
    def _tokenize(self, text: str) -> List[str]:
        """
        简单分词（支持中英文）
        
        - 中文：按字分词
        - 英文：按单词分词
        - 数字：保持完整
        """
        import re
        pattern = r'[\u4e00-\u9fff]|[a-zA-Z]+|[0-9]+'
        return re.findall(pattern, text.lower())
    
    def _build_index(self):
        """构建 BM25 索引"""
        if not self._documents:
            return
        
        try:
            from rank_bm25 import BM25Okapi
            
            self._tokenized_corpus = [
                self._tokenize(doc.page_content) 
                for doc in self._documents
            ]
            self._bm25 = BM25Okapi(self._tokenized_corpus)
            logger.info(f"BM25 index built with {len(self._documents)} documents")
            
        except ImportError:
            logger.error("rank_bm25 not installed. Run: pip install rank-bm25")
            self._bm25 = None
        except Exception as e:
            logger.error(f"Failed to build BM25 index: {e}")
            self._bm25 = None
    
    def update_documents(self, documents: List[Document]):
        """更新文档并重建索引"""
        with self._lock:
            self._documents = documents
            self._bm25 = None
            self._tokenized_corpus = None
            self._build_index()
    
    def retrieve(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        BM25 检索
        
        Args:
            query: 查询文本
            top_k: 返回的文档数量
        
        Returns:
            List[Dict]: 包含 document 和 score 的字典列表
        """
        with self._lock:
            if self._bm25 is None:
                self._build_index()
            
            if self._bm25 is None or not self._documents:
                return []
        
        try:
            tokenized_query = self._tokenize(query)
            scores = self._bm25.get_scores(tokenized_query)
            
            # 按分数排序
            scored_indices = sorted(
                enumerate(scores), 
                key=lambda x: x[1], 
                reverse=True
            )[:top_k]
            
            results = []
            for idx, score in scored_indices:
                if score > 0:
                    results.append({
                        "document": self._documents[idx],
                        "score": float(score)
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"BM25 retrieval failed: {e}")
            return []
    
    @property
    def document_count(self) -> int:
        """获取索引中的文档数量"""
        return len(self._documents)

