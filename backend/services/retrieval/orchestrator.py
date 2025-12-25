"""
Retrieval Orchestrator
检索编排器 - 负责按顺序执行各阶段

职责清晰分离:
- Orchestrator: 管理阶段列表、按顺序执行、收集统计
- Stage: 单一阶段的具体逻辑
"""
import logging
import time
from typing import Any, Dict, List, Optional

from langchain_core.documents import Document

from .stages import (
    RetrievalStage,
    RetrievalContext,
    QueryExpansionStage,
    HybridRetrievalStage,
    RRFFusionStage,
    RerankingStage,
    ScoreTruncationStage,
    MMRStage,
)
from managers.timing import pipeline_start, pipeline_end, get_timing_summary

logger = logging.getLogger(__name__)


class RetrievalOrchestrator:
    """
    检索编排器
    
    管理检索流水线的各个阶段，按顺序执行:
    1. Query Expansion (可选)
    2. Hybrid Retrieval
    3. RRF Fusion
    4. Reranking (可选)
    5. Score Truncation (智能分数截断)
    6. MMR Post-processing (可选)
    
    Usage:
        orchestrator = RetrievalOrchestrator()
        orchestrator.set_vector_store(vector_store)
        
        context = orchestrator.retrieve("如何使用Python？")
        documents = context.to_langchain_documents()
    """
    
    def __init__(self):
        """初始化编排器和默认阶段"""
        # 创建各阶段实例
        self._query_expansion = QueryExpansionStage()
        self._hybrid_retrieval = HybridRetrievalStage()
        self._rrf_fusion = RRFFusionStage()
        self._reranking = RerankingStage()
        self._score_truncation = ScoreTruncationStage()
        self._mmr = MMRStage()
        
        # 阶段列表（有序）
        self._stages: List[RetrievalStage] = [
            self._query_expansion,
            self._hybrid_retrieval,
            self._rrf_fusion,
            self._reranking,
            self._score_truncation,
            self._mmr,
        ]
        
        logger.info(f"RetrievalOrchestrator initialized with {len(self._stages)} stages")
    
    # =========================================================================
    # 依赖设置
    # =========================================================================
    
    def set_vector_store(self, vector_store: Any):
        """设置向量存储"""
        self._hybrid_retrieval.set_vector_store(vector_store)
    
    def set_embedding_function(self, fn):
        """设置嵌入函数（用于 MMR）"""
        self._mmr.set_embedding_function(fn)
    
    # =========================================================================
    # 核心方法
    # =========================================================================
    
    def retrieve(self, query: str) -> RetrievalContext:
        """
        执行完整的检索流水线
        
        Args:
            query: 用户查询
        
        Returns:
            RetrievalContext: 包含最终文档和各阶段元数据
        """
        pipeline_start("RAG Retrieval Pipeline")
        start_time = time.time()
        
        # 初始化上下文
        context = RetrievalContext(original_query=query)
        
        try:
            # 按顺序执行各阶段
            for stage in self._stages:
                if stage.is_enabled():
                    context = stage.execute(context)
                else:
                    logger.debug(f"Stage '{stage.name}' is disabled, skipping")
            
            # 记录总时长
            total_duration = (time.time() - start_time) * 1000
            context.stage_metadata["total_duration_ms"] = total_duration
            context.stage_metadata["timing"] = get_timing_summary()
            
            pipeline_end("RAG Retrieval Pipeline")
            
            # 日志
            confidence = "⚠ LOW CONFIDENCE" if context.low_confidence else ""
            logger.info(
                f"Pipeline completed in {total_duration:.2f}ms: "
                f"{len(context.expanded_queries)} queries → "
                f"{len(context.fused_documents)} fused → "
                f"{len(context.reranked_documents)} reranked → "
                f"{len(context.truncated_documents)} truncated → "
                f"{len(context.final_documents)} final {confidence}"
            )
            
            return context
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            import traceback
            traceback.print_exc()
            
            pipeline_end("RAG Retrieval Pipeline (Failed)")
            
            context.stage_metadata["error"] = str(e)
            context.stage_metadata["total_duration_ms"] = (time.time() - start_time) * 1000
            return context
    
    def retrieve_simple(self, query: str, top_k: int = 5) -> List[Document]:
        """简化接口，直接返回 LangChain Document 列表"""
        context = self.retrieve(query)
        return context.to_langchain_documents()[:top_k]
    
    # =========================================================================
    # 配置管理
    # =========================================================================
    
    def update_config(self, **kwargs):
        """
        动态更新配置
        
        Args:
            kwargs: 格式为 "stage__param": value
                    例如 "query_expansion__enabled": True
        """
        stage_map = {
            "query_expansion": self._query_expansion,
            "hybrid_retrieval": self._hybrid_retrieval,
            "rrf_fusion": self._rrf_fusion,
            "reranking": self._reranking,
            "score_truncation": self._score_truncation,
            "mmr": self._mmr,
        }
        
        for key, value in kwargs.items():
            parts = key.split('__')
            if len(parts) == 2:
                stage_name, param = parts
                if stage_name in stage_map:
                    stage_map[stage_name].update_config(**{param: value})
        
        logger.info(f"Orchestrator config updated: {kwargs}")
    
    def get_pipeline_info(self) -> Dict[str, Any]:
        """获取流水线配置信息"""
        return {
            "query_expansion": self._query_expansion.get_config(),
            "hybrid_retrieval": self._hybrid_retrieval.get_config(),
            "rrf_fusion": self._rrf_fusion.get_config(),
            "reranking": self._reranking.get_config(),
            "score_truncation": self._score_truncation.get_config(),
            "mmr": self._mmr.get_config(),
        }
    
    # =========================================================================
    # 高级功能：自定义阶段
    # =========================================================================
    
    def add_stage(self, stage: RetrievalStage, position: int = -1):
        """
        添加自定义阶段
        
        Args:
            stage: 实现了 RetrievalStage 接口的阶段
            position: 插入位置，-1 表示末尾
        """
        if position < 0:
            self._stages.append(stage)
        else:
            self._stages.insert(position, stage)
        logger.info(f"Added stage '{stage.name}' at position {position}")
    
    def remove_stage(self, name: str):
        """移除指定名称的阶段"""
        self._stages = [s for s in self._stages if s.name != name]
        logger.info(f"Removed stage '{name}'")
    
    def get_stages(self) -> List[str]:
        """获取当前阶段列表"""
        return [s.name for s in self._stages]

