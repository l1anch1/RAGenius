"""
Documents Routes
文档相关路由
"""
from flask import Blueprint, jsonify, request
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
    
    @documents_bp.route("/api/documents/delete", methods=["POST"])
    def delete_document():
        """删除单个文档"""
        try:
            data = request.get_json()
            if not data or 'filename' not in data:
                return jsonify({"status": "error", "message": "Filename is required"}), 400
            
            filename = data['filename']
            result = document_service.delete_document(filename)
            
            if result['status'] == 'error':
                return jsonify(result), 404 if 'not found' in result['message'].lower() else 500
            
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in delete_document: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    @documents_bp.route("/api/documents/clear", methods=["POST"])
    def clear_all_documents():
        """清空所有文档"""
        try:
            result = document_service.clear_all_documents()
            
            if result['status'] == 'error':
                return jsonify(result), 500
            
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in clear_all_documents: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    @documents_bp.route("/api/documents/upload", methods=["POST"])
    def upload_document():
        """上传文档"""
        try:
            # 检查是否有文件
            if 'file' not in request.files:
                return jsonify({"status": "error", "message": "No file provided"}), 400
            
            file = request.files['file']
            
            # 检查文件名
            if file.filename == '':
                return jsonify({"status": "error", "message": "No file selected"}), 400
            
            # 上传文件
            result = document_service.upload_document(file)
            
            if result['status'] == 'error':
                return jsonify(result), 400
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Error in upload_document: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    @documents_bp.route("/api/documents/preview/<path:filename>", methods=["GET"])
    def preview_document(filename):
        """获取文档预览"""
        try:
            # 获取查询参数中的最大长度
            max_length = request.args.get('max_length', default=1000, type=int)
            
            result = document_service.get_document_preview(filename, max_length)
            
            if result['status'] == 'error':
                return jsonify(result), 404
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Error in preview_document: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    return documents_bp
