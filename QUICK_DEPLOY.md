# 快速部署指南（10 分钟上线）

这是最快速的部署方法，适合快速演示和小规模使用。

## 🚀 方案：VPS + Docker（推荐新手）

### 前提条件
- ✅ 已购买域名
- ✅ 有一张信用卡（用于购买 VPS）
- ✅ 基本的命令行使用经验

---

## 步骤 1: 购买服务器（5 分钟）

推荐：**DigitalOcean** 或 **Vultr**

### DigitalOcean（国际，稳定）

1. 访问：https://www.digitalocean.com/
2. 注册账号（新用户有 $200 免费额度）
3. 创建 Droplet：
   - **Image**: Ubuntu 22.04 LTS
   - **Plan**: Basic ($12/月)
     - 2 CPU
     - 4 GB RAM
     - 80 GB SSD
   - **Datacenter**: Singapore 或 San Francisco（选离你近的）
   - **Authentication**: SSH Key（推荐）或 Password

4. 等待 1-2 分钟，服务器创建完成
5. 记录服务器 IP 地址：`123.456.789.0`

### Vultr（有日本节点，国内快）

1. 访问：https://www.vultr.com/
2. 注册账号
3. Deploy New Server：
   - **Location**: Tokyo, Japan（东京节点国内快）
   - **Type**: Cloud Compute - Shared CPU
   - **Plan**: 4 GB RAM ($12/月)
   - **OS**: Ubuntu 22.04
4. 记录 IP 地址和密码

---

## 步骤 2: 配置域名（2 分钟）

在你的域名管理后台（如阿里云、腾讯云、Cloudflare）：

```
添加 A 记录：
主机记录: @           类型: A    记录值: 你的服务器IP
主机记录: www         类型: A    记录值: 你的服务器IP
```

**示例**（假设 IP 是 123.456.789.0）：
```
@ → 123.456.789.0
www → 123.456.789.0
```

保存后，DNS 解析需要 5-10 分钟生效。

---

## 步骤 3: 自动化部署脚本（3 分钟）

### 3.1 SSH 登录服务器

```bash
ssh root@你的服务器IP
```

输入密码（如果没用 SSH Key）。

### 3.2 运行一键部署脚本

**复制整个脚本，粘贴到终端，回车：**

```bash
#!/bin/bash
set -e

echo "╔═══════════════════════════════════════════════╗"
echo "║     RAGenius 一键部署脚本                    ║"
echo "╚═══════════════════════════════════════════════╝"
echo ""

# 1. 更新系统
echo "📦 更新系统..."
apt update && apt upgrade -y

# 2. 安装 Docker
echo "🐳 安装 Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
systemctl start docker
systemctl enable docker
rm get-docker.sh

# 3. 安装必要工具
echo "🔧 安装工具..."
apt install -y git nginx certbot python3-certbot-nginx ufw

# 4. 配置防火墙
echo "🔥 配置防火墙..."
ufw --force enable
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp

# 5. 克隆项目
echo "📥 克隆项目..."
cd /opt
git clone https://github.com/l1anch1/DeepSeek-RAG.git ragenius
cd ragenius

# 6. 配置环境变量
echo "⚙️  配置环境..."
cat > .env << 'ENV_EOF'
# LLM 配置（请稍后修改为你的真实 API Key）
LLM_USE_OPENAI=true
LLM_OPENAI_API_KEY=sk-YOUR-API-KEY-HERE
LLM_OPENAI_MODEL=gpt-4o

# Flask 环境
FLASK_ENV=production
DEVICE=cpu

# 其他配置使用默认值
ENV_EOF

# 7. 启动服务
echo "🚀 启动服务..."
docker compose up -d --build

# 8. 等待服务启动
echo "⏳ 等待服务启动..."
sleep 30

# 9. 测试服务
echo "🧪 测试服务..."
curl -f http://localhost:8000/api/health || echo "⚠️  后端未就绪"
curl -f http://localhost:3000 || echo "⚠️  前端未就绪"

# 10. 配置 Nginx
echo "🌐 配置 Nginx..."
cat > /etc/nginx/sites-available/ragenius << 'NGINX_EOF'
server {
    listen 80;
    server_name _;  # 先用下划线，稍后替换为你的域名

    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_buffering off;
        proxy_cache off;
    }

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
NGINX_EOF

ln -sf /etc/nginx/sites-available/ragenius /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

echo ""
echo "╔═══════════════════════════════════════════════╗"
echo "║          ✅ 部署完成！                        ║"
echo "╚═══════════════════════════════════════════════╝"
echo ""
echo "📝 下一步操作："
echo ""
echo "1. 修改 API Key："
echo "   nano /opt/ragenius/.env"
echo "   将 sk-YOUR-API-KEY-HERE 改为你的真实 OpenAI API Key"
echo "   保存后运行：cd /opt/ragenius && docker compose restart"
echo ""
echo "2. 配置域名："
echo "   nano /etc/nginx/sites-available/ragenius"
echo "   将 server_name _; 改为 server_name yourdomain.com www.yourdomain.com;"
echo "   保存后运行：nginx -t && systemctl restart nginx"
echo ""
echo "3. 配置 HTTPS："
echo "   certbot --nginx -d yourdomain.com -d www.yourdomain.com"
echo ""
echo "4. 访问你的网站："
echo "   http://你的服务器IP （临时访问）"
echo "   http://你的域名 （DNS 解析后）"
echo ""
echo "📚 完整文档：/opt/ragenius/DEPLOYMENT_GUIDE.md"
echo ""
```

脚本会自动完成所有配置！

---

## 步骤 4: 配置 API Key（1 分钟）

```bash
# 编辑环境变量
nano /opt/ragenius/.env
```

找到这行：
```
LLM_OPENAI_API_KEY=sk-YOUR-API-KEY-HERE
```

改为你的真实 OpenAI API Key：
```
LLM_OPENAI_API_KEY=sk-proj-abc123xyz...
```

按 `Ctrl+X`，然后 `Y`，然后 `Enter` 保存。

**重启服务**：
```bash
cd /opt/ragenius
docker compose restart
```

---

## 步骤 5: 配置域名和 HTTPS（5 分钟）

### 5.1 更新 Nginx 配置

```bash
nano /etc/nginx/sites-available/ragenius
```

将第一行的：
```
server_name _;
```

改为你的域名：
```
server_name yourproject.com www.yourproject.com;
```

保存并重启：
```bash
nginx -t
systemctl restart nginx
```

### 5.2 配置 SSL 证书

```bash
certbot --nginx -d yourproject.com -d www.yourproject.com
```

按提示：
1. 输入你的邮箱
2. 同意服务条款（输入 `Y`）
3. 选择是否重定向 HTTP 到 HTTPS（选 `2`，推荐）

完成！证书会自动续期。

---

## 步骤 6: 访问你的网站 ✨

打开浏览器，访问：
```
https://yourproject.com
```

你应该看到 RAGenius 的界面！

---

## 🔧 常用命令

```bash
# 查看服务状态
cd /opt/ragenius && docker compose ps

# 查看日志
docker compose logs -f

# 重启服务
docker compose restart

# 停止服务
docker compose down

# 启动服务
docker compose up -d

# 更新代码
git pull && docker compose up -d --build

# 查看 Nginx 状态
systemctl status nginx

# 重启 Nginx
systemctl restart nginx
```

---

## 🆘 问题排查

### 1. 无法访问网站
```bash
# 检查防火墙
ufw status

# 检查 Nginx
systemctl status nginx

# 检查容器
docker compose ps

# 查看日志
docker compose logs backend
docker compose logs frontend
```

### 2. SSL 证书失败
```bash
# 确保域名已解析（等待 10 分钟）
ping yourproject.com

# 重新申请证书
certbot --nginx -d yourproject.com -d www.yourproject.com
```

### 3. 服务启动失败
```bash
# 查看详细日志
docker compose logs backend

# 检查 .env 配置
cat /opt/ragenius/.env

# 重新构建
docker compose down
docker compose up -d --build
```

---

## 📊 监控和维护

### 查看资源使用
```bash
# 内存使用
free -h

# 磁盘使用
df -h

# Docker 资源
docker stats
```

### 自动备份（推荐）
```bash
# 创建备份脚本
cat > /opt/ragenius/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups"
mkdir -p $BACKUP_DIR
DATE=$(date +%Y%m%d_%H%M%S)
docker compose exec -T backend tar czf - /app/data > $BACKUP_DIR/data_$DATE.tar.gz
find $BACKUP_DIR -name "data_*.tar.gz" -mtime +7 -delete
EOF

chmod +x /opt/ragenius/backup.sh

# 设置每天备份
crontab -e
# 添加：0 2 * * * /opt/ragenius/backup.sh
```

---

## ✅ 部署检查清单

- [ ] 服务器创建完成
- [ ] 域名 DNS 解析配置
- [ ] Docker 和服务运行正常
- [ ] API Key 配置正确
- [ ] Nginx 配置正确
- [ ] SSL 证书配置成功
- [ ] 可以通过 HTTPS 访问
- [ ] 可以上传文档并提问

全部完成？恭喜你，网站已经上线了！🎉

---

## 💰 成本估算

- **服务器**: $12/月（DigitalOcean 4GB）
- **域名**: $10-15/年
- **SSL 证书**: 免费（Let's Encrypt）
- **总计**: ~$13/月

---

**需要帮助？** 参考完整的 [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) 或提交 Issue。

