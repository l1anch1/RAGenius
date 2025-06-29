import os
from flask import Blueprint, jsonify
from config import DOCUMENTS_DIR

documents_bp = Blueprint("documents", __name__)


@documents_bp.route("/api/documents", methods=["GET"])
def get_documents():
    try:
        if not os.path.exists(DOCUMENTS_DIR):
            return jsonify({"status": "success", "documents": []})

        documents = [
            file_name
            for file_name in os.listdir(DOCUMENTS_DIR)
            if os.path.isfile(os.path.join(DOCUMENTS_DIR, file_name))
            and file_name != ".gitkeep"
        ]

        return jsonify({"status": "success", "documents": documents})
    except Exception as e:
        return jsonify(
            {"status": "error", "message": f"cannot get documents: {str(e)}"}
        )
