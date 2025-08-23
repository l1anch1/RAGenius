# RAGenius 架构重构说明

## 重构概述

本次重构将原有的基于全局共享变量的架构，改为基于**依赖注入**和**分层架构**的现代软件工程架构。

## 架构对比

### 旧架构问题

1. **全局状态管理混乱**
   - 使用 `backend/core/shared_instances.py` 全局变量
   - 线程安全问题
   - 状态同步困难
   - 测试困难

2. **紧耦合**
   - 各模块直接访问全局变量
   - 难以单独测试和替换组件
   - 循环依赖问题

3. **缺乏抽象**
   - 没有接口定义
   - 实现细节暴露
   - 扩展性差

### 新架构优势

1. **分层架构**
   ```
   Routes Layer (路由层)
        ↓
   Service Layer (服务层)  
        ↓
   Manager Layer (管理器层)
        ↓
   Interface Layer (接口层)
   ```

2. **依赖注入**
   - 统一的容器管理
   - 生命周期控制
   - 易于测试和替换

3. **线程安全缓存**
   - 使用 `CacheManager` 管理实例
   - RLock 保证线程安全
   - TTL 缓存策略

## 新架构组件

### 1. 接口层 (`interfaces/`)
- `VectorStoreInterface`: 向量存储抽象接口
- `EmbeddingInterface`: 嵌入模型抽象接口  
- `LLMInterface`: 大语言模型抽象接口
- `DocumentServiceInterface`: 文档服务抽象接口
- `QueryServiceInterface`: 查询服务抽象接口
- `SystemServiceInterface`: 系统服务抽象接口

### 2. 管理器层 (`managers/`)
- `CacheManager`: 线程安全的缓存管理器
- `ChromaVectorStoreManager`: ChromaDB向量存储管理器
- `EmbeddingManager`: 嵌入模型管理器
- `LLMManager`: 大语言模型管理器

### 3. 服务层 (`services/`)
- `DocumentService`: 文档管理服务
- `QueryService`: 查询处理服务
- `SystemService`: 系统信息服务

### 4. 路由层 (`routes/`)
- `documents.py`: 文档相关路由
- `query.py`: 查询相关路由
- `system.py`: 系统相关路由

### 5. 依赖注入容器 (`container.py`)
- `DIContainer`: 统一管理所有依赖关系

## 关键改进

### 1. 线程安全缓存管理
```python
class CacheManager(Generic[T]):
    def __init__(self, ttl: int = 300, name: str = "cache"):
        self._cache: Optional[T] = None
        self._timestamp = 0
        self._lock = threading.RLock()  # 线程安全
        self._ttl = ttl
```

### 2. 依赖注入
```python
class DIContainer:
    def initialize(self):
        # 1. 创建模型管理器
        self._instances['embedding_manager'] = EmbeddingManager()
        self._instances['llm_manager'] = LLMManager()
        
        # 2. 创建向量存储管理器
        self._instances['vector_store_manager'] = ChromaVectorStoreManager(
            embedding_interface=self._instances['embedding_manager']
        )
        
        # 3. 创建服务
        self._instances['document_service'] = DocumentService(
            vector_store_manager=self._instances['vector_store_manager']
        )
```

### 3. 接口抽象
```python
class VectorStoreInterface(ABC):
    @abstractmethod
    def get_store(self) -> Optional[Any]:
        """获取向量存储实例"""
        pass
    
    @abstractmethod
    def rebuild_store(self, documents_dir: str) -> bool:
        """重建向量存储"""
        pass
```

### 4. 现代化RAG链
```python
# 使用新的LangChain Runnable API
qa_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)
```

## 启动方式

```bash
./run.sh
```

## API兼容性

新架构完全兼容原有的API接口：

- `GET /api/documents` - 获取文档列表
- `GET /api/documents/vectorized` - 获取已向量化文档
- `GET /api/info` - 获取系统信息
- `POST /api/rebuild` - 重建知识库
- `POST /api/query` - 查询接口
- `POST /api/query/stream` - 流式查询接口

## 配置要求

确保 `.env` 文件包含必要的配置：
```env
OPENAI_API_KEY=your_api_key_here
LLM_OPENAI_API_BASE=https://api.openai-proxy.org/v1
LLM_OPENAI_MODEL=gpt-4o
LLM_USE_OPENAI=true
```

## 性能优势

1. **缓存管理**: 智能TTL缓存，避免重复初始化
2. **线程安全**: RLock保护，支持并发访问
3. **资源管理**: 统一的生命周期管理
4. **错误处理**: 分层错误处理，更好的错误追踪

## 扩展性

1. **新增LLM提供商**: 实现 `LLMInterface` 即可
2. **新增向量数据库**: 实现 `VectorStoreInterface` 即可  
3. **新增服务**: 通过依赖注入容器注册即可
4. **A/B测试**: 可以轻松切换不同实现

## 测试友好

1. **Mock支持**: 接口抽象便于Mock测试
2. **依赖注入**: 可以注入测试双件
3. **单元测试**: 每个组件可独立测试
4. **集成测试**: 容器化管理便于集成测试

## 总结

新架构遵循SOLID原则，提供了更好的：
- **可维护性**: 清晰的分层和职责分离
- **可扩展性**: 接口抽象和依赖注入
- **可测试性**: 松耦合和依赖注入
- **可靠性**: 线程安全和错误处理
- **性能**: 智能缓存和资源管理

这是一个符合现代软件工程最佳实践的架构重构。
