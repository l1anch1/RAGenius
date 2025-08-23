"""
Documents Routes
文档相关路由
"""
from flask import Blueprint, jsonify
import logging

from services.document_service import DocumentService

logger = logging.getLogger(__name__)


def create_documents_blueprint(document_service: DocumentService) -> Blueprint:
    """创建文档路由蓝图"""
    
    documents_bp = Blueprint('documents', __name__)
    
    @documents_bp.route("/api/documents", methods=["GET"])
    def get_documents():
        """获取文档列表"""
        try:
            result = document_service.get_documents()
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in get_documents: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    @documents_bp.route("/api/documents/vectorized", methods=["GET"])
    def get_vectorized_documents():
        """获取已向量化的文档列表"""
        try:
            result = document_service.get_vectorized_documents()
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in get_vectorized_documents: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    return documents_bp
