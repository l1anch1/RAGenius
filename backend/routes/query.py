import re
import json
from flask import Blueprint, request, Response, jsonify, stream_with_context
from core.document_processor import get_vector_store
from core.model_utils import get_llm
from langchain_core.prompts import PromptTemplate
from core.retrieval_chain import FINANCE_QA_PROMPT_TEMPLATE, create_qa_chain
from config import SEARCH_K

query_bp = Blueprint("query", __name__)

global_qa_chain = None


@query_bp.route("/api/query/stream", methods=["POST", "GET"])
def stream_query_knowledge_base():
    """Stream processing of knowledge base queries"""
    if not global_qa_chain:
        return jsonify(
            {
                "status": "error",
                "message": "The knowledge base is not initialized. Please build it first",
            }
        )

    if request.method == "POST":
        data = request.get_json()
        query = data.get("query", "")
    else:
        query = request.args.get("q", "")

    if not query.strip():
        return jsonify({"status": "error", "message": "Query content cannot be empty"})

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

            # Get LLM with streaming callback
            streaming_llm = get_llm(streaming=True)

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

            full_prompt = prompt.format(context=context, question=query)

            # Start streaming generation
            for chunk in streaming_llm.stream(full_prompt):
                token_content = chunk.content if hasattr(chunk, "content") else chunk
                yield f"data: {json.dumps({'type': 'token', 'token': token_content})}\n\n"

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
