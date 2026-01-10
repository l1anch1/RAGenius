"""
Query Service
查询服务实现
"""
import json
from typing import Dict, Any, Generator
import logging

from interfaces.services import QueryServiceInterface
from interfaces.vector_store import VectorStoreInterface, LLMInterface
from services.retrieval import RetrievalOrchestrator
from managers.timing import timed
from config import SEARCH_K

logger = logging.getLogger(__name__)


class QueryService(QueryServiceInterface):
    """查询服务实现"""
    
    def __init__(
        self, 
        vector_store_manager: VectorStoreInterface, 
        llm_manager: LLMInterface,
        retrieval_orchestrator: RetrievalOrchestrator
    ):
        """
        初始化查询服务
        
        Args:
            vector_store_manager: 向量存储管理器（依赖注入）
            llm_manager: LLM管理器（依赖注入）
            retrieval_orchestrator: 检索编排器（依赖注入）
        """
        self.vector_store_manager = vector_store_manager
        self.llm_manager = llm_manager
        self.retrieval_orchestrator = retrieval_orchestrator
        
        logger.info("QueryService initialized")
    
    def _ensure_orchestrator_dependencies(self):
        """确保编排器的依赖已绑定"""
        vector_store = self.vector_store_manager.get_store()
        if vector_store:
            self.retrieval_orchestrator.set_vector_store(vector_store)
        
        # 设置 embedding function 给 MMR 阶段
        embedding_model = self.vector_store_manager.embedding_interface.get_embeddings()
        if embedding_model:
            self.retrieval_orchestrator.set_embedding_function(
                lambda text: embedding_model.embed_query(text)
            )
    
    def _do_retrieval(self, query: str) -> tuple:
        """
        执行检索流程（抽取的公共方法）
        
        Returns:
            (retrieved_docs_for_llm, sources, retrieval_metadata, low_confidence)
        """
        vector_store = self.vector_store_manager.get_store()
        
        if not vector_store:
            logger.info("Knowledge base not initialized")
            return [], [], {}, True  # low_confidence=True when no knowledge base
        
        try:
            collection = vector_store._collection
            total_count = collection.count()
            logger.info(f"Knowledge base contains {total_count} total chunks")
        except Exception as e:
            logger.warning(f"Could not get collection count: {e}")
        
        # 确保编排器依赖已绑定
        self._ensure_orchestrator_dependencies()
        
        # 执行检索流水线
        context = self.retrieval_orchestrator.retrieve(query)
        
        retrieved_docs = context.to_langchain_documents()
        retrieved_docs_for_llm = retrieved_docs[:SEARCH_K]
        retrieved_docs_for_sources = retrieved_docs[:SEARCH_K * 2]
        
        sources = self._format_sources(retrieved_docs_for_sources)
        
        retrieval_metadata = {
            "expanded_queries": context.expanded_queries,
            "stages": context.stage_metadata,
            "total_duration_ms": context.stage_metadata.get("total_duration_ms", 0),
            "low_confidence": context.low_confidence
        }
        
        logger.info(f"Retrieved {len(retrieved_docs)} documents")
        
        return retrieved_docs_for_llm, sources, retrieval_metadata, context.low_confidence
    
    def process_query(self, query: str, chat_history: list = None) -> Dict[str, Any]:
        """处理查询请求"""
        try:
            llm = self.llm_manager.get_llm()
            if not llm:
                return {
                    "status": "error",
                    "message": "LLM not available. Please check if LLM is configured."
                }
            
            # 执行检索
            retrieved_docs_for_llm, sources, retrieval_metadata, low_confidence = self._do_retrieval(query)
            
            if chat_history:
                logger.info(f"Chat history provided: {len(chat_history)} previous turns")
            
            # 生成回答（传入 low_confidence 标志）
            result = self._generate_answer_with_docs(query, retrieved_docs_for_llm, llm, chat_history, low_confidence)
            
            response = {
                "status": "success",
                "answer": result,
                "sources": sources
            }
            
            if retrieval_metadata:
                response["retrieval_metadata"] = retrieval_metadata
            
            return response
            
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            import traceback
            traceback.print_exc()
            
            error_msg = str(e).lower()
            if "api key" in error_msg or "unauthorized" in error_msg or "404" in error_msg:
                error_message = "OpenAI API key is not valid."
            else:
                error_message = f"Query processing failed: {str(e)}"
            
            return {"status": "error", "message": error_message}
    
    def process_stream_query(self, query: str, chat_history: list = None) -> Generator[str, None, None]:
        """处理流式查询请求"""
        try:
            llm = self.llm_manager.get_llm()
            if not llm:
                yield self._create_sse_event("error", "LLM not available")
                return
            
            # 执行检索
            retrieved_docs_for_llm, sources, retrieval_metadata, low_confidence = self._do_retrieval(query)
                
            # 发送检索结果
            if retrieval_metadata:
                yield self._create_sse_event("retrieval_metadata", retrieval_metadata)
                yield self._create_sse_event("sources", sources)
            
            try:
                for chunk in self._stream_answer_with_docs(query, retrieved_docs_for_llm, llm, chat_history, low_confidence):
                    if chunk:
                        yield self._create_sse_event("token", chunk)
                
                yield self._create_sse_event("end", "")
                
            except Exception as e:
                logger.error(f"Stream query processing failed: {e}")
                yield self._create_sse_event("error", str(e))
                
        except Exception as e:
            logger.error(f"Stream query setup failed: {e}")
            yield self._create_sse_event("error", str(e))
    
    def update_pipeline_config(self, **kwargs):
        """更新检索流水线配置"""
        self.retrieval_orchestrator.update_config(**kwargs)
    
    def get_pipeline_info(self) -> Dict[str, Any]:
        """获取检索流水线信息"""
        return self.retrieval_orchestrator.get_pipeline_info()
    
    def _format_chat_history(self, chat_history: list = None) -> str:
        """格式化对话历史"""
        if not chat_history:
            return ""
        
        recent_history = chat_history[-5:]
        formatted = ["**对话历史**："]
        for i, turn in enumerate(recent_history, 1):
            question = turn.get("question", "")
            answer = turn.get("answer", "")
            if question and answer:
                formatted.append(f"\n第{i}轮对话：")
                formatted.append(f"用户：{question}")
                formatted.append(f"助手：{answer}")
        
        return "\n".join(formatted) if len(formatted) > 1 else ""
    
    def _format_sources(self, docs: list) -> list:
        """格式化源文档"""
        sources = []
        file_chunk_count = {}
        seen_content = set()
        
        for doc in docs:
            source_path = doc.metadata.get('source', 'Unknown')
            if source_path != 'Unknown':
                import os
                source_filename = os.path.basename(source_path)
            else:
                source_filename = source_path
            
            content_preview = doc.page_content[:100].strip()
            content_hash = hash(content_preview)
            
            if content_hash in seen_content:
                continue
            
            current_count = file_chunk_count.get(source_filename, 0)
            if current_count >= 5:
                continue
            
            chunk_num = current_count + 1
            display_source = f"{source_filename}" if chunk_num == 1 else f"{source_filename} (片段{chunk_num})"
            
            sources.append({
                "content": doc.page_content,
                "source": display_source
            })
            seen_content.add(content_hash)
            file_chunk_count[source_filename] = chunk_num
            
            if len(sources) >= 12:
                break
        
        return sources
    
    @timed("LLM Answer Generation")
    def _generate_answer_with_docs(self, query: str, docs: list, llm, chat_history: list = None, low_confidence: bool = False) -> str:
        """使用文档生成回答"""
        try:
            from langchain_core.prompts import PromptTemplate
            from langchain_core.output_parsers import StrOutputParser
            
            formatted_history = self._format_chat_history(chat_history)
            
            if docs:
                # 根据置信度选择不同的 prompt
                if low_confidence:
                    from config import GENERAL_QA_PROMPT_TEMPLATE_LOW_CONFIDENCE
                    template = GENERAL_QA_PROMPT_TEMPLATE_LOW_CONFIDENCE
                    logger.info("Using low-confidence prompt template")
                else:
                    from config import GENERAL_QA_PROMPT_TEMPLATE
                    template = GENERAL_QA_PROMPT_TEMPLATE
                
                prompt = PromptTemplate(
                    template=template,
                    input_variables=["context", "question", "chat_history"]
                )
                
                context = self._format_docs_for_llm(docs)
                
                chain = prompt | llm | StrOutputParser()
                return chain.invoke({
                    "context": context,
                    "question": query,
                    "chat_history": formatted_history
                })
            else:
                from config import GENERAL_QA_PROMPT_TEMPLATE_NO_DOCS
                
                prompt = PromptTemplate(
                    template=GENERAL_QA_PROMPT_TEMPLATE_NO_DOCS,
                    input_variables=["question", "chat_history"]
                )
                
                chain = prompt | llm | StrOutputParser()
                return chain.invoke({
                    "question": query,
                    "chat_history": formatted_history
                })
            
        except Exception as e:
            logger.error(f"Failed to generate answer: {e}")
            return f"生成回答时出错: {str(e)}"
    
    def _stream_answer_with_docs(self, query: str, docs: list, llm, chat_history: list = None, low_confidence: bool = False) -> Generator[str, None, None]:
        """流式生成回答"""
        try:
            from langchain_core.prompts import PromptTemplate
            from langchain_core.output_parsers import StrOutputParser
            
            formatted_history = self._format_chat_history(chat_history)
            
            if docs:
                # 根据置信度选择不同的 prompt
                if low_confidence:
                    from config import GENERAL_QA_PROMPT_TEMPLATE_LOW_CONFIDENCE
                    template = GENERAL_QA_PROMPT_TEMPLATE_LOW_CONFIDENCE
                else:
                    from config import GENERAL_QA_PROMPT_TEMPLATE
                    template = GENERAL_QA_PROMPT_TEMPLATE
                
                prompt = PromptTemplate(
                    template=template,
                    input_variables=["context", "question", "chat_history"]
                )
                
                context = self._format_docs_for_llm(docs)
                chain = prompt | llm | StrOutputParser()
                
                for chunk in chain.stream({
                    "context": context,
                    "question": query,
                    "chat_history": formatted_history
                }):
                    yield chunk
            else:
                from config import GENERAL_QA_PROMPT_TEMPLATE_NO_DOCS
                
                prompt = PromptTemplate(
                    template=GENERAL_QA_PROMPT_TEMPLATE_NO_DOCS,
                    input_variables=["question", "chat_history"]
                )
                
                chain = prompt | llm | StrOutputParser()
                
                for chunk in chain.stream({
                    "question": query,
                    "chat_history": formatted_history
                }):
                    yield chunk
                
        except Exception as e:
            logger.error(f"Failed to stream answer: {e}")
            yield f"生成回答时出错: {str(e)}"
    
    def _format_docs_for_llm(self, docs: list) -> str:
        """格式化文档用于LLM"""
        formatted = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get('source', 'Unknown')
            formatted.append(f"[文档{i} - {source}]\n{doc.page_content}")
        return "\n\n" + "="*50 + "\n\n".join(formatted)
    
    def _create_sse_event(self, event_type: str, data) -> str:
        """创建SSE事件"""
        event_data = {"type": event_type, event_type: data}
        return f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
