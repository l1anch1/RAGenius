from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from langchain.retrievers import EnsembleRetriever

from config import SEARCH_K
import core.shared_instances as shared
from core.model_utils import get_llm
from core.document_processor import get_vector_store
from prompts import FINANCE_QA_PROMPT_TEMPLATE, GENERAL_QA_PROMPT_TEMPLATE


def create_qa_chain() -> RetrievalQA:
    try:
        if shared.qa_chain is not None:
            return shared.qa_chain

        llm_instance = get_llm()
        if llm_instance is None:
            return None

        vector_db = get_vector_store()
        if vector_db is None:
            return None

        bm25_retriever = vector_db.as_retriever(
            search_type="similarity", search_kwargs={"k": SEARCH_K}
        )
        semantic_retriever = vector_db.as_retriever(
            search_type="mmr", search_kwargs={"k": SEARCH_K}
        )

        ensemble_retriever = EnsembleRetriever(
            retrievers=[bm25_retriever, semantic_retriever], weights=[0.5, 0.5]
        )

        prompt = PromptTemplate(
            template=FINANCE_QA_PROMPT_TEMPLATE, input_variables=["context", "question"]
        )

        shared.qa_chain = RetrievalQA.from_chain_type(
            llm=llm_instance,
            chain_type="stuff",
            retriever=ensemble_retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt},
        )

        return shared.qa_chain

    except Exception as e:
        raise RuntimeError(f"cannot create QA chain: {str(e)}")
