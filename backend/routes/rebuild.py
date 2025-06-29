from flask import Blueprint, jsonify
from core.document_processor import build_knowledge_base
from core.retrieval_chain import create_qa_chain

rebuild_bp = Blueprint("rebuild", __name__)

global_qa_chain = None


@rebuild_bp.route("/api/rebuild", methods=["POST"])
def rebuild_knowledge_base_route():
    global global_qa_chain

    try:
        success = build_knowledge_base()
        if success:
            global_qa_chain = create_qa_chain()
            return jsonify(
                {
                    "status": "success",
                    "message": "The knowledge base was rebuilt successfully",
                }
            )
        else:
            return jsonify(
                {"status": "error", "message": "Failed to rebuild the knowledge base"}
            )
    except Exception as e:
        return jsonify(
            {
                "status": "error",
                "message": f"Failed to rebuild the knowledge base: {str(e)}",
            }
        )
