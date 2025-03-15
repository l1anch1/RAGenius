from langchain.chains import RetrievalQA
from langchain_core.language_models.llms import LLM
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate

from app.config import SEARCH_K
import app.core.shared_instances as shared
from app.core.model_utils import get_llm
from app.core.document_processor import get_vector_store

# FINANCE_QA_PROMPT_TEMPLATE = """  
# 你是一位专业的金融分析师和助手，拥有丰富的金融市场知识和经验。  
# 你需要根据提供的背景信息回答用户的问题。  

# 背景信息: {context}  

# 用户问题: {question}  

# 请以专业、清晰的方式回答问题，依据提供的背景信息。如果背景信息不足以回答问题，  
# 请坦诚地说明，并尽可能提供相关的一般性建议。回答中应注重专业性和实用性，  
# 避免过度技术性的术语，确保普通投资者也能理解。  
# 所有回答必须使用简体中文，并保持专业性、准确性和可读性。  
# """


# FINANCE_QA_PROMPT_TEMPLATE = """  
# 你是一位专业的编译领域专家，拥有丰富的理论基础和开发经验，了解编译领域的各种知识。  
# 你需要根据提供的背景信息回答用户的问题。  

# 背景信息: {context}  

# 用户问题: {question}  

# 请以专业、清晰的方式回答问题，依据提供的背景信息。如果背景信息不足以回答问题，  
# 请坦诚地说明，并尽可能提供相关的一般性建议。回答中应注重专业性和实用性，  
# 避免过度技术性的术语，确保普通投资者也能理解。  
# 所有回答必须使用简体中文，并保持专业性、准确性和可读性。  
# """


FINANCE_QA_PROMPT_TEMPLATE = """  
你是一位专业的人机交互和教育大模型专家，拥有丰富的理论基础和开发经验，了解大模型的各种知识。  
你需要根据提供的背景信息回答用户的问题。  

背景信息: {context}  

用户问题: {question}  

请以专业、清晰的方式回答问题，依据提供的背景信息。如果背景信息不足以回答问题，  
请坦诚地说明，并尽可能提供相关的一般性建议。回答中应注重专业性和实用性，  
避免过度技术性的术语，确保普通开发和研究者也能理解。  
所有回答必须使用简体中文，并保持专业性、准确性和可读性。  
"""

def create_qa_chain(llm: LLM, vector_db: Chroma, embedding_model=None) -> RetrievalQA:
    try:
        # 获取LLM  
        llm_instance = get_llm()  
        if llm_instance is None:  
            return None  
            
        # 获取向量数据库  
        vector_db = get_vector_store()  
        if vector_db is None:  
            return None  
        # 创建检索器
        retriever = vector_db.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": SEARCH_K
            }
        )

        # 创建提示模板
        prompt = PromptTemplate(template=FINANCE_QA_PROMPT_TEMPLATE, input_variables=["context", "query"])

        # 创建链
        shared.qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",  # 使用stuff方法将所有文档合并
            retriever=retriever,
            return_source_documents=True,  # 返回源文档
            chain_type_kwargs={"prompt": prompt}
        )

        return shared.qa_chain

    except Exception as e:
        print(f"QA chain creating error: {str(e)}")
        raise RuntimeError(f"Cannot create QA chain: {str(e)}")
