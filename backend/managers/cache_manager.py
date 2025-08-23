"""
Cache Manager
线程安全的缓存管理器
"""
import threading
import time
from typing import Optional, Callable, TypeVar, Generic
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CacheManager(Generic[T]):
    """线程安全的缓存管理器"""
    
    def __init__(self, ttl: int = 300, name: str = "cache"):
        """
        初始化缓存管理器
        
        Args:
            ttl: 缓存生存时间（秒）
            name: 缓存名称，用于日志
        """
        self._cache: Optional[T] = None
        self._timestamp = 0
        self._lock = threading.RLock()
        self._ttl = ttl
        self._name = name
        logger.debug(f"CacheManager '{name}' initialized with TTL={ttl}s")
    
    def get_or_create(self, factory: Callable[[], T], force_refresh: bool = False) -> Optional[T]:
        """
        获取缓存或创建新对象
        
        Args:
            factory: 创建对象的工厂函数
            force_refresh: 是否强制刷新缓存
        
        Returns:
            缓存的对象或新创建的对象
        """
        with self._lock:
            if force_refresh or self._is_expired():
                try:
                    logger.debug(f"CacheManager '{self._name}': Creating new instance")
                    self._cache = factory()
                    self._timestamp = time.time()
                    logger.debug(f"CacheManager '{self._name}': Instance created successfully")
                except Exception as e:
                    logger.error(f"CacheManager '{self._name}': Failed to create instance: {e}")
                    return None
            else:
                logger.debug(f"CacheManager '{self._name}': Using cached instance")
            
            return self._cache
    
    def get(self) -> Optional[T]:
        """获取缓存对象（不创建新对象）"""
        with self._lock:
            if self._is_expired():
                return None
            return self._cache
    
    def invalidate(self) -> None:
        """使缓存失效"""
        with self._lock:
            logger.debug(f"CacheManager '{self._name}': Invalidating cache")
            self._cache = None
            self._timestamp = 0
    
    def is_valid(self) -> bool:
        """检查缓存是否有效"""
        with self._lock:
            return self._cache is not None and not self._is_expired()
    
    def _is_expired(self) -> bool:
        """检查缓存是否过期"""
        if self._cache is None:
            return True
        return (time.time() - self._timestamp) > self._ttl
    
    def get_age(self) -> float:
        """获取缓存年龄（秒）"""
        with self._lock:
            if self._cache is None:
                return float('inf')
            return time.time() - self._timestamp
