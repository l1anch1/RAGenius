"""
Query Service
查询服务实现
"""
import json
from typing import Dict, Any, Generator
import logging

from interfaces.services import QueryServiceInterface
from interfaces.vector_store import VectorStoreInterface, LLMInterface
from managers.cache_manager import CacheManager
from config import SEARCH_K, SIMILARITY_WEIGHT, MMR_WEIGHT, MMR_LAMBDA

logger = logging.getLogger(__name__)


class QueryService(QueryServiceInterface):
    """查询服务实现"""
    
    def __init__(self, vector_store_manager: VectorStoreInterface, llm_manager: LLMInterface):
        """
        初始化查询服务
        
        Args:
            vector_store_manager: 向量存储管理器
            llm_manager: LLM管理器
        """
        self.vector_store_manager = vector_store_manager
        self.llm_manager = llm_manager
        
        # QA链的缓存管理器
        self._qa_chain_cache = CacheManager(
            ttl=1800,  # 30分钟TTL
            name="qa_chain"
        )
        
        logger.info("QueryService initialized")
    
    def process_query(self, query: str, chat_history: list = None) -> Dict[str, Any]:
        """处理查询请求
        
        Args:
            query: 用户查询
            chat_history: 对话历史，格式为 [{"question": "问题", "answer": "回答"}, ...]
        """
        try:
            # 获取LLM（必需）
            llm = self.llm_manager.get_llm()
            if not llm:
                return {
                    "status": "error",
                    "message": "LLM not available. Please check if LLM is configured."
                }
            
            # 尝试获取向量存储和检索相关文档（可选）
            vector_store = self.vector_store_manager.get_store()
            retrieved_docs_for_llm = []
            sources = []
            
            if vector_store:
                # 知识库已初始化，进行检索
                try:
                    collection = vector_store._collection
                    total_count = collection.count()
                    logger.info(f"Knowledge base contains {total_count} total chunks")
                except Exception as e:
                    logger.warning(f"Could not get collection count: {e}")
                
                # 创建混合检索器
                retriever = self._create_hybrid_retriever(vector_store)
                all_retrieved_docs = retriever.get_relevant_documents(query)
                
                # 放宽文档数量限制，允许更多候选文档用于参考来源显示
                max_candidates = SEARCH_K * 2  # 允许更多候选文档
                retrieved_docs_for_sources = all_retrieved_docs[:max_candidates] if len(all_retrieved_docs) > max_candidates else all_retrieved_docs
                retrieved_docs_for_llm = all_retrieved_docs[:SEARCH_K] if len(all_retrieved_docs) > SEARCH_K else all_retrieved_docs
                
                # 添加调试信息
                logger.info(f"Retrieved {len(all_retrieved_docs)} documents from hybrid retriever")
                logger.info(f"Using {len(retrieved_docs_for_sources)} for sources, {len(retrieved_docs_for_llm)} for LLM")
                for i, doc in enumerate(retrieved_docs_for_llm[:3]):  # 只打印前3个
                    logger.info(f"Doc #{i+1}: {doc.metadata.get('source', 'Unknown')} - {doc.page_content[:100]}...")
                
                # 格式化参考来源 - 使用更多候选文档
                sources = self._format_sources(retrieved_docs_for_sources)
            else:
                # 知识库未初始化，不进行检索
                logger.info("Knowledge base not initialized, proceeding without document retrieval")
            
            if chat_history:
                logger.info(f"Chat history provided: {len(chat_history)} previous turns")
            
            # 生成回答（无论是否有文档）
            result = self._generate_answer_with_docs(query, retrieved_docs_for_llm, llm, chat_history)
            
            return {
                "status": "success",
                "answer": result,
                "sources": sources
            }
            
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            error_msg = str(e).lower()
            
            if "api key" in error_msg or "unauthorized" in error_msg or "404" in error_msg:
                error_message = "OpenAI API key is not valid. Please set a valid OPENAI_API_KEY environment variable."
            else:
                error_message = f"Query processing failed: {str(e)}"
            
            return {
                "status": "error",
                "message": error_message
            }
    
    def process_stream_query(self, query: str, chat_history: list = None) -> Generator[str, None, None]:
        """处理流式查询请求
        
        Args:
            query: 用户查询
            chat_history: 对话历史，格式为 [{"question": "问题", "answer": "回答"}, ...]
        """
        try:
            # 获取LLM（必需）
            llm = self.llm_manager.get_llm()
            if not llm:
                yield self._create_sse_event("error", "LLM not available")
                return
            
            # 尝试获取向量存储和检索相关文档（可选）
            vector_store = self.vector_store_manager.get_store()
            retrieved_docs_for_llm = []
            sources = []
            
            if vector_store:
                # 知识库已初始化，进行检索
                retriever = self._create_hybrid_retriever(vector_store)
                all_retrieved_docs = retriever.get_relevant_documents(query)
                
                # 放宽文档数量限制，允许更多候选文档用于参考来源显示
                max_candidates = SEARCH_K * 2  # 允许更多候选文档
                retrieved_docs_for_sources = all_retrieved_docs[:max_candidates] if len(all_retrieved_docs) > max_candidates else all_retrieved_docs
                retrieved_docs_for_llm = all_retrieved_docs[:SEARCH_K] if len(all_retrieved_docs) > SEARCH_K else all_retrieved_docs
                
                # 格式化并发送参考来源 - 使用更多候选文档
                sources = self._format_sources(retrieved_docs_for_sources)
                yield self._create_sse_event("sources", sources)
            else:
                # 知识库未初始化，不进行检索
                logger.info("Knowledge base not initialized, proceeding without document retrieval")
                yield self._create_sse_event("sources", [])
            
            # 流式生成答案（无论是否有文档）
            try:
                # 使用指定文档进行流式生成
                for chunk in self._stream_answer_with_docs(query, retrieved_docs_for_llm, llm, chat_history):
                    if chunk:
                        yield self._create_sse_event("token", chunk)
                
                yield self._create_sse_event("end", "")
                
            except Exception as e:
                logger.error(f"Stream query processing failed: {e}")
                error_msg = str(e).lower()
                
                if "api key" in error_msg or "unauthorized" in error_msg or "404" in error_msg:
                    error_message = "OpenAI API key is not valid. Please set a valid OPENAI_API_KEY environment variable."
                else:
                    error_message = str(e)
                
                yield self._create_sse_event("error", error_message)
                
        except Exception as e:
            logger.error(f"Stream query setup failed: {e}")
            yield self._create_sse_event("error", str(e))
    
    def _get_qa_chain(self):
        """获取QA链"""
        return self._qa_chain_cache.get_or_create(self._create_qa_chain)
    
    def _create_qa_chain(self):
        """创建QA链"""
        try:
            # 获取LLM
            llm = self.llm_manager.get_llm()
            if not llm:
                logger.error("LLM not available")
                return None
            
            # 获取向量存储
            vector_store = self.vector_store_manager.get_store()
            if not vector_store:
                logger.error("Vector store not available")
                return None
            
            # 创建检索器
            retriever = vector_store.as_retriever(search_kwargs={"k": SEARCH_K})
            
            # 创建提示模板
            from langchain.prompts import PromptTemplate
            from prompts import GENERAL_QA_PROMPT_TEMPLATE
            
            prompt = PromptTemplate(
                template=GENERAL_QA_PROMPT_TEMPLATE,
                input_variables=["context", "question"]
            )
            
            # 创建简单的RAG链
            from langchain_core.runnables import RunnablePassthrough
            from langchain_core.output_parsers import StrOutputParser
            
            def format_docs(docs):
                return "\n\n".join(doc.page_content for doc in docs)
            
            qa_chain = (
                {"context": retriever | format_docs, "question": RunnablePassthrough()}
                | prompt
                | llm
                | StrOutputParser()
            )
            
            logger.info("QA chain created successfully")
            return qa_chain
            
        except Exception as e:
            logger.error(f"Failed to create QA chain: {e}")
            return None
    
    def _extract_sources(self, result) -> list:
        """从结果中提取源文档"""
        sources = []
        
        if hasattr(result, 'source_documents'):
            for doc in result.source_documents:
                source_info = {
                    "content": doc.page_content,  # 显示完整内容，不截取
                    "source": doc.metadata.get('source', 'Unknown')
                }
                sources.append(source_info)
        
        return sources
    
    def _format_chat_history(self, chat_history: list = None) -> str:
        """格式化对话历史为字符串
        
        Args:
            chat_history: 对话历史，格式为 [{"question": "问题", "answer": "回答"}, ...]
        
        Returns:
            格式化后的对话历史字符串
        """
        if not chat_history or len(chat_history) == 0:
            return ""
        
        # 限制历史对话数量，避免token过多（只保留最近5轮对话）
        recent_history = chat_history[-5:] if len(chat_history) > 5 else chat_history
        
        formatted = []
        formatted.append("**对话历史**：")
        for i, turn in enumerate(recent_history, 1):
            question = turn.get("question", "")
            answer = turn.get("answer", "")
            if question and answer:
                formatted.append(f"\n第{i}轮对话：")
                formatted.append(f"用户：{question}")
                formatted.append(f"助手：{answer}")
        
        return "\n".join(formatted) if formatted else ""
    
    def _format_sources(self, docs: list) -> list:
        """格式化源文档，智能显示不同的相关片段"""
        sources = []
        file_chunk_count = {}  # 记录每个文件已添加的chunk数量
        seen_content = set()  # 用内容hash去重，避免完全相同的chunks
        
        logger.info(f"Formatting {len(docs)} documents as sources")
        
        for i, doc in enumerate(docs):
            source_path = doc.metadata.get('source', 'Unknown')
            # 提取文件名
            if source_path != 'Unknown':
                import os
                source_filename = os.path.basename(source_path)
            else:
                source_filename = source_path
            
            # 使用内容的前100字符作为唯一标识，避免完全相同的chunks
            # 减少hash长度，允许更多相似但不完全相同的内容
            content_preview = doc.page_content[:100].strip()
            content_hash = hash(content_preview)
            
            logger.info(f"Source #{i+1}: {source_filename} - Content hash: {content_hash}")
            
            # 检查是否是重复内容
            if content_hash in seen_content:
                logger.info(f"Skipping duplicate content from {source_filename}")
                continue
            
            # 限制每个文件最多显示5个chunks，但允许多个文件
            current_count = file_chunk_count.get(source_filename, 0)
            if current_count >= 5:
                logger.info(f"Skipping {source_filename} - already have {current_count} chunks")
                continue
            
            # 添加chunk编号以区分同一文件的不同片段
            chunk_num = current_count + 1
            display_source = f"{source_filename}" if chunk_num == 1 else f"{source_filename} (片段{chunk_num})"
            
            source_info = {
                "content": doc.page_content,  # 显示完整内容
                "source": display_source
            }
            sources.append(source_info)
            seen_content.add(content_hash)
            file_chunk_count[source_filename] = chunk_num
            
            # 限制总数量 - 增加到12个
            if len(sources) >= 12:
                break
        
        logger.info(f"After formatting: {len(sources)} unique sources from {len(file_chunk_count)} files")
        for filename, count in file_chunk_count.items():
            logger.info(f"  {filename}: {count} chunks")
        
        return sources
    
    def _generate_answer_with_docs(self, query: str, docs: list, llm, chat_history: list = None) -> str:
        """使用指定的文档生成回答
        
        Args:
            query: 用户查询
            docs: 检索到的文档列表（如果为空，则不使用文档）
            llm: LLM实例
            chat_history: 对话历史，格式为 [{"question": "问题", "answer": "回答"}, ...]
        """
        try:
            from langchain.prompts import PromptTemplate
            from langchain_core.output_parsers import StrOutputParser
            
            # 格式化对话历史
            formatted_history = self._format_chat_history(chat_history)
            
            # 根据是否有文档选择不同的提示模板
            if docs and len(docs) > 0:
                # 有文档，使用文档问答模板
                from prompts import GENERAL_QA_PROMPT_TEMPLATE
                
                prompt = PromptTemplate(
                    template=GENERAL_QA_PROMPT_TEMPLATE,
                    input_variables=["context", "question", "chat_history"]
                )
                
                # 格式化文档内容
                def format_docs(docs):
                    formatted = []
                    for i, doc in enumerate(docs, 1):
                        source = doc.metadata.get('source', 'Unknown')
                        content = doc.page_content
                        formatted.append(f"[文档{i} - {source}]\n{content}")
                    return "\n\n" + "="*50 + "\n\n".join(formatted)
                
                context = format_docs(docs)
                
                # 记录传递给LLM的确切内容
                logger.info(f"Sending {len(docs)} documents to LLM:")
                for i, doc in enumerate(docs, 1):
                    source = doc.metadata.get('source', 'Unknown')
                    logger.info(f"  Doc {i}: {source} ({len(doc.page_content)} chars)")
                
                # 调用LLM
                chain = prompt | llm | StrOutputParser()
                result = chain.invoke({
                    "context": context,
                    "question": query,
                    "chat_history": formatted_history
                })
            else:
                # 无文档，使用通用问答模板
                from prompts import GENERAL_QA_PROMPT_TEMPLATE_NO_DOCS
                
                prompt = PromptTemplate(
                    template=GENERAL_QA_PROMPT_TEMPLATE_NO_DOCS,
                    input_variables=["question", "chat_history"]
                )
                
                logger.info("No documents available, using general QA template")
                
                # 调用LLM
                chain = prompt | llm | StrOutputParser()
                result = chain.invoke({
                    "question": query,
                    "chat_history": formatted_history
                })
            
            if chat_history:
                logger.info(f"Including {len(chat_history)} previous conversation turns")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate answer with docs: {e}")
            return f"生成回答时出错: {str(e)}"
    
    def _stream_answer_with_docs(self, query: str, docs: list, llm, chat_history: list = None) -> Generator[str, None, None]:
        """使用指定的文档流式生成回答
        
        Args:
            query: 用户查询
            docs: 检索到的文档列表（如果为空，则不使用文档）
            llm: LLM实例
            chat_history: 对话历史，格式为 [{"question": "问题", "answer": "回答"}, ...]
        """
        try:
            from langchain.prompts import PromptTemplate
            from langchain_core.output_parsers import StrOutputParser
            
            # 格式化对话历史
            formatted_history = self._format_chat_history(chat_history)
            
            # 根据是否有文档选择不同的提示模板
            if docs and len(docs) > 0:
                # 有文档，使用文档问答模板
                from prompts import GENERAL_QA_PROMPT_TEMPLATE
                
                prompt = PromptTemplate(
                    template=GENERAL_QA_PROMPT_TEMPLATE,
                    input_variables=["context", "question", "chat_history"]
                )
                
                # 格式化文档内容（与非流式版本保持一致）
                def format_docs(docs):
                    formatted = []
                    for i, doc in enumerate(docs, 1):
                        source = doc.metadata.get('source', 'Unknown')
                        content = doc.page_content
                        formatted.append(f"[文档{i} - {source}]\n{content}")
                    return "\n\n" + "="*50 + "\n\n".join(formatted)
                
                context = format_docs(docs)
                
                # 创建流式链
                chain = prompt | llm | StrOutputParser()
                
                # 流式调用
                for chunk in chain.stream({
                    "context": context,
                    "question": query,
                    "chat_history": formatted_history
                }):
                    yield chunk
            else:
                # 无文档，使用通用问答模板
                from prompts import GENERAL_QA_PROMPT_TEMPLATE_NO_DOCS
                
                prompt = PromptTemplate(
                    template=GENERAL_QA_PROMPT_TEMPLATE_NO_DOCS,
                    input_variables=["question", "chat_history"]
                )
                
                logger.info("No documents available, using general QA template for streaming")
                
                # 创建流式链
                chain = prompt | llm | StrOutputParser()
                
                # 流式调用
                for chunk in chain.stream({
                    "question": query,
                    "chat_history": formatted_history
                }):
                    yield chunk
                
        except Exception as e:
            logger.error(f"Failed to stream answer with docs: {e}")
            yield f"生成回答时出错: {str(e)}"
    
    def _create_hybrid_retriever(self, vector_store):
        """创建混合检索器，结合BM25和语义检索"""
        try:
            from langchain.retrievers import EnsembleRetriever
            
            # 增加每个检索器的返回数量，确保有足够的候选文档
            # 让每个检索器返回更多文档，然后由EnsembleRetriever进行合并和排序
            k_per_retriever = SEARCH_K  # 每个检索器都返回完整数量
            
            similarity_retriever = vector_store.as_retriever(
                search_type="similarity", 
                search_kwargs={"k": k_per_retriever}
            )
            
            # 创建基于MMR的检索器（最大边际相关性，减少冗余）
            mmr_retriever = vector_store.as_retriever(
                search_type="mmr", 
                search_kwargs={
                    "k": k_per_retriever,
                    "lambda_mult": MMR_LAMBDA  # 平衡相关性和多样性
                }
            )
            
            # 创建混合检索器，不在这里限制数量，让它返回更多候选
            ensemble_retriever = EnsembleRetriever(
                retrievers=[similarity_retriever, mmr_retriever], 
                weights=[SIMILARITY_WEIGHT, MMR_WEIGHT]  # 可配置的权重
                # 移除search_kwargs限制，让它返回更多候选文档
            )
            
            logger.info(f"Hybrid retriever created successfully:")
            logger.info(f"  - Similarity retriever: k={k_per_retriever}, weight={SIMILARITY_WEIGHT}")
            logger.info(f"  - MMR retriever: k={k_per_retriever}, weight={MMR_WEIGHT}, lambda={MMR_LAMBDA}")
            logger.info(f"  - No final k limit on EnsembleRetriever to get more candidates")
            return ensemble_retriever
            
        except Exception as e:
            logger.error(f"Failed to create hybrid retriever: {e}")
            # 回退到简单的相似度检索
            logger.info("Falling back to similarity retriever")
            return vector_store.as_retriever(search_kwargs={"k": SEARCH_K * 2})  # 增加回退时的文档数量
    
    def _create_sse_event(self, event_type: str, data) -> str:
        """创建SSE事件"""
        event_data = {
            "type": event_type,
            event_type: data
        }
        return f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
