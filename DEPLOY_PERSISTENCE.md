# 🚀 在阿里云 ECS 启用数据持久化

## ⚡ 一键部署脚本

复制粘贴以下命令到你的阿里云 ECS 终端：

```bash
cd /opt/ragenius

# 1. 拉取最新代码
git pull

# 2. 配置持久化（默认已启用）
# 无需修改 .env，已经包含默认配置

# 3. 重新部署
docker compose down
docker compose up -d --build

# 4. 验证
echo "等待容器启动..."
sleep 30

# 5. 检查日志
docker compose logs -f backend | head -50
```

---

## ✅ 验证持久化是否生效

### 方法 1：检查 Volume

```bash
# 查看 volume 列表
docker volume ls | grep chroma

# 应该看到：
# local     ragenius_chroma_data
```

### 方法 2：查看数据目录

```bash
# 进入容器
docker compose exec backend bash

# 查看持久化目录
ls -lh /app/chroma_data/

# 应该看到类似输出（在你上传文档后）：
# drwxr-xr-x 2 root root 4.0K Jan  3 12:00 chroma.sqlite3
# -rw-r--r-- 1 root root  20K Jan  3 12:00 ...
```

### 方法 3：测试数据持久化

```bash
# 1. 在网页上上传文档并构建知识库
# 2. 查询一个问题，记住答案
# 3. 重启容器：
docker compose restart

# 4. 等待 30 秒后刷新网页
# 5. 再次查询相同问题
# 6. 如果能得到相同答案，说明持久化成功！✅
```

---

## 📊 配置说明

### 当前配置（持久化模式）

在 `docker-compose.yml` 中：

```yaml
environment:
  - CHROMA_PERSIST_DIR=/app/chroma_data  # 持久化路径

volumes:
  - chroma_data:/app/chroma_data  # Docker Volume 映射
```

### 数据存储位置

```bash
# 宿主机（阿里云 ECS）路径：
/var/lib/docker/volumes/ragenius_chroma_data/_data

# 容器内路径：
/app/chroma_data
```

---

## 🔄 切换到内存模式（可选）

如果你想要内存模式（容器重启后数据丢失）：

### 方式 1：通过 .env（推荐）

```bash
nano /opt/ragenius/.env
```

添加或修改：

```bash
CHROMA_PERSIST_DIR=
```

然后重启：

```bash
docker compose down
docker compose up -d
```

### 方式 2：修改 docker-compose.yml

```bash
nano /opt/ragenius/docker-compose.yml
```

注释掉持久化配置：

```yaml
environment:
  - CHROMA_PERSIST_DIR=  # 留空启用内存模式

volumes:
  - models_cache:/app/models_cache
  # - chroma_data:/app/chroma_data  # 注释掉
```

---

## 🧹 清空知识库

### 方法 1：通过网页（推荐）

直接重新上传文档并构建知识库，会自动覆盖旧数据。

### 方法 2：删除 Volume

```bash
# 停止容器
docker compose down

# 删除 volume（慎用！会删除所有知识库数据）
docker volume rm ragenius_chroma_data

# 重新启动
docker compose up -d
```

---

## 💾 备份知识库

### 备份

```bash
cd /opt/ragenius

# 创建备份
docker run --rm \
  -v ragenius_chroma_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/chroma_backup_$(date +%Y%m%d_%H%M%S).tar.gz -C /data .

echo "备份完成！文件保存在当前目录"
ls -lh chroma_backup_*.tar.gz
```

### 恢复

```bash
cd /opt/ragenius

# 列出备份文件
ls -lh chroma_backup_*.tar.gz

# 停止容器
docker compose down

# 恢复指定备份（替换日期时间）
docker run --rm \
  -v ragenius_chroma_data:/data \
  -v $(pwd):/backup \
  alpine sh -c "rm -rf /data/* && tar xzf /backup/chroma_backup_20260103_120000.tar.gz -C /data"

# 重新启动
docker compose up -d

echo "恢复完成！"
```

---

## 📈 磁盘空间管理

### 查看 Volume 占用空间

```bash
# 查看所有 volumes 大小
docker system df -v | grep ragenius

# 或者直接查看目录大小
sudo du -sh /var/lib/docker/volumes/ragenius_chroma_data/_data
```

### 预估空间需求

| 文档大小 | 预估 Volume 大小 |
|---------|----------------|
| 10 MB   | ~20-30 MB     |
| 100 MB  | ~200-300 MB   |
| 1 GB    | ~2-3 GB       |

---

## 🔍 故障排查

### 问题 1：重启后数据丢失

**可能原因**：
1. `CHROMA_PERSIST_DIR` 未配置
2. Volume 未正确挂载

**解决方案**：

```bash
# 检查环境变量
docker compose exec backend bash -c 'echo $CHROMA_PERSIST_DIR'
# 应该输出：/app/chroma_data

# 检查 volume
docker volume ls | grep chroma
# 应该看到：ragenius_chroma_data

# 检查挂载
docker compose exec backend df -h | grep chroma
# 应该看到：/app/chroma_data
```

### 问题 2：数据占用空间过大

**解决方案**：

```bash
# 1. 删除旧数据
docker compose down
docker volume rm ragenius_chroma_data

# 2. 重新构建（只上传必要文档）
docker compose up -d

# 3. 定期清理不需要的知识库
```

### 问题 3：无法写入数据

**可能原因**：权限问题

**解决方案**：

```bash
# 检查容器内权限
docker compose exec backend ls -ld /app/chroma_data
# 应该显示：drwxr-xr-x

# 如果权限不对，进入容器修复
docker compose exec backend chmod 755 /app/chroma_data
```

---

## 📝 简历加分点

配置持久化后，你可以在简历上写：

> **数据持久化与容器化部署**
> - 实现 ChromaDB 向量数据库持久化方案，采用 Docker Volume 管理数据生命周期
> - 设计灵活的存储模式配置（内存/持久化），支持不同部署场景
> - 实现生产环境数据备份与恢复机制，确保知识库数据安全

---

## 🎯 快速参考

```bash
# 查看配置
docker compose config | grep -A 5 CHROMA

# 查看日志
docker compose logs backend | grep -i chroma

# 进入容器检查
docker compose exec backend bash
ls -lh /app/chroma_data/

# 重启服务
docker compose restart backend

# 完全重新部署
docker compose down && docker compose up -d --build
```

---

需要帮助随时说！🚀

