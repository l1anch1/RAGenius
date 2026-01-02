# 🚀 阿里云 ECS 完整部署指南

> **详细的阿里云 ECS 部署教程，从购买服务器到上线全流程**

---

## 📋 目录

- [选择方案](#选择方案)
- [购买服务器](#购买服务器)
- [初始化服务器](#初始化服务器)
- [一键部署](#一键部署)
- [配置 API Key](#配置-api-key)
- [配置域名](#配置域名)
- [配置 HTTPS](#配置-https)
- [验证部署](#验证部署)
- [常见问题](#常见问题)

---

## 📊 选择方案

阿里云 ECS 有 3 个选择：

| 方案 | 是否需要备案 | 速度（国内） | 价格/月 | 推荐度 |
|------|-------------|-------------|---------|--------|
| **阿里云香港** | ❌ 不需要 | ⚡⚡⚡⚡⚡ | ¥60+ | ⭐⭐⭐⭐⭐ |
| 阿里云国内 | ✅ 需要 | ⚡⚡⚡⚡⚡ | ¥50+ | ⭐⭐⭐ |
| 阿里云海外 | ❌ 不需要 | ⚡⚡⚡ | $8+ | ⭐⭐⭐⭐ |

### 💡 推荐：阿里云香港

**优势：**
- ✅ **无需备案**：省去繁琐的备案流程
- ⚡ **速度快**：延迟 10-50ms（比国外服务器快）
- 🇨🇳 **中文界面**：操作简单
- 💳 **支付方便**：支持支付宝、微信

---

## 🛒 购买服务器

### 步骤 1：访问阿里云

访问：https://www.aliyun.com/product/ecs

### 步骤 2：选择配置

#### 推荐配置（¥60-80/月）

**基础配置：**
- **地域**：香港（重要！）
- **实例规格**：
  - CPU: 2核
  - 内存: 4GB
  - 推荐：`ecs.t6-c1m2.large` 或 `ecs.n4.large`
- **镜像**：Ubuntu 22.04 64位
- **存储**：40GB 高效云盘
- **带宽**：5Mbps（可按需调整）

#### 详细选择步骤

1. **选择地域和可用区**
   ```
   地域：中国香港
   可用区：随机分配（默认即可）
   ```

2. **选择实例**
   ```
   分类：共享标准型
   实例规格：
   - ecs.t6-c1m2.large (2核4GB) - 推荐
   - ecs.n4.large (2核4GB) - 备选
   ```

3. **选择镜像**
   ```
   镜像类型：公共镜像
   操作系统：Ubuntu
   版本：Ubuntu 22.04 64位
   ```

4. **选择存储**
   ```
   系统盘：高效云盘 40GB
   数据盘：不需要（可选）
   ```

5. **配置网络**
   ```
   网络：默认专有网络
   公网 IP：分配
   带宽计费模式：按使用流量
   带宽峰值：5Mbps
   ```

6. **设置安全组**
   ```
   勾选以下端口：
   ✅ 22 (SSH)
   ✅ 80 (HTTP)
   ✅ 443 (HTTPS)
   ```

### 步骤 3：设置实例信息

1. **实例名称**：`ragenius-prod`（可自定义）
2. **登录凭证**：
   - **方式 1（推荐）**：密钥对（更安全）
     - 创建新密钥对：`ragenius-key`
     - 下载 `.pem` 文件并妥善保存
   - **方式 2**：自定义密码
     - 设置一个强密码（至少 8 位，包含大小写字母、数字、特殊字符）

### 步骤 4：确认订单

- 购买时长：建议 1 个月（测试）或 1 年（打折）
- 勾选服务协议
- 点击"立即购买"
- 完成支付

### 💰 费用估算

| 配置 | 月付 | 年付（约 8.5 折） |
|------|------|------------------|
| 2核4GB 5Mbps | ¥70 | ¥714 (¥59.5/月) |
| 2核8GB 5Mbps | ¥100 | ¥1020 (¥85/月) |

---

## 🔑 初始化服务器

### 步骤 1：获取服务器信息

1. 登录阿里云控制台
2. 进入 **云服务器 ECS** → **实例列表**
3. 找到你的实例，记录：
   - **公网 IP**：123.456.789.0
   - **登录用户名**：root（Ubuntu 默认）

### 步骤 2：连接服务器

#### 方式 1：使用密钥对（推荐）

```bash
# 1. 修改密钥文件权限
chmod 400 ~/Downloads/ragenius-key.pem

# 2. SSH 连接
ssh -i ~/Downloads/ragenius-key.pem root@你的服务器IP
```

#### 方式 2：使用密码

```bash
ssh root@你的服务器IP
# 输入密码
```

#### 方式 3：使用阿里云网页终端

1. 在实例列表中找到你的服务器
2. 点击右侧 **远程连接** → **VNC 登录**
3. 输入密码登录

### 步骤 3：更新系统（可选）

```bash
# 首次登录后，建议更新系统
apt update && apt upgrade -y
```

---

## ⚡ 一键部署

### 方法 1：直接运行（推荐）

```bash
# 复制以下命令，在服务器终端粘贴运行
bash <(curl -fsSL https://raw.githubusercontent.com/l1anch1/DeepSeek-RAG/main/deploy_aliyun.sh)
```

### 方法 2：下载后运行

```bash
# 1. 下载脚本
wget https://raw.githubusercontent.com/l1anch1/DeepSeek-RAG/main/deploy_aliyun.sh

# 2. 添加执行权限
chmod +x deploy_aliyun.sh

# 3. 运行脚本
./deploy_aliyun.sh
```

### 方法 3：手动复制粘贴

1. 在本地打开 `deploy_aliyun.sh` 文件
2. 复制全部内容（Cmd+A, Cmd+C）
3. 在服务器终端输入：
   ```bash
   cat > deploy.sh
   ```
4. 粘贴脚本内容（Cmd+V）
5. 按 `Ctrl+D` 保存
6. 运行：
   ```bash
   bash deploy.sh
   ```

### ⏱️ 部署过程

脚本会自动完成以下操作（约 5-10 分钟）：

```
[1/11] 检测系统信息          ✅
[2/11] 配置阿里云镜像源      ⚡ 加速下载
[3/11] 更新系统              📦
[4/11] 安装 Docker           🐳
[5/11] 配置 Docker 镜像加速  ⚡
[6/11] 安装必要工具          🔧
[7/11] 配置防火墙            🔥
[8/11] 克隆项目代码          📥
[9/11] 创建配置文件          ⚙️
[10/11] 启动服务             🚀 (需要 3-5 分钟)
[11/11] 配置 Nginx           🌐
```

部署完成后，你会看到：

```
╔═══════════════════════════════════════════════════════════════╗
║                    ✅ 部署完成！                              ║
╚═══════════════════════════════════════════════════════════════╝
```

---

## 🔑 配置 API Key

### ⚠️ 重要：必须配置 API Key，否则无法使用！

```bash
# 1. 编辑配置文件
nano /opt/ragenius/.env

# 2. 找到这行：
LLM_OPENAI_API_KEY=sk-YOUR-API-KEY-HERE

# 3. 改为你的真实 API Key：
LLM_OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx

# 4. 保存：Ctrl+O 回车
# 5. 退出：Ctrl+X
```

### 重启服务使配置生效

```bash
cd /opt/ragenius
docker compose restart
```

### 验证 API Key 配置

```bash
# 查看日志，确认没有 API Key 错误
docker compose logs backend | grep -i "api"
```

---

## 🌐 配置域名（推荐）

### 步骤 1：添加 DNS 解析

在你的域名管理后台（如阿里云域名控制台）：

1. 进入 **域名解析**
2. 添加 **A 记录**：
   ```
   记录类型: A
   主机记录: @
   解析线路: 默认
   记录值: 你的服务器公网IP
   TTL: 600（10分钟）
   ```
3. 添加 **www 记录**（可选）：
   ```
   记录类型: A
   主机记录: www
   解析线路: 默认
   记录值: 你的服务器公网IP
   TTL: 600
   ```

### 步骤 2：修改 Nginx 配置

```bash
# 1. 编辑 Nginx 配置
nano /etc/nginx/sites-available/ragenius

# 2. 找到这行：
server_name _;

# 3. 改为你的域名：
server_name yourdomain.com www.yourdomain.com;

# 4. 保存：Ctrl+O 回车
# 5. 退出：Ctrl+X
```

### 步骤 3：测试并重启 Nginx

```bash
# 测试配置
nginx -t

# 重启 Nginx
systemctl restart nginx
```

### 步骤 4：等待 DNS 生效

```bash
# 测试域名解析（5-10 分钟后）
ping yourdomain.com

# 或使用
nslookup yourdomain.com
```

---

## 🔒 配置 HTTPS（推荐）

### 前提条件

- ✅ 域名已配置并解析生效
- ✅ Nginx 已配置域名
- ✅ 80 和 443 端口已开放

### 步骤 1：安装 SSL 证书

```bash
# 运行 Certbot（已在部署脚本中安装）
certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### 步骤 2：按提示操作

```
1. 输入邮箱地址（用于证书续期提醒）
2. 同意服务条款：Y
3. 是否接收推广邮件：N
4. 重定向 HTTP 到 HTTPS：选择 2 (推荐)
```

### 步骤 3：验证 HTTPS

```bash
# 测试 HTTPS 访问
curl -I https://yourdomain.com

# 应该返回 200 OK
```

### 自动续期

Certbot 会自动配置证书续期，测试续期：

```bash
# 测试自动续期
certbot renew --dry-run
```

---

## ✅ 验证部署

### 1. 检查服务状态

```bash
cd /opt/ragenius
docker compose ps
```

**期望输出：**
```
NAME                STATUS              PORTS
backend             running (healthy)   0.0.0.0:8000->8000/tcp
frontend            running             0.0.0.0:3000->3000/tcp
chroma_db           running             0.0.0.0:8001->8001/tcp
```

### 2. 测试后端 API

```bash
# 本地测试
curl http://localhost:8000/api/health

# 应该返回
{"status":"healthy","timestamp":"2025-01-02T10:00:00Z"}
```

### 3. 测试前端

在浏览器打开：
- 如果配置了域名：https://yourdomain.com
- 如果没有域名：http://你的服务器IP

### 4. 测试功能

1. **上传文档**
   - 点击"上传文档"
   - 选择 PDF/TXT/MD 文件
   - 确认上传成功

2. **提问测试**
   - 输入问题："这个文档的主要内容是什么？"
   - 查看是否有流式响应
   - 确认答案质量

3. **查看日志**
   ```bash
   cd /opt/ragenius
   docker compose logs -f backend
   ```

---

## 📊 性能监控

### 查看系统资源

```bash
# 实时监控
htop

# 查看内存使用
free -h

# 查看磁盘使用
df -h

# 查看 Docker 容器资源
docker stats
```

### 查看日志

```bash
# 所有服务日志
docker compose logs -f

# 后端日志
docker compose logs -f backend

# 前端日志
docker compose logs -f frontend

# Nginx 日志
tail -f /var/log/nginx/ragenius_access.log
tail -f /var/log/nginx/ragenius_error.log
```

---

## 🔧 常用操作

### 重启服务

```bash
cd /opt/ragenius

# 重启所有服务
docker compose restart

# 重启单个服务
docker compose restart backend
```

### 停止服务

```bash
cd /opt/ragenius
docker compose down
```

### 启动服务

```bash
cd /opt/ragenius
docker compose up -d
```

### 更新代码

```bash
cd /opt/ragenius

# 拉取最新代码
git pull

# 重新构建并启动
docker compose up -d --build
```

### 清理日志

```bash
# 清理 Docker 日志
docker compose down
docker system prune -af --volumes

# 清理 Nginx 日志
echo "" > /var/log/nginx/ragenius_access.log
echo "" > /var/log/nginx/ragenius_error.log
```

---

## ❓ 常见问题

### Q1: 服务启动失败

**症状：** `docker compose ps` 显示服务 `Exited`

**解决方法：**
```bash
# 1. 查看日志
docker compose logs backend

# 2. 常见原因：
# - API Key 未配置或无效
# - 端口被占用
# - 内存不足

# 3. 检查配置
nano /opt/ragenius/.env

# 4. 重启服务
docker compose restart
```

### Q2: 前端无法访问

**症状：** 浏览器显示 502 Bad Gateway

**解决方法：**
```bash
# 1. 检查 Nginx 状态
systemctl status nginx

# 2. 检查服务状态
docker compose ps

# 3. 检查 Nginx 配置
nginx -t

# 4. 查看 Nginx 日志
tail -f /var/log/nginx/ragenius_error.log

# 5. 重启 Nginx
systemctl restart nginx
```

### Q3: API 调用失败

**症状：** 前端页面报错 "Failed to fetch"

**解决方法：**
```bash
# 1. 检查 API Key
nano /opt/ragenius/.env
# 确认 LLM_OPENAI_API_KEY 已配置

# 2. 测试 API
curl http://localhost:8000/api/health

# 3. 查看后端日志
docker compose logs backend | tail -50

# 4. 重启后端
docker compose restart backend
```

### Q4: HTTPS 证书申请失败

**症状：** Certbot 报错

**解决方法：**
```bash
# 1. 检查域名解析
ping yourdomain.com

# 2. 检查 80 端口是否开放
netstat -tuln | grep :80

# 3. 检查防火墙
ufw status

# 4. 重试申请
certbot --nginx -d yourdomain.com --dry-run
```

### Q5: 内存不足

**症状：** 服务频繁重启，系统卡顿

**解决方法：**
```bash
# 1. 查看内存使用
free -h

# 2. 限制容器内存（编辑 docker-compose.yml）
nano /opt/ragenius/docker-compose.yml

# 添加：
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G

# 3. 重启服务
docker compose up -d

# 4. 考虑升级服务器配置
```

### Q6: 上传文件失败

**症状：** 文件上传卡住或失败

**解决方法：**
```bash
# 1. 检查文件大小限制
nano /etc/nginx/sites-available/ragenius
# 确认：client_max_body_size 50M;

# 2. 重启 Nginx
systemctl restart nginx

# 3. 检查磁盘空间
df -h

# 4. 清理空间
docker system prune -f
```

---

## 🔐 安全建议

### 1. 修改 SSH 端口（可选）

```bash
# 编辑 SSH 配置
nano /etc/ssh/sshd_config

# 修改端口（例如改为 2222）
Port 2222

# 重启 SSH
systemctl restart sshd

# 记得在防火墙开放新端口
ufw allow 2222/tcp
```

### 2. 禁用 root 密码登录

```bash
# 编辑 SSH 配置
nano /etc/ssh/sshd_config

# 修改以下选项
PermitRootLogin prohibit-password
PasswordAuthentication no

# 重启 SSH
systemctl restart sshd
```

### 3. 配置防火墙

```bash
# 查看当前规则
ufw status numbered

# 只允许必要的端口
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS

# 删除其他规则
ufw delete [规则号]
```

### 4. 定期更新系统

```bash
# 创建更新脚本
cat > /root/update.sh << 'EOF'
#!/bin/bash
apt update && apt upgrade -y
apt autoremove -y
docker system prune -f
EOF

chmod +x /root/update.sh

# 定期运行（例如每周日）
crontab -e
# 添加：0 3 * * 0 /root/update.sh
```

---

## 📈 性能优化

### 1. 启用 Nginx 缓存

```bash
nano /etc/nginx/sites-available/ragenius

# 在 http 块添加
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m inactive=60m;

# 在 location / 添加
proxy_cache my_cache;
proxy_cache_valid 200 1h;
```

### 2. 优化 Docker

```bash
# 编辑 docker-compose.yml
nano /opt/ragenius/docker-compose.yml

# 添加资源限制
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1.5'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G
```

### 3. 启用 gzip 压缩

```bash
nano /etc/nginx/nginx.conf

# 确保启用
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css application/json application/javascript;
```

---

## 📚 相关文档

- [项目 README](../README.md)
- [快速部署指南](../QUICK_DEPLOY.md)
- [通用部署指南](../DEPLOYMENT_GUIDE.md)
- [无需备案方案对比](../NO_BEIAN_DEPLOY.md)

---

## 🆘 需要帮助？

- 📧 Email: asherlii@outlook.com
- 💬 提交 Issue: https://github.com/l1anch1/DeepSeek-RAG/issues
- 📖 阿里云文档: https://help.aliyun.com/product/25365.html

---

## ✅ 部署检查清单

完成部署后，确认以下项目：

- [ ] 阿里云 ECS 已购买（香港节点，2核4GB）
- [ ] 已配置安全组（22, 80, 443 端口）
- [ ] 已 SSH 连接到服务器
- [ ] 一键部署脚本执行成功
- [ ] Docker 服务正常运行
- [ ] 已配置 OpenAI API Key
- [ ] 已测试后端 API (http://localhost:8000/api/health)
- [ ] 已测试前端访问 (http://服务器IP)
- [ ] Nginx 反向代理配置正确
- [ ] （可选）域名已配置并解析生效
- [ ] （可选）HTTPS 证书已配置
- [ ] 所有功能测试通过

---

**🎉 恭喜！你的 RAGenius 已成功部署到阿里云！**

