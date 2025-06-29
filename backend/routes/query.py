# Flask Blueprint (query_bp.py)
import re
import json
from flask import Blueprint, request, Response, jsonify, stream_with_context
from core.document_processor import get_vector_store
from core.model_utils import get_llm
from langchain_core.prompts import PromptTemplate
from core.retrieval_chain import FINANCE_QA_PROMPT_TEMPLATE, create_qa_chain
from config import SEARCH_K
from langchain.chains import LLMChain

query_bp = Blueprint("query", __name__)


# Use a function to initialize the QA chain, not a global variable
def create_global_qa_chain():
    vector_db = get_vector_store()
    llm = get_llm(streaming=True)  # Ensure streaming is enabled

    prompt = PromptTemplate(
        template=FINANCE_QA_PROMPT_TEMPLATE,
        input_variables=["context", "question"],
    )

    # Create the chain using LLMChain directly
    chain = LLMChain(llm=llm, prompt=prompt)

    return chain


global_qa_chain = create_global_qa_chain()  # initialize qa_chain


@query_bp.route("/api/query/stream", methods=["POST", "GET"])
def stream_query_knowledge_base():
    """Stream processing of knowledge base queries"""
    if not global_qa_chain:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "The knowledge base is not initialized. Please build it first",
                }
            ),
            500,
        )  # Return 500 status code

    if request.method == "POST":
        data = request.get_json()
        query = data.get("query", "")
    else:
        query = request.args.get("q", "")

    if not query.strip():
        return (
            jsonify({"status": "error", "message": "Query content cannot be empty"}),
            400,
        )  # Return 400 status code

    def is_significant_overlap(text1, text2, overlap_threshold=0.4):
        norm_text1 = re.sub(r"\s+", "", text1).lower()
        norm_text2 = re.sub(r"\s+", "", text2).lower()

        shorter = norm_text1 if len(norm_text1) <= len(norm_text2) else norm_text2
        longer = norm_text2 if len(norm_text1) <= len(norm_text2) else norm_text1

        max_match_length = 0
        for i in range(len(shorter)):
            for j in range(i + 1, len(shorter) + 1):
                substring = shorter[i:j]
                if len(substring) > 30 and substring in longer:
                    max_match_length = max(max_match_length, len(substring))

        overlap_ratio = max_match_length / len(shorter)
        return overlap_ratio >= overlap_threshold

    def generate():
        try:
            # Get relevant documents
            vector_db = get_vector_store()
            docs = vector_db.similarity_search(query, k=SEARCH_K)

            # Build context
            context = "\n\n".join([doc.page_content for doc in docs])

            # Build prompt
            prompt = PromptTemplate(
                template=FINANCE_QA_PROMPT_TEMPLATE,
                input_variables=["context", "question"],
            )

            # Prepare source document information
            sources = []
            has_significant_overlap = False

            for doc in docs:
                content = doc.page_content.strip()
                source_name = (
                    doc.metadata.get("source", "unknown")
                    if hasattr(doc, "metadata")
                    else "unknown"
                )

                has_significant_overlap = any(
                    is_significant_overlap(content, existing_source["content"])
                    for existing_source in sources
                )

                if not has_significant_overlap:
                    sources.append({"content": content, "source": source_name})

            # Use the chain to run the prompt and context
            try:
                result = global_qa_chain.run(
                    context=context, question=query
                )  # Use the chain
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
                return  # Ensure the generator exits after sending an error

            # Stream the results token by token
            for token in result:  # Directly iterate over the string result
                yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"

            # After text generation completes, send source documents information
            yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"

            # Send completion signal
            yield f"data: {json.dumps({'type': 'end'})}\n\n"

        except Exception as e:
            error_msg = str(e)
            yield f"data: {json.dumps({'type': 'error', 'error': error_msg})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
