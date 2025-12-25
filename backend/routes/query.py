"""
Query Routes
查询相关路由
"""
from flask import Blueprint, request, jsonify, Response
import logging

from services.query_service import QueryService

logger = logging.getLogger(__name__)


def create_query_blueprint(query_service: QueryService) -> Blueprint:
    """创建查询路由蓝图"""
    
    query_bp = Blueprint('query', __name__)
    
    @query_bp.route("/api/query", methods=["POST"])
    def query():
        """处理查询请求"""
        try:
            data = request.get_json()
            if not data or 'query' not in data:
                return jsonify({"status": "error", "message": "Query is required"}), 400
            
            user_query = data['query']
            if not user_query.strip():
                return jsonify({"status": "error", "message": "Query cannot be empty"}), 400
            
            # 获取对话历史（可选）
            chat_history = data.get('chat_history', [])
            if chat_history and not isinstance(chat_history, list):
                chat_history = []
            
            result = query_service.process_query(user_query, chat_history)
            
            if result['status'] == 'error':
                return jsonify(result), 500
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Error in query: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    @query_bp.route("/api/query/stream", methods=["POST"])
    def query_stream():
        """处理流式查询请求"""
        try:
            data = request.get_json()
            if not data or 'query' not in data:
                return jsonify({"status": "error", "message": "Query is required"}), 400
            
            user_query = data['query']
            if not user_query.strip():
                return jsonify({"status": "error", "message": "Query cannot be empty"}), 400
            
            # 获取对话历史（可选）
            chat_history = data.get('chat_history', [])
            if chat_history and not isinstance(chat_history, list):
                chat_history = []
            
            def generate():
                try:
                    for event in query_service.process_stream_query(user_query, chat_history):
                        yield event
                except Exception as e:
                    logger.error(f"Error in stream query: {e}")
                    yield f"data: {{\"type\": \"error\", \"error\": \"{str(e)}\"}}\n\n"
            
            return Response(
                generate(),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'Access-Control-Allow-Origin': '*'
                }
            )
            
        except Exception as e:
            logger.error(f"Error in query_stream: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    # ========================================
    # 检索流水线配置 API
    # ========================================
    
    @query_bp.route("/api/retrieval/config", methods=["GET"])
    def get_retrieval_config():
        """获取当前检索流水线配置"""
        try:
            pipeline_info = query_service.get_pipeline_info()
            return jsonify({
                "status": "success",
                "config": pipeline_info
            })
        except Exception as e:
            logger.error(f"Error getting retrieval config: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    @query_bp.route("/api/retrieval/config", methods=["POST"])
    def update_retrieval_config():
        """更新检索流水线配置
        
        请求体示例:
        {
            "query_expansion__enabled": true,
            "query_expansion__n_subqueries": 5,
            "hybrid_retrieval__embedding_weight": 0.7,
            "reranking__enabled": false,
            "mmr_postprocessing__mode": "always"
        }
        """
        try:
            data = request.get_json()
            if not data:
                return jsonify({"status": "error", "message": "No configuration provided"}), 400
            
            # 更新配置
            query_service.update_pipeline_config(**data)
            
            # 返回更新后的配置
            pipeline_info = query_service.get_pipeline_info()
            return jsonify({
                "status": "success",
                "message": "Configuration updated",
                "config": pipeline_info
            })
            
        except Exception as e:
            logger.error(f"Error updating retrieval config: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    return query_bp
