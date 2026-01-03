# ChromaDB 持久化配置说明

## 📌 概述

RAGenius 现在支持两种向量数据库模式：

1. **持久化模式**（默认，推荐生产环境）
2. **纯内存模式**（适合开发测试）

---

## 🔧 配置方法

### 方式 1：持久化模式（推荐）

**特点**：
- ✅ 数据保存在 Docker Volume 中
- ✅ 容器重启/删除后数据不丢失
- ✅ 适合生产环境
- ✅ 用户上传的文档会永久保存

**配置**：

在 `.env` 文件中添加（或保持默认）：

```bash
# 持久化模式（默认）
CHROMA_PERSIST_DIR=/app/chroma_data
```

或者**不设置**这个变量（`docker-compose.yml` 中有默认值）。

**Docker Volume**：

`docker-compose.yml` 已经配置了 volume：

```yaml
volumes:
  - chroma_data:/app/chroma_data

volumes:
  chroma_data:
    driver: local
```

---

### 方式 2：纯内存模式

**特点**：
- ✅ 完全在内存中运行
- ✅ 不占用磁盘空间
- ✅ 性能略高（无磁盘 I/O）
- ❌ 容器重启后数据丢失
- ❌ 不适合生产环境

**配置**：

在 `.env` 文件中设置：

```bash
# 纯内存模式
CHROMA_PERSIST_DIR=
```

或者在 `docker-compose.yml` 中注释掉 volume：

```yaml
volumes:
  - models_cache:/app/models_cache
  # - chroma_data:/app/chroma_data  # 注释掉以使用纯内存模式
```

---

## 🚀 生产环境部署

### 在阿里云 ECS 上启用持久化

#### 1. 修改 `.env` 文件

```bash
# SSH 登录服务器
ssh root@你的服务器IP

# 编辑配置
nano /opt/ragenius/.env
```

**确保包含**（或保持默认）：

```bash
CHROMA_PERSIST_DIR=/app/chroma_data
```

#### 2. 重新部署

```bash
cd /opt/ragenius

# 停止并删除旧容器
docker compose down

# 启动新容器（会自动创建 volume）
docker compose up -d

# 查看日志
docker compose logs -f backend
```

#### 3. 验证持久化

```bash
# 查看 volume 列表
docker volume ls | grep chroma_data

# 查看 volume 详情
docker volume inspect ragenius_chroma_data

# 应该看到类似输出：
# {
#     "Name": "ragenius_chroma_data",
#     "Mountpoint": "/var/lib/docker/volumes/ragenius_chroma_data/_data",
#     ...
# }
```

#### 4. 测试持久化

```bash
# 1. 在网页上上传文档并构建知识库
# 2. 重启容器
docker compose restart

# 3. 刷新网页，检查知识库是否还在
# 4. 如果还在，说明持久化成功！✅
```

---

## 📊 两种模式对比

| 特性 | 持久化模式 | 纯内存模式 |
|------|-----------|-----------|
| 数据存储位置 | Docker Volume | 容器内存 |
| 容器重启后 | ✅ 数据保留 | ❌ 数据丢失 |
| 容器删除后 | ✅ 数据保留 | ❌ 数据丢失 |
| 磁盘占用 | 有（取决于文档量） | 无 |
| 内存占用 | 低 | 高 |
| 性能 | 略低（有磁盘 I/O） | 略高 |
| 生产环境推荐 | ✅ 是 | ❌ 否 |
| 开发测试推荐 | ⚠️ 可选 | ✅ 是 |

---

## 🔍 常见问题

### Q1: 如何查看已保存的数据？

```bash
# 进入容器
docker compose exec backend bash

# 查看 ChromaDB 数据目录
ls -lh /app/chroma_data/

# 应该看到 chroma.sqlite3 等文件
```

### Q2: 如何清空知识库？

**方式 A：通过网页**（推荐）
- 重新上传文档并构建知识库（会覆盖旧数据）

**方式 B：删除 Volume**

```bash
# 停止容器
docker compose down

# 删除 volume（慎用！会删除所有数据）
docker volume rm ragenius_chroma_data

# 重新启动
docker compose up -d
```

### Q3: 如何备份知识库？

```bash
# 备份 volume
docker run --rm \
  -v ragenius_chroma_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/chroma_backup_$(date +%Y%m%d).tar.gz -C /data .

# 恢复 volume
docker run --rm \
  -v ragenius_chroma_data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/chroma_backup_20260103.tar.gz -C /data
```

### Q4: 持久化会占用多少磁盘空间？

大约是文档总大小的 **2-3 倍**：
- 原始文档
- 向量嵌入（每个 chunk ~1-2KB）
- ChromaDB 索引

示例：
- 10MB 文档 → 约 20-30MB 磁盘空间
- 100MB 文档 → 约 200-300MB 磁盘空间

### Q5: 之前的"隐式持久化"数据还在吗？

是的！在 `/tmp` 或其他临时目录。你可以：

```bash
# 查找旧数据
docker compose exec backend bash
find /tmp -name "chroma.sqlite3" 2>/dev/null

# 如果不需要，可以删除
rm -rf /tmp/.chroma* /tmp/chroma* 2>/dev/null
```

---

## 💡 推荐配置

### 生产环境（阿里云 ECS）

```bash
# .env
CHROMA_PERSIST_DIR=/app/chroma_data
```

### 开发环境（本地 Docker）

```bash
# .env
CHROMA_PERSIST_DIR=
# 或者
# CHROMA_PERSIST_DIR=/app/chroma_data
```

根据你的需求选择！

---

## 📝 简历加分点

使用持久化模式后，你可以在简历上写：

> - 实现 ChromaDB 向量数据库持久化，采用 Docker Volume 管理，确保生产环境数据安全
> - 设计可配置的存储模式（内存/持久化），支持不同部署场景的灵活切换

---

需要帮助随时说！🚀

