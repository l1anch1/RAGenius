"""
Retrieval Pipeline Stages
检索流水线各阶段定义

每个 Stage 是独立的、可插拔的处理单元，遵循统一接口。
"""
import os
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from langchain_core.documents import Document

logger = logging.getLogger(__name__)


# =============================================================================
# 数据结构
# =============================================================================

@dataclass
class ScoredDocument:
    """带分数的文档"""
    document: Document
    score: float
    source: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def page_content(self) -> str:
        return self.document.page_content
    
    @property
    def doc_metadata(self) -> Dict[str, Any]:
        return self.document.metadata


@dataclass
class RetrievalContext:
    """
    检索上下文 - 在各阶段之间传递的数据容器
    
    每个阶段读取需要的数据，写入产出的数据，
    形成数据流：query → expanded_queries → retrieved_docs → fused_docs → ...
    """
    # 输入
    original_query: str
    
    # 各阶段产出
    expanded_queries: List[str] = field(default_factory=list)
    retrieved_results: Dict[str, Dict[str, List[ScoredDocument]]] = field(default_factory=dict)
    fused_documents: List[ScoredDocument] = field(default_factory=list)
    reranked_documents: List[ScoredDocument] = field(default_factory=list)
    truncated_documents: List[ScoredDocument] = field(default_factory=list)  # 智能截断后
    final_documents: List[ScoredDocument] = field(default_factory=list)
    
    # 置信度标记
    low_confidence: bool = False  # 是否低置信度（没有高相关文档）
    
    # 元数据（各阶段的统计信息）
    stage_metadata: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def to_langchain_documents(self) -> List[Document]:
        """转换为 LangChain Document 列表"""
        return [sd.document for sd in self.final_documents]


# =============================================================================
# Stage 基类
# =============================================================================

class RetrievalStage(ABC):
    """
    检索阶段基类
    
    所有阶段必须实现:
    - name: 阶段名称
    - execute(): 执行逻辑
    - is_enabled(): 是否启用
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """阶段名称"""
        pass
    
    @abstractmethod
    def execute(self, context: RetrievalContext) -> RetrievalContext:
        """
        执行阶段逻辑
        
        Args:
            context: 检索上下文（包含前序阶段的产出）
        
        Returns:
            更新后的检索上下文
        """
        pass
    
    @abstractmethod
    def is_enabled(self) -> bool:
        """该阶段是否启用"""
        pass
    
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置（用于 API 展示）"""
        return {}
    
    def update_config(self, **kwargs):
        """更新配置"""
        pass


# =============================================================================
# Stage 实现
# =============================================================================

class QueryExpansionStage(RetrievalStage):
    """
    查询扩展阶段
    
    使用 QueryExpansionLLMManager 管理的轻量 LLM（如 gpt-4o-mini）
    生成多角度查询，提高召回率。
    
    注意：即使 enabled=False，阶段仍然执行，只是返回原始查询。
    这确保 expanded_queries 始终有值。
    """
    
    def __init__(self):
        from config import (
            QUERY_EXPANSION_ENABLED,
            QUERY_EXPANSION_N_SUBQUERIES,
            QUERY_EXPANSION_INCLUDE_ORIGINAL
        )
        
        self._llm_manager = None  # 延迟初始化
        self.enabled = QUERY_EXPANSION_ENABLED
        self.n_subqueries = QUERY_EXPANSION_N_SUBQUERIES
        self.include_original = QUERY_EXPANSION_INCLUDE_ORIGINAL
        
        from config import QUERY_EXPANSION_PROMPT_TEMPLATE
        self._prompt_template = QUERY_EXPANSION_PROMPT_TEMPLATE
    
    @property
    def name(self) -> str:
        return "Query Expansion"
    
    def is_enabled(self) -> bool:
        # 始终返回 True，确保 expanded_queries 被设置
        # 实际扩展逻辑在 execute 中根据 self.enabled 判断
        return True
    
    def execute(self, context: RetrievalContext) -> RetrievalContext:
        from managers.timing import timed
        
        logger.info(f"[QueryExpansion] Input: \"{context.original_query}\"")
        
        @timed("Query Expansion")
        def _do_expand():
            if not self.enabled:
                logger.info("[QueryExpansion] ⏭ Disabled, using original query only")
                return [context.original_query]
            
            queries = []
            if self.include_original:
                queries.append(context.original_query)
            
            try:
                llm = self._get_llm()
                if llm is None:
                    return [context.original_query]
                
                prompt = self._prompt_template.format(
                    n=self.n_subqueries,
                    query=context.original_query
                )
                
                response = llm.invoke(prompt)
                content = response.content if hasattr(response, 'content') else str(response)
                
                new_queries = [q.strip() for q in content.strip().split('\n') if q.strip()]
                for q in new_queries[:self.n_subqueries]:
                    if q and q not in queries:
                        queries.append(q)
                
            except Exception as e:
                logger.error(f"Query expansion failed: {e}")
                if context.original_query not in queries:
                    queries.append(context.original_query)
            
            return queries
        
        context.expanded_queries = _do_expand()
        
        # 打印扩展的查询
        logger.info(f"[QueryExpansion] Output: {len(context.expanded_queries)} queries")
        for i, q in enumerate(context.expanded_queries, 1):
            logger.info(f"    {i}. {q}")
        
        context.stage_metadata["query_expansion"] = {
            "n_queries": len(context.expanded_queries),
            "queries": context.expanded_queries
        }
        return context
    
    def _get_llm(self) -> Any:
        """通过 Manager 获取 LLM（统一管理、带缓存）"""
        if self._llm_manager is None:
            from managers import QueryExpansionLLMManager
            self._llm_manager = QueryExpansionLLMManager()
        return self._llm_manager.get_llm()
    
    def get_config(self) -> Dict[str, Any]:
        from config import QUERY_EXPANSION_MODEL
        return {
            "enabled": self.enabled,
            "n_subqueries": self.n_subqueries,
            "model": QUERY_EXPANSION_MODEL
        }
    
    def update_config(self, **kwargs):
        if 'enabled' in kwargs:
            self.enabled = kwargs['enabled']
        if 'n_subqueries' in kwargs:
            self.n_subqueries = kwargs['n_subqueries']


class HybridRetrievalStage(RetrievalStage):
    """混合检索阶段 (Embedding + BM25)"""
    
    def __init__(self, vector_store: Any = None):
        from config import HYBRID_TOP_K_PER_QUERY
        from concurrent.futures import ThreadPoolExecutor
        
        self._vector_store = vector_store
        self._bm25_retriever = None
        self._documents_hash = None
        
        self.top_k_per_query = HYBRID_TOP_K_PER_QUERY
        
        self._query_executor = ThreadPoolExecutor(max_workers=8)
        self._retrieval_executor = ThreadPoolExecutor(max_workers=4)
    
    @property
    def name(self) -> str:
        return "Hybrid Retrieval"
    
    def is_enabled(self) -> bool:
        return True  # 检索阶段始终启用
    
    def set_vector_store(self, vector_store: Any):
        self._vector_store = vector_store
        self._rebuild_bm25_index()
    
    def execute(self, context: RetrievalContext) -> RetrievalContext:
        from managers.timing import timed
        
        @timed("Hybrid Retrieval")
        def _do_retrieve():
            queries = context.expanded_queries or [context.original_query]
            
            futures = {}
            for query in queries:
                futures[query] = self._query_executor.submit(self._retrieve_single, query)
            
            all_results = {}
            for query, future in futures.items():
                try:
                    all_results[query] = future.result(timeout=60)
                except Exception as e:
                    logger.error(f"Retrieval failed for '{query}': {e}")
                    all_results[query] = {"embedding": [], "bm25": []}
            
            return all_results
        
        context.retrieved_results = _do_retrieve()
        
        total_embedding = sum(len(r.get("embedding", [])) for r in context.retrieved_results.values())
        total_bm25 = sum(len(r.get("bm25", [])) for r in context.retrieved_results.values())
        
        # 打印检索结果摘要
        logger.info(f"[HybridRetrieval] Output: {total_embedding} embedding + {total_bm25} BM25")
        for query, results in context.retrieved_results.items():
            emb_count = len(results.get("embedding", []))
            bm25_count = len(results.get("bm25", []))
            short_query = query[:35] + "..." if len(query) > 35 else query
            logger.info(f"    → \"{short_query}\": emb={emb_count}, bm25={bm25_count}")
        
        context.stage_metadata["hybrid_retrieval"] = {
            "total_embedding_results": total_embedding,
            "total_bm25_results": total_bm25
        }
        return context
    
    def _retrieve_single(self, query: str) -> Dict[str, List[ScoredDocument]]:
        """单个查询的混合检索"""
        results = {}
        try:
            embedding_future = self._retrieval_executor.submit(self._embedding_retrieve, query)
            bm25_future = self._retrieval_executor.submit(self._bm25_retrieve, query)
            
            results["embedding"] = embedding_future.result(timeout=30)
            results["bm25"] = bm25_future.result(timeout=30)
        except Exception as e:
            logger.error(f"Parallel retrieval failed: {e}")
            results["embedding"] = self._embedding_retrieve(query)
            results["bm25"] = self._bm25_retrieve(query)
        return results
    
    def _embedding_retrieve(self, query: str) -> List[ScoredDocument]:
        if self._vector_store is None:
            return []
        try:
            results = self._vector_store.similarity_search_with_score(query, k=self.top_k_per_query)
            return [
                ScoredDocument(document=doc, score=1/(1+score), source="embedding")
                for doc, score in results
            ]
        except Exception as e:
            logger.error(f"Embedding retrieval failed: {e}")
            return []
    
    def _bm25_retrieve(self, query: str) -> List[ScoredDocument]:
        if self._bm25_retriever is None:
            self._rebuild_bm25_index()
        if self._bm25_retriever is None:
            return []
        
        # BM25Retriever 返回 Dict 列表，需要转换为 ScoredDocument
        results = self._bm25_retriever.retrieve(query, self.top_k_per_query)
        return [
            ScoredDocument(document=r["document"], score=r["score"], source="bm25")
            for r in results
        ]
    
    def _rebuild_bm25_index(self):
        """重建 BM25 索引"""
        if self._vector_store is None:
            return
        try:
            from .bm25 import BM25Retriever
            
            collection = self._vector_store._collection
            results = collection.get(include=["documents", "metadatas"])
            
            if not results or not results.get("documents"):
                return
            
            documents = []
            for i, doc_content in enumerate(results["documents"]):
                metadata = results["metadatas"][i] if results.get("metadatas") else {}
                documents.append(Document(page_content=doc_content, metadata=metadata))
            
            new_hash = hash(tuple(d.page_content[:100] for d in documents[:100]))
            if new_hash == self._documents_hash:
                return
            
            self._documents_hash = new_hash
            self._bm25_retriever = BM25Retriever(documents)
            
        except Exception as e:
            logger.error(f"Failed to rebuild BM25 index: {e}")
    
    def get_config(self) -> Dict[str, Any]:
        return {"top_k_per_query": self.top_k_per_query}
    
    def update_config(self, **kwargs):
        if 'top_k_per_query' in kwargs:
            self.top_k_per_query = kwargs['top_k_per_query']


class RRFFusionStage(RetrievalStage):
    """RRF 融合阶段"""
    
    def __init__(self):
        from config import RRF_K, RRF_TOP_K
        
        self.k = RRF_K
        self.top_k = RRF_TOP_K
    
    @property
    def name(self) -> str:
        return "RRF Fusion"
    
    def is_enabled(self) -> bool:
        return True
    
    def execute(self, context: RetrievalContext) -> RetrievalContext:
        from managers.timing import timed
        from collections import defaultdict
        
        @timed("RRF Fusion")
        def _do_fuse():
            # 扁平化结果
            flattened = {}
            for query, strategy_results in context.retrieved_results.items():
                for strategy, docs in strategy_results.items():
                    key = f"{query[:30]}_{strategy}"
                    flattened[key] = docs
            
            # RRF 计算
            doc_scores = defaultdict(lambda: {"score": 0.0, "doc": None, "sources": []})
            
            for source_name, doc_list in flattened.items():
                for rank, scored_doc in enumerate(doc_list, start=1):
                    doc_key = (scored_doc.page_content[:400], scored_doc.doc_metadata.get('source', ''))
                    rrf_score = 1.0 / (self.k + rank)
                    
                    doc_scores[doc_key]["score"] += rrf_score
                    doc_scores[doc_key]["sources"].append(source_name)
                    if doc_scores[doc_key]["doc"] is None:
                        doc_scores[doc_key]["doc"] = scored_doc.document
            
            # 排序
            sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1]["score"], reverse=True)
            
            return [
                ScoredDocument(
                    document=doc_info["doc"],
                    score=doc_info["score"],
                    source="rrf_fusion",
                    metadata={"original_sources": doc_info["sources"]}
                )
                for _, doc_info in sorted_docs[:self.top_k]
            ]
        
        context.fused_documents = _do_fuse()
        
        # 打印 RRF 融合结果
        logger.info(f"[RRFFusion] Output: {len(context.fused_documents)} documents (top 5 shown)")
        for i, doc in enumerate(context.fused_documents[:5], 1):
            source = os.path.basename(doc.doc_metadata.get('source', 'unknown'))
            preview = doc.page_content[:400].replace('\n', ' ')
            logger.info(f"    {i}. [{doc.score:.4f}] {source}")
            logger.info(f"       {preview}...")
        
        context.stage_metadata["rrf_fusion"] = {"n_results": len(context.fused_documents)}
        return context
    
    def get_config(self) -> Dict[str, Any]:
        return {"k": self.k, "top_k": self.top_k}
    
    def update_config(self, **kwargs):
        if 'k' in kwargs:
            self.k = kwargs['k']
        if 'top_k' in kwargs:
            self.top_k = kwargs['top_k']


class RerankingStage(RetrievalStage):
    """
    Cross-Encoder 重排阶段
    
    使用 RerankingModelManager 管理的 CrossEncoder 模型进行精排。
    
    注意：即使 enabled=False，阶段仍然执行，只是跳过实际重排逻辑，
    将 fused_documents 传递给下游。这确保数据流不会中断。
    """
    
    def __init__(self):
        from config import RERANKING_ENABLED, RERANKING_MODEL, RERANKING_TOP_K, RERANKING_BATCH_SIZE
        
        self._model_manager = None  # 延迟初始化
        self.enabled = RERANKING_ENABLED
        self.model_name = RERANKING_MODEL
        self.top_k = RERANKING_TOP_K
        self.batch_size = RERANKING_BATCH_SIZE
    
    @property
    def name(self) -> str:
        return "Cross-Encoder Reranking"
    
    def is_enabled(self) -> bool:
        # 始终返回 True，确保数据流不中断
        # 实际的重排逻辑在 execute 中根据 self.enabled 判断
        return True
    
    def execute(self, context: RetrievalContext) -> RetrievalContext:
        from managers.timing import timed
        
        @timed("Cross-Encoder Reranking")
        def _do_rerank():
            documents = context.fused_documents
            
            if not self.enabled or not documents:
                return documents[:self.top_k] if documents else []
            
            model = self._get_model()
            if model is None:
                return documents[:self.top_k]
            
            try:
                pairs = [(context.original_query, doc.page_content) for doc in documents]
                scores = model.predict(pairs, batch_size=self.batch_size, show_progress_bar=False)
                
                scored_docs = [
                    ScoredDocument(
                        document=doc.document,
                        score=float(score),
                        source="reranker",
                        metadata={**doc.metadata, "original_score": doc.score}
                    )
                    for doc, score in zip(documents, scores)
                ]
                scored_docs.sort(key=lambda x: x.score, reverse=True)
                return scored_docs[:self.top_k]
                
            except Exception as e:
                logger.error(f"Reranking failed: {e}")
                return documents[:self.top_k]
        
        context.reranked_documents = _do_rerank()
        
        # 打印重排结果
        status = "✓" if self.enabled else "⏭ disabled"
        logger.info(f"[Reranking] {status} Output: {len(context.reranked_documents)} documents (top 5 shown)")
        for i, doc in enumerate(context.reranked_documents[:5], 1):
            source = os.path.basename(doc.doc_metadata.get('source', 'unknown'))
            preview = doc.page_content[:400].replace('\n', ' ')
            logger.info(f"    {i}. [{doc.score:.4f}] {source}")
            logger.info(f"       {preview}...")
        
        context.stage_metadata["reranking"] = {
            "n_results": len(context.reranked_documents),
            "enabled": self.enabled
        }
        return context
    
    def _get_model(self):
        """通过 Manager 获取模型（统一管理、带缓存）"""
        if self._model_manager is None:
            from managers import RerankingModelManager
            self._model_manager = RerankingModelManager()
        return self._model_manager.get_model()
    
    def get_config(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "model": self.model_name,
            "top_k": self.top_k
        }
    
    def update_config(self, **kwargs):
        if 'enabled' in kwargs:
            self.enabled = kwargs['enabled']
        if 'top_k' in kwargs:
            self.top_k = kwargs['top_k']


class ScoreTruncationStage(RetrievalStage):
    """
    智能分数截断阶段
    
    使用双重保护机制过滤低相关文档：
    1. 相对分数差截断：检测分数"断崖"，在大差距处截断
    2. 绝对分数下限：过滤掉分数过低的文档
    3. 保底策略：至少返回 top-1，并标记 low_confidence
    """
    
    def __init__(self):
        from config import (
            SCORE_TRUNCATION_ENABLED,
            SCORE_GAP_THRESHOLD,
            SCORE_MIN_THRESHOLD
        )
        
        self.enabled = SCORE_TRUNCATION_ENABLED
        self.gap_threshold = SCORE_GAP_THRESHOLD
        self.min_threshold = SCORE_MIN_THRESHOLD
    
    @property
    def name(self) -> str:
        return "Score Truncation"
    
    def is_enabled(self) -> bool:
        return True  # 始终执行，内部判断是否实际截断
    
    def execute(self, context: RetrievalContext) -> RetrievalContext:
        from managers.timing import timed
        
        @timed("Score Truncation")
        def _do_truncate():
            documents = context.reranked_documents
            
            if not documents:
                return [], True  # 空文档，低置信度
            
            if not self.enabled:
                # 未启用截断，直接传递
                return documents, False
            
            # Step 1: 绝对分数过滤
            filtered = [d for d in documents if d.score > self.min_threshold]
            
            # Step 2: 相对分数差截断（检测断崖）
            result = []
            for i, doc in enumerate(filtered):
                result.append(doc)
                if i < len(filtered) - 1:
                    gap = filtered[i].score - filtered[i + 1].score
                    if gap > self.gap_threshold:
                        logger.info(f"[ScoreTruncation] Gap detected: {filtered[i].score:.2f} → {filtered[i+1].score:.2f} (gap={gap:.2f} > {self.gap_threshold})")
                        break
            
            # Step 3: 保底策略
            if not result:
                # 没有通过过滤的文档，返回 top-1 + 低置信度
                logger.info(f"[ScoreTruncation] No docs passed filters, fallback to top-1 with low_confidence")
                return [documents[0]], True
            
            # 检查是否所有文档都是低分
            top_score = result[0].score if result else 0
            low_confidence = top_score < self.min_threshold
            
            return result, low_confidence
        
        truncated, low_confidence = _do_truncate()
        context.truncated_documents = truncated
        context.low_confidence = low_confidence
        
        # 打印截断结果
        original_count = len(context.reranked_documents)
        truncated_count = len(truncated)
        confidence_str = "⚠ LOW CONFIDENCE" if low_confidence else "✓ normal"
        
        logger.info(f"[ScoreTruncation] {original_count} → {truncated_count} documents ({confidence_str})")
        if truncated_count < original_count:
            logger.info(f"[ScoreTruncation] Removed {original_count - truncated_count} low-relevance documents")
        
        context.stage_metadata["score_truncation"] = {
            "original_count": original_count,
            "truncated_count": truncated_count,
            "low_confidence": low_confidence,
            "gap_threshold": self.gap_threshold,
            "min_threshold": self.min_threshold
        }
        
        return context
    
    def get_config(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "gap_threshold": self.gap_threshold,
            "min_threshold": self.min_threshold
        }
    
    def update_config(self, **kwargs):
        if 'enabled' in kwargs:
            self.enabled = kwargs['enabled']
        if 'gap_threshold' in kwargs:
            self.gap_threshold = kwargs['gap_threshold']
        if 'min_threshold' in kwargs:
            self.min_threshold = kwargs['min_threshold']


class MMRStage(RetrievalStage):
    """
    MMR 多样性后处理阶段
    
    注意：作为流水线的最后一个阶段，必须始终执行以设置 final_documents。
    mode="never" 时跳过 MMR 逻辑，直接截取。
    """
    
    def __init__(self, embedding_function=None):
        from config import MMR_MODE, MMR_SIMILARITY_THRESHOLD, MMR_LAMBDA, MMR_FINAL_K
        
        self._embedding_function = embedding_function
        self.mode = MMR_MODE  # auto | always | never
        self.similarity_threshold = MMR_SIMILARITY_THRESHOLD
        self.lambda_mult = MMR_LAMBDA
        self.final_k = MMR_FINAL_K
    
    @property
    def name(self) -> str:
        return "MMR Post-processing"
    
    def is_enabled(self) -> bool:
        # 始终返回 True，因为这是最后一个阶段，必须设置 final_documents
        return True
    
    def set_embedding_function(self, fn):
        self._embedding_function = fn
    
    def execute(self, context: RetrievalContext) -> RetrievalContext:
        from managers.timing import timed
        import numpy as np
        
        @timed("MMR Post-processing")
        def _do_mmr():
            # 使用截断后的文档（如果有），否则使用重排后的文档
            documents = context.truncated_documents if context.truncated_documents else context.reranked_documents
            
            if not documents:
                return []
            
            if self.mode == "never":
                return documents[:self.final_k]
            
            # 如果文档数量已经很少，跳过 MMR
            if len(documents) <= 2:
                logger.info(f"[MMR] Only {len(documents)} documents, skipping MMR")
                return documents[:self.final_k]
            
            embedding_fn = self._get_embedding_function()
            if embedding_fn is None:
                return documents[:self.final_k]
            
            should_apply = self.mode == "always"
            avg_sim = 0.0
            
            if self.mode == "auto":
                avg_sim = self._compute_avg_similarity(documents, embedding_fn)
                should_apply = avg_sim > self.similarity_threshold
                logger.info(f"[MMR] Auto-check: avg_similarity={avg_sim:.4f}, threshold={self.similarity_threshold}")
                if should_apply:
                    logger.info(f"[MMR] → Similarity {avg_sim:.4f} > {self.similarity_threshold}, applying MMR")
                else:
                    logger.info(f"[MMR] → Similarity {avg_sim:.4f} ≤ {self.similarity_threshold}, skipping MMR")
            
            if should_apply:
                return self._apply_mmr(documents, embedding_fn)
            else:
                return documents[:self.final_k]
        
        context.final_documents = _do_mmr()
        
        # 打印最终结果（这些将输入到 LLM）
        logger.info(f"[MMR] mode={self.mode} → Final: {len(context.final_documents)} documents for LLM")
        logger.info("─" * 50)
        for i, doc in enumerate(context.final_documents, 1):
            source = os.path.basename(doc.doc_metadata.get('source', 'unknown'))
            preview = doc.page_content[:400].replace('\n', ' ')
            logger.info(f"  📄 {i}. [{doc.score:.4f}] {source}")
            logger.info(f"     {preview}...")
        logger.info("─" * 50)
        
        context.stage_metadata["mmr"] = {
            "n_results": len(context.final_documents),
            "mode": self.mode
        }
        return context
    
    def _get_embedding_function(self):
        """获取 embedding 函数（由 orchestrator 注入）"""
        if self._embedding_function is None:
            logger.warning("Embedding function not set, MMR will use simple truncation")
        return self._embedding_function
    
    def _compute_avg_similarity(self, documents, embedding_fn) -> float:
        import numpy as np
        if len(documents) < 2:
            return 0.0
        try:
            embeddings = [np.array(embedding_fn(doc.page_content)) for doc in documents[:10]]
            similarities = []
            for i in range(len(embeddings)):
                for j in range(i + 1, len(embeddings)):
                    sim = np.dot(embeddings[i], embeddings[j]) / (
                        np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[j])
                    )
                    similarities.append(sim)
            return float(np.mean(similarities)) if similarities else 0.0
        except:
            return 0.0
    
    def _apply_mmr(self, documents, embedding_fn) -> List[ScoredDocument]:
        import numpy as np
        
        if len(documents) <= self.final_k:
            return documents
        
        try:
            doc_embeddings = [np.array(embedding_fn(doc.page_content)) for doc in documents]
            
            selected = [0]
            remaining = list(range(1, len(documents)))
            
            while len(selected) < self.final_k and remaining:
                best_score, best_idx = float('-inf'), None
                
                for idx in remaining:
                    relevance = documents[idx].score
                    max_sim = max(
                        np.dot(doc_embeddings[idx], doc_embeddings[sel]) / (
                            np.linalg.norm(doc_embeddings[idx]) * np.linalg.norm(doc_embeddings[sel])
                        )
                        for sel in selected
                    )
                    mmr_score = self.lambda_mult * relevance - (1 - self.lambda_mult) * max_sim
                    
                    if mmr_score > best_score:
                        best_score, best_idx = mmr_score, idx
                
                if best_idx is not None:
                    selected.append(best_idx)
                    remaining.remove(best_idx)
                else:
                    break
            
            return [
                ScoredDocument(
                    document=documents[i].document,
                    score=documents[i].score,
                    source="mmr",
                    metadata={**documents[i].metadata, "mmr_selected": True}
                )
                for i in selected
            ]
        except Exception as e:
            logger.error(f"MMR failed: {e}")
            return documents[:self.final_k]
    
    def get_config(self) -> Dict[str, Any]:
        return {
            "enabled": self.mode != "never",
            "mode": self.mode,
            "similarity_threshold": self.similarity_threshold,
            "lambda_mult": self.lambda_mult,
            "final_k": self.final_k
        }
    
    def update_config(self, **kwargs):
        if 'mode' in kwargs and kwargs['mode'] in ("auto", "always", "never"):
            self.mode = kwargs['mode']
        if 'similarity_threshold' in kwargs:
            self.similarity_threshold = kwargs['similarity_threshold']
        if 'lambda_mult' in kwargs:
            self.lambda_mult = kwargs['lambda_mult']
        if 'final_k' in kwargs:
            self.final_k = kwargs['final_k']

