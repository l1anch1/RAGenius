"""
System Routes
系统相关路由
"""
from flask import Blueprint, jsonify
import logging

from services.system_service import SystemService
from services.document_service import DocumentService

logger = logging.getLogger(__name__)


def create_system_blueprint(system_service: SystemService, document_service: DocumentService) -> Blueprint:
    """创建系统路由蓝图"""
    
    system_bp = Blueprint('system', __name__)
    
    @system_bp.route("/api/info", methods=["GET"])
    def get_info():
        """获取系统信息"""
        try:
            result = system_service.get_system_info()
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in get_info: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    @system_bp.route("/api/rebuild", methods=["POST"])
    def rebuild():
        """重建知识库"""
        try:
            result = document_service.rebuild_knowledge_base()
            
            if result['status'] == 'error':
                return jsonify(result), 500
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Error in rebuild: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    return system_bp
