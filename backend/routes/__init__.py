"""
Routes Package
路由层 - 负责 HTTP API
"""

from .query import create_query_blueprint
from .documents import create_documents_blueprint
from .system import create_system_blueprint

__all__ = [
    "create_query_blueprint",
    "create_documents_blueprint",
    "create_system_blueprint",
]
