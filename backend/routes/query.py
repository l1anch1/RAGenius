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
            
            result = query_service.process_query(user_query)
            
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
            
            def generate():
                try:
                    for event in query_service.process_stream_query(user_query):
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
    
    return query_bp
