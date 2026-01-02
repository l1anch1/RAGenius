#!/bin/bash
# RAGenius 阿里云 ECS 一键部署脚本
# 支持：阿里云香港/海外/国内 ECS
# 系统：Ubuntu 20.04 / 22.04
# 使用方法：ssh root@your-ip，然后运行此脚本

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_header() {
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  $1"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
}

print_step() {
    echo -e "\n${GREEN}[$(date '+%H:%M:%S')]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# 检查是否为 root 用户
if [[ $EUID -ne 0 ]]; then
   print_error "此脚本需要 root 权限运行"
   echo "请使用: sudo bash $0"
   exit 1
fi

# 欢迎界面
clear
print_header "RAGenius 一键部署脚本 - 阿里云 ECS 优化版"
echo ""
echo "  系统要求："
echo "    • Ubuntu 20.04 / 22.04"
echo "    • 至少 2GB RAM（推荐 4GB）"
echo "    • 至少 20GB 磁盘空间"
echo ""
echo "  预计耗时：5-10 分钟（取决于网络速度）"
echo ""
read -p "$(echo -e ${YELLOW}🤔 确认开始部署? \(y/n\) ${NC})" -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_error "部署已取消"
    exit 0
fi

print_success "开始部署..."

# ============================================
# 1. 检测系统信息
# ============================================
print_step "[1/11] 检测系统信息..."

OS_VERSION=$(lsb_release -rs)
OS_CODENAME=$(lsb_release -cs)
CPU_CORES=$(nproc)
TOTAL_RAM=$(free -h | awk '/^Mem:/ {print $2}')

echo "  • 操作系统: Ubuntu $OS_VERSION ($OS_CODENAME)"
echo "  • CPU 核心: $CPU_CORES"
echo "  • 内存: $TOTAL_RAM"

# 检查内存
TOTAL_RAM_MB=$(free -m | awk '/^Mem:/ {print $2}')
if [ "$TOTAL_RAM_MB" -lt 1800 ]; then
    print_warning "内存不足 2GB，可能影响性能"
    read -p "是否继续? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

print_success "系统检测完成"

# ============================================
# 2. 配置阿里云镜像源（加速下载）
# ============================================
print_step "[2/11] 配置阿里云镜像源..."

# 备份原始源
cp /etc/apt/sources.list /etc/apt/sources.list.backup.$(date +%Y%m%d_%H%M%S)

# 根据 Ubuntu 版本配置镜像源
if [ "$OS_CODENAME" = "jammy" ]; then
    cat > /etc/apt/sources.list << 'EOF'
deb http://mirrors.aliyun.com/ubuntu/ jammy main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ jammy-security main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ jammy-updates main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ jammy-backports main restricted universe multiverse
EOF
elif [ "$OS_CODENAME" = "focal" ]; then
    cat > /etc/apt/sources.list << 'EOF'
deb http://mirrors.aliyun.com/ubuntu/ focal main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ focal-security main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ focal-updates main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ focal-backports main restricted universe multiverse
EOF
else
    print_warning "不支持的 Ubuntu 版本，跳过镜像源配置"
fi

print_success "镜像源配置完成"

# ============================================
# 3. 更新系统
# ============================================
print_step "[3/11] 更新系统包..."

export DEBIAN_FRONTEND=noninteractive
apt update -qq || { print_error "系统更新失败"; exit 1; }
apt upgrade -y -qq || { print_error "系统升级失败"; exit 1; }

print_success "系统更新完成"

# ============================================
# 4. 安装 Docker（使用阿里云镜像）
# ============================================
print_step "[4/11] 安装 Docker..."

# 检查是否已安装 Docker
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    print_warning "Docker 已安装: $DOCKER_VERSION"
    read -p "是否重新安装? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
    else
        print_success "跳过 Docker 安装"
        skip_docker=true
    fi
fi

if [ "$skip_docker" != "true" ]; then
    # 安装依赖
    apt install -y -qq \
        apt-transport-https \
        ca-certificates \
        curl \
        software-properties-common \
        gnupg \
        lsb-release

    # 添加 Docker 官方 GPG key（使用阿里云镜像）
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://mirrors.aliyun.com/docker-ce/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

    # 添加 Docker 阿里云仓库
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://mirrors.aliyun.com/docker-ce/linux/ubuntu \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

    # 安装 Docker
    apt update -qq
    apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

    # 启动 Docker
    systemctl start docker
    systemctl enable docker

    print_success "Docker 安装完成: $(docker --version)"
else
    systemctl start docker
    systemctl enable docker
fi

# ============================================
# 5. 配置 Docker 镜像加速
# ============================================
print_step "[5/11] 配置 Docker 镜像加速..."

mkdir -p /etc/docker
cat > /etc/docker/daemon.json << 'EOF'
{
  "registry-mirrors": [
    "https://registry.docker-cn.com",
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.ccs.tencentyun.com"
  ],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "live-restore": true
}
EOF

systemctl daemon-reload
systemctl restart docker

print_success "Docker 镜像加速配置完成"

# 验证 Docker 安装
docker run --rm hello-world > /dev/null 2>&1 && print_success "Docker 运行正常" || print_warning "Docker 测试失败"

# ============================================
# 6. 安装必要工具
# ============================================
print_step "[6/11] 安装必要工具..."

apt install -y -qq \
    git \
    nginx \
    certbot \
    python3-certbot-nginx \
    ufw \
    wget \
    curl \
    vim \
    htop \
    net-tools

print_success "工具安装完成"

# ============================================
# 7. 配置防火墙
# ============================================
print_step "[7/11] 配置防火墙..."

# 检查是否已启用 UFW
if ufw status | grep -q "Status: active"; then
    print_warning "UFW 已启用，跳过配置"
else
    ufw --force enable
    ufw allow ssh
    ufw allow 80/tcp
    ufw allow 443/tcp
    print_success "防火墙配置完成"
fi

echo "  当前防火墙状态："
ufw status numbered | head -n 10

# ============================================
# 8. 克隆项目
# ============================================
print_step "[8/11] 克隆项目代码..."

cd /opt

# 如果目录已存在，询问是否备份
if [ -d "ragenius" ]; then
    print_warning "检测到已存在的安装目录"
    BACKUP_DIR="ragenius.backup.$(date +%Y%m%d_%H%M%S)"
    mv ragenius "$BACKUP_DIR"
    print_success "已备份到: /opt/$BACKUP_DIR"
fi

# 克隆项目
print_step "正在从 GitHub 克隆代码..."
if git clone --depth 1 https://github.com/l1anch1/DeepSeek-RAG.git ragenius; then
    print_success "项目克隆完成"
else
    print_error "项目克隆失败，请检查网络连接"
    exit 1
fi

cd ragenius
CURRENT_DIR=$(pwd)
echo "  项目目录: $CURRENT_DIR"

# ============================================
# 9. 创建配置文件
# ============================================
print_step "[9/11] 创建配置文件..."

# 检查是否已存在 .env 文件
if [ -f ".env" ]; then
    print_warning ".env 文件已存在，备份为 .env.backup"
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
fi

# 创建 .env 文件
cat > .env << 'EOF'
# ============================================
# RAGenius 配置文件
# ============================================

# ============================================
# LLM 配置（重要：请修改为你的真实 API Key！）
# ============================================
LLM_USE_OPENAI=true
LLM_OPENAI_API_KEY=sk-YOUR-API-KEY-HERE
LLM_OPENAI_MODEL=gpt-4o
LLM_OPENAI_API_BASE=https://api.openai.com/v1

# 如果使用本地模型（需要先安装 Ollama）
# LLM_USE_OPENAI=false
# LLM_LOCAL_MODEL=deepseek-r1:14b

# ============================================
# Flask 环境
# ============================================
FLASK_ENV=production
FLASK_DEBUG=false

# ============================================
# 硬件配置
# ============================================
DEVICE=cpu

# 如果有 GPU（需要 NVIDIA GPU + CUDA）
# DEVICE=cuda

# ============================================
# 检索配置（可选，使用默认值）
# ============================================
CHUNK_SIZE=600
CHUNK_OVERLAP=150
SEARCH_K=8
RERANK_TOP_K=5
SCORE_THRESHOLD=0.3
MMR_DIVERSITY_SCORE=0.3

# ============================================
# 日志配置
# ============================================
LOG_LEVEL=INFO

# ============================================
# 安全配置
# ============================================
SECRET_KEY=$(openssl rand -hex 32)
EOF

print_success "配置文件创建完成"
print_warning "⚠️  重要：请稍后修改 /opt/ragenius/.env 中的 API Key！"

# ============================================
# 10. 启动服务
# ============================================
print_step "[10/11] 启动 Docker 服务..."

print_warning "首次启动需要下载镜像，可能需要 3-5 分钟，请耐心等待..."

# 拉取镜像
echo "  正在拉取 Docker 镜像..."
docker compose pull || print_warning "镜像拉取失败，将在启动时自动构建"

# 启动服务
echo "  正在启动服务..."
if docker compose up -d; then
    print_success "服务启动成功"
else
    print_error "服务启动失败"
    echo "  请查看日志: docker compose logs"
    exit 1
fi

# 等待服务启动
print_step "等待服务完全启动..."
sleep 15

# 检查服务状态
echo ""
echo "  服务状态："
docker compose ps

# 测试服务
echo ""
print_step "测试服务健康..."

# 测试后端
if curl -f http://localhost:8000/api/health 2>/dev/null | grep -q "healthy"; then
    print_success "后端服务正常运行"
else
    print_warning "后端服务可能还在启动中..."
fi

# 测试前端
if curl -f http://localhost:3000 2>/dev/null > /dev/null; then
    print_success "前端服务正常运行"
else
    print_warning "前端服务可能还在启动中..."
fi

# ============================================
# 11. 配置 Nginx 反向代理
# ============================================
print_step "[11/11] 配置 Nginx..."

# 获取公网 IP
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s icanhazip.com 2>/dev/null || echo "获取失败")

cat > /etc/nginx/sites-available/ragenius << 'EOF'
server {
    listen 80;
    server_name _;  # 临时配置，稍后替换为你的域名

    # 限制上传文件大小
    client_max_body_size 50M;
    client_body_timeout 300s;

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    # 后端 API
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_http_version 1.1;
        
        # WebSocket 支持
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        
        # 基本头部
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # SSE 流式响应支持（重要！）
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        
        # 允许大文件上传
        client_max_body_size 50M;
    }

    # 前端
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # 日志
    access_log /var/log/nginx/ragenius_access.log;
    error_log /var/log/nginx/ragenius_error.log;
}
EOF

# 启用配置
ln -sf /etc/nginx/sites-available/ragenius /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# 测试配置
if nginx -t 2>&1 | grep -q "syntax is ok"; then
    print_success "Nginx 配置正确"
    systemctl restart nginx
    systemctl enable nginx
    print_success "Nginx 已启动"
else
    print_error "Nginx 配置错误"
    nginx -t
    exit 1
fi

# ============================================
# 部署完成！
# ============================================
echo ""
print_header "✅ 部署完成！"
echo ""

cat << EOF
╔═══════════════════════════════════════════════════════════════╗
║                    🎉 恭喜！部署成功                           ║
╚═══════════════════════════════════════════════════════════════╝

${GREEN}RAGenius 已成功部署到你的阿里云 ECS${NC}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

${YELLOW}📝 重要：接下来必须完成的 3 个步骤${NC}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

${RED}1️⃣  配置 OpenAI API Key（必须！否则无法使用）${NC}

   ${BLUE}命令：${NC}
   nano /opt/ragenius/.env

   ${BLUE}找到这行：${NC}
   LLM_OPENAI_API_KEY=sk-YOUR-API-KEY-HERE

   ${BLUE}改为你的真实 API Key：${NC}
   LLM_OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx

   ${BLUE}保存：${NC}Ctrl+O 回车，${BLUE}退出：${NC}Ctrl+X

   ${BLUE}重启服务：${NC}
   cd /opt/ragenius && docker compose restart

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

${YELLOW}2️⃣  配置域名（推荐）${NC}

   ${BLUE}a) 在域名管理后台添加 A 记录：${NC}
      类型: A
      主机记录: @
      记录值: ${GREEN}${PUBLIC_IP}${NC}

   ${BLUE}b) 修改 Nginx 配置：${NC}
      nano /etc/nginx/sites-available/ragenius

      ${BLUE}找到：${NC}
      server_name _;

      ${BLUE}改为你的域名：${NC}
      server_name yourdomain.com www.yourdomain.com;

      ${BLUE}保存后重启：${NC}
      nginx -t && systemctl restart nginx

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

${YELLOW}3️⃣  配置 HTTPS 证书（推荐）${NC}

   ${BLUE}等域名解析生效后（5-10分钟），运行：${NC}
   certbot --nginx -d yourdomain.com -d www.yourdomain.com

   按提示输入邮箱，选择重定向 HTTP 到 HTTPS

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

${GREEN}🌐 临时访问地址（配置 API Key 后可用）：${NC}

   ${BLUE}http://${PUBLIC_IP}${NC}

   ${RED}注意：没有配置 API Key 会无法正常使用！${NC}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

${GREEN}📚 常用命令：${NC}

   ${BLUE}查看服务状态：${NC}
   cd /opt/ragenius && docker compose ps

   ${BLUE}查看实时日志：${NC}
   cd /opt/ragenius && docker compose logs -f

   ${BLUE}查看后端日志：${NC}
   cd /opt/ragenius && docker compose logs -f backend

   ${BLUE}重启服务：${NC}
   cd /opt/ragenius && docker compose restart

   ${BLUE}停止服务：${NC}
   cd /opt/ragenius && docker compose down

   ${BLUE}启动服务：${NC}
   cd /opt/ragenius && docker compose up -d

   ${BLUE}更新代码：${NC}
   cd /opt/ragenius && git pull && docker compose up -d --build

   ${BLUE}查看系统资源：${NC}
   htop

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

${GREEN}🔍 验证部署：${NC}

   ${BLUE}1. 检查服务状态${NC}
   cd /opt/ragenius && docker compose ps
   # 应该看到 3 个服务都是 running (healthy) 状态

   ${BLUE}2. 测试后端 API${NC}
   curl http://localhost:8000/api/health
   # 应该返回 {"status": "healthy", ...}

   ${BLUE}3. 在浏览器访问${NC}
   http://${PUBLIC_IP}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

${GREEN}📖 完整文档：${NC}

   • 部署指南: /opt/ragenius/DEPLOYMENT_GUIDE.md
   • 快速部署: /opt/ragenius/QUICK_DEPLOY.md
   • 项目文档: /opt/ragenius/README.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

${GREEN}🆘 遇到问题？${NC}

   ${BLUE}服务启动失败：${NC}
   docker compose logs backend

   ${BLUE}前端无法访问：${NC}
   docker compose logs frontend

   ${BLUE}Nginx 错误：${NC}
   tail -f /var/log/nginx/ragenius_error.log

   ${BLUE}提交 Issue：${NC}
   https://github.com/l1anch1/DeepSeek-RAG/issues

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

${GREEN}💡 下一步建议：${NC}

1. ${YELLOW}立即配置 API Key${NC}（否则无法使用）
2. 等待 5 分钟让服务完全启动
3. 访问 http://${PUBLIC_IP} 测试
4. 配置域名和 HTTPS（推荐）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

${GREEN}🎉 祝你使用愉快！${NC}

EOF

