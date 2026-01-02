# RAGenius 部署上线指南

## 🎯 部署方案概览

| 方案 | 难度 | 成本 | 适用场景 | 推荐度 |
|------|------|------|----------|--------|
| **方案 1: VPS + Docker** | ⭐⭐ 中等 | $5-20/月 | 完全控制 | ⭐⭐⭐⭐⭐ |
| **方案 2: Railway** | ⭐ 简单 | $5-10/月 | 快速上线 | ⭐⭐⭐⭐ |
| **方案 3: 云平台** | ⭐⭐⭐ 复杂 | $10-50/月 | 企业级 | ⭐⭐⭐ |

---

## 📋 准备工作

### 1. 域名配置（必须）

你已经有域名，需要配置 DNS：

```
A 记录配置：
主机记录     记录类型    记录值
@           A          你的服务器IP
www         A          你的服务器IP
api         A          你的服务器IP  (可选，用于后端)
```

**示例**：
- 域名：`yourproject.com`
- 前端：`https://yourproject.com`
- 后端：`https://api.yourproject.com` 或 `https://yourproject.com/api`

### 2. 环境变量准备

创建生产环境的 `.env` 文件：

```bash
# 复制示例文件
cp .env.example .env.production

# 编辑配置
nano .env.production
```

必需配置：
```env
# LLM 配置
LLM_USE_OPENAI=true
LLM_OPENAI_API_KEY=sk-your-real-api-key
LLM_OPENAI_MODEL=gpt-4o

# 或使用本地模型
LLM_USE_OPENAI=false
LLM_LOCAL_MODEL=deepseek-r1:14b

# Flask 环境
FLASK_ENV=production

# 其他配置
DEVICE=cpu  # 如果有 GPU 可以改为 cuda
```

---

## 🚀 方案 1: VPS + Docker 部署（推荐）

### 适用平台
- DigitalOcean (国际)
- Vultr (国际)
- Linode (国际)
- 阿里云 (国内)
- 腾讯云 (国内)
- Vultr (有日本、新加坡节点，国内访问快)

### 步骤 1.1: 创建服务器

**推荐配置**：
- CPU: 2 核心
- 内存: 4GB RAM（最低 2GB）
- 存储: 50GB SSD
- 系统: Ubuntu 22.04 LTS
- 月费: ~$12-20

**快速创建**（以 DigitalOcean 为例）：
1. 访问 https://www.digitalocean.com/
2. Create → Droplets
3. 选择 Ubuntu 22.04
4. 选择 Regular (2 CPU, 4GB RAM)
5. 选择离你最近的数据中心
6. 添加 SSH Key（推荐）

### 步骤 1.2: 初始服务器配置

SSH 登录服务器：
```bash
ssh root@your_server_ip
```

**1. 更新系统**
```bash
apt update && apt upgrade -y
```

**2. 安装 Docker**
```bash
# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 启动 Docker
systemctl start docker
systemctl enable docker

# 验证安装
docker --version
docker compose version
```

**3. 安装其他工具**
```bash
apt install -y git nginx certbot python3-certbot-nginx ufw
```

**4. 配置防火墙**
```bash
# 允许 SSH、HTTP、HTTPS
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### 步骤 1.3: 部署应用

**1. 克隆项目**
```bash
cd /opt
git clone https://github.com/l1anch1/DeepSeek-RAG.git ragenius
cd ragenius
```

**2. 配置环境变量**
```bash
# 复制环境变量文件
cp .env.example .env

# 编辑配置（使用 nano 或 vim）
nano .env
```

填入你的配置：
```env
LLM_USE_OPENAI=true
LLM_OPENAI_API_KEY=sk-your-actual-api-key-here
LLM_OPENAI_MODEL=gpt-4o
FLASK_ENV=production
```

**3. 启动服务**
```bash
# 构建并启动
docker compose up -d --build

# 查看日志
docker compose logs -f

# 查看运行状态
docker compose ps
```

**4. 测试服务**
```bash
# 测试后端
curl http://localhost:8000/api/health

# 测试前端
curl http://localhost:3000
```

### 步骤 1.4: 配置 Nginx 反向代理

**1. 创建 Nginx 配置**
```bash
nano /etc/nginx/sites-available/ragenius
```

**配置文件内容**：
```nginx
# 前端和后端在同一域名
server {
    listen 80;
    server_name yourproject.com www.yourproject.com;

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # 后端 API
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # SSE 支持（流式响应）
        proxy_buffering off;
        proxy_cache off;
    }

    # 前端
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

**2. 启用配置**
```bash
# 创建软链接
ln -s /etc/nginx/sites-available/ragenius /etc/nginx/sites-enabled/

# 测试配置
nginx -t

# 重启 Nginx
systemctl restart nginx
```

### 步骤 1.5: 配置 HTTPS (SSL 证书)

**使用 Let's Encrypt（免费）**：
```bash
# 自动配置 SSL
certbot --nginx -d yourproject.com -d www.yourproject.com

# 按提示输入邮箱
# 选择是否重定向 HTTP 到 HTTPS（推荐选是）

# 测试自动续期
certbot renew --dry-run
```

证书会自动续期，无需手动操作。

### 步骤 1.6: 验证部署

访问你的域名：
```
https://yourproject.com
```

应该能看到前端界面！

---

## 🚄 方案 2: Railway 快速部署（最简单）

Railway 是一个现代化的部署平台，支持自动 CI/CD。

### 步骤 2.1: 准备项目

**1. 创建 railway.json**
```bash
cat > railway.json << 'EOF'
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE"
  },
  "deploy": {
    "startCommand": "docker-compose up",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
EOF
```

**2. 准备 Dockerfile（已有，无需修改）**

### 步骤 2.2: 部署到 Railway

**1. 注册 Railway**
- 访问 https://railway.app/
- 使用 GitHub 账号登录

**2. 创建新项目**
```
New Project → Deploy from GitHub repo → 选择你的仓库
```

**3. 配置环境变量**
在 Railway 项目中：
- 点击服务 → Variables
- 添加环境变量：
  ```
  LLM_USE_OPENAI=true
  LLM_OPENAI_API_KEY=sk-your-key
  LLM_OPENAI_MODEL=gpt-4o
  FLASK_ENV=production
  ```

**4. 配置域名**
- Settings → Domains
- Add Custom Domain
- 输入你的域名
- 在域名 DNS 配置 CNAME 记录（Railway 会提供）

**5. 部署**
- Railway 会自动检测 Dockerfile
- 自动构建和部署
- 每次 push 到 main 都会自动部署

---

## ☁️ 方案 3: 云平台部署（企业级）

### AWS / Azure / Google Cloud 部署要点

**架构**：
```
[Load Balancer] → [Container Service] → [Database]
                          ↓
                    [File Storage]
```

**步骤**：
1. 创建容器注册表（ECR / ACR / GCR）
2. 推送 Docker 镜像
3. 创建容器服务（ECS / AKS / GKE）
4. 配置负载均衡器
5. 配置自动扩展
6. 配置监控和日志

详细步骤较复杂，建议查看各平台官方文档。

---

## 🔧 部署后配置

### 1. 配置持久化存储

**修改 docker-compose.yml**：
```yaml
volumes:
  # 持久化向量数据库
  vectordb_data:
    driver: local
  # 持久化模型缓存
  models_cache:
    driver: local
  # 持久化上传的文档
  documents_data:
    driver: local

services:
  backend:
    volumes:
      - vectordb_data:/app/data/vectordb
      - models_cache:/app/models_cache
      - documents_data:/app/data/documents
```

### 2. 配置备份脚本

创建 `backup.sh`：
```bash
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# 备份数据
docker compose exec -T backend tar czf - /app/data | gzip > $BACKUP_DIR/data_$DATE.tar.gz

# 保留最近 7 天的备份
find $BACKUP_DIR -name "data_*.tar.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR/data_$DATE.tar.gz"
```

设置定时任务：
```bash
# 编辑 crontab
crontab -e

# 添加每天凌晨 2 点备份
0 2 * * * /opt/ragenius/backup.sh
```

### 3. 配置日志

创建 `docker-compose.override.yml`：
```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
  
  frontend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 4. 配置监控（可选）

**简单监控**：
```bash
# 安装监控工具
docker run -d --name=netdata \
  -p 19999:19999 \
  -v /proc:/host/proc:ro \
  -v /sys:/host/sys:ro \
  --cap-add SYS_PTRACE \
  --security-opt apparmor=unconfined \
  netdata/netdata
```

访问 `http://your-ip:19999` 查看监控。

---

## 📊 性能优化

### 1. 使用 CDN（可选）

**Cloudflare（免费）**：
1. 注册 Cloudflare
2. 添加你的域名
3. 更新域名 DNS 到 Cloudflare
4. 启用 CDN 和缓存

### 2. 数据库优化

如果使用量大，考虑：
- 使用独立的 PostgreSQL 数据库
- 配置连接池
- 添加 Redis 缓存

### 3. 扩展部署

**水平扩展**：
```yaml
services:
  backend:
    deploy:
      replicas: 3  # 运行 3 个实例
```

配合负载均衡器使用。

---

## 🔒 安全加固

### 1. 更新 Nginx 配置

添加安全头：
```nginx
# 在 server 块中添加
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;

# 限制请求大小
client_max_body_size 50M;

# 限制请求频率
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
location /api/ {
    limit_req zone=api burst=20;
}
```

### 2. 配置防火墙

```bash
# 只允许必要的端口
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### 3. 定期更新

```bash
# 创建更新脚本
cat > /opt/ragenius/update.sh << 'EOF'
#!/bin/bash
cd /opt/ragenius
git pull
docker compose down
docker compose up -d --build
docker system prune -f
EOF

chmod +x /opt/ragenius/update.sh
```

---

## 📋 部署检查清单

部署完成后，检查以下项目：

- [ ] 域名正确解析到服务器
- [ ] HTTPS 证书配置成功（绿色锁）
- [ ] 前端可以正常访问
- [ ] 后端 API 可以正常响应
- [ ] 可以上传文档
- [ ] 可以提问并获得回答
- [ ] 流式响应正常工作
- [ ] 日志正常记录
- [ ] 备份脚本配置完成
- [ ] 防火墙规则正确
- [ ] SSL 证书自动续期配置
- [ ] 监控系统运行（如果配置）

---

## 🆘 常见问题

### 1. 端口冲突
```bash
# 查看端口占用
netstat -tulpn | grep :8000

# 停止占用端口的进程
kill -9 <PID>
```

### 2. Docker 容器无法启动
```bash
# 查看日志
docker compose logs backend
docker compose logs frontend

# 重新构建
docker compose down
docker compose build --no-cache
docker compose up -d
```

### 3. 内存不足
```bash
# 查看内存使用
free -h

# 增加 swap
fallocate -l 4G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

### 4. SSL 证书更新失败
```bash
# 手动更新
certbot renew

# 查看证书状态
certbot certificates
```

---

## 📞 获取帮助

- 📖 项目文档：[README.md](./README.md)
- 🐛 提交 Issue：https://github.com/l1anch1/DeepSeek-RAG/issues
- 📧 Email：asherlii@outlook.com

---

**祝部署顺利！** 🎉

