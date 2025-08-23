"""
Flask Application with Dependency Injection
使用依赖注入的Flask应用
"""
import os
import logging
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from container import container
from routes.documents import create_documents_blueprint
from routes.query import create_query_blueprint  
from routes.system import create_system_blueprint

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def create_app() -> Flask:
    """创建Flask应用"""
    
    app = Flask(__name__)
    
    # 启用CORS
    CORS(app)
    
    # 配置应用
    app.config['JSON_AS_ASCII'] = False
    app.config['DEBUG'] = True
    
    try:
        # 初始化依赖注入容器
        logger.info("Initializing dependency injection container...")
        container.initialize()
        
        # 获取服务实例
        document_service = container.get_document_service()
        query_service = container.get_query_service()
        system_service = container.get_system_service()
        
        # 注册蓝图
        app.register_blueprint(create_documents_blueprint(document_service))
        app.register_blueprint(create_query_blueprint(query_service))
        app.register_blueprint(create_system_blueprint(system_service, document_service))
        
        logger.info("Flask application created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create Flask application: {e}")
        raise
    
    return app


def main():
    """主函数"""
    try:
        app = create_app()
        
        # 启动应用
        logger.info("Starting Flask application...")
        app.run(
            host='0.0.0.0',
            port=8000,
            debug=True,
            use_reloader=True
        )
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise


if __name__ == "__main__":
    main()
