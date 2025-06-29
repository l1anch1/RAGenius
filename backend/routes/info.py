from flask import Blueprint, jsonify
from config import (
    LLM_LOCAL_MODEL,
    EMBEDDING_MODEL,
    LLM_NUM_THREAD,
    LLM_USE_OPENAI,
    LLM_OPENAI_API_KEY,
    LLM_OPENAI_MODEL,
)
from core.shared_instances import qa_chain

info_bp = Blueprint("info", __name__)


@info_bp.route("/api/info", methods=["GET"])
def get_system_info():
    try:
        model = (
            LLM_OPENAI_MODEL
            if LLM_USE_OPENAI and LLM_OPENAI_API_KEY
            else LLM_LOCAL_MODEL
        )
        return jsonify(
            {
                "status": "success",
                "model": model,
                "embedding_model": EMBEDDING_MODEL,
                "threads": LLM_NUM_THREAD,
                "initialized": qa_chain is not None,
            }
        )
    except Exception as e:
        return jsonify(
            {"status": "error", "message": f"cannot get system info: {str(e)}"}
        )
