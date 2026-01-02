# 🚀 Railway 一键部署指南

> **最简单的部署方式**：3 分钟上线，无需配置服务器！

---

## ✨ 为什么选择 Railway？

- ⚡ **3 分钟部署**：连接 GitHub，自动部署
- 🔄 **自动 CI/CD**：推送代码自动更新
- 🆓 **免费额度**：每月 $5 免费额度
- 🌐 **自动 HTTPS**：免费域名 + SSL 证书
- 📊 **自动监控**：内置日志、性能指标
- 🛠️ **零运维**：无需管理服务器

---

## 📋 部署步骤

### 步骤 1：注册 Railway

1. 访问 [Railway.app](https://railway.app/)
2. 点击 "Login" → "Login with GitHub"
3. 授权 Railway 访问你的 GitHub

💰 **定价**：
- 免费：$5/月额度（适合小项目）
- Developer：$5/月订阅（含 $5 额度 + 优先支持）

---

### 步骤 2：准备项目

确保你的项目已推送到 GitHub：

```bash
cd /Users/lianchi/Documents/CS/RAGenius
git add .
git commit -m "chore: add Railway deployment config"
git push
```

---

### 步骤 3：创建 Railway 项目

#### 方法 1：通过 Railway Dashboard（推荐）

1. 登录 [Railway Dashboard](https://railway.app/dashboard)
2. 点击 **"New Project"**
3. 选择 **"Deploy from GitHub repo"**
4. 选择你的 `RAGenius` 仓库
5. Railway 会自动检测 `docker-compose.yml`

#### 方法 2：使用 Railway CLI

```bash
# 安装 Railway CLI
npm install -g @railway/cli

# 登录
railway login

# 初始化项目
cd /Users/lianchi/Documents/CS/RAGenius
railway init

# 部署
railway up
```

---

### 步骤 4：配置环境变量

在 Railway Dashboard 中：

1. 点击你的项目
2. 选择 **Backend 服务**
3. 进入 **"Variables"** 标签
4. 添加以下环境变量：

```bash
# LLM 配置（必填）
LLM_USE_OPENAI=true
LLM_OPENAI_API_KEY=sk-proj-your-key-here
LLM_OPENAI_MODEL=gpt-4o

# Flask 环境
FLASK_ENV=production

# 硬件配置
DEVICE=cpu

# 其他配置（可选）
CHUNK_SIZE=600
CHUNK_OVERLAP=150
SEARCH_K=8
```

5. 点击 **"Add Variable"** 保存

---

### 步骤 5：配置服务端口

Railway 需要知道每个服务监听的端口：

#### Backend 服务：
- 在 "Settings" → "Networking"
- **Port**: `8000`
- 勾选 **"Generate Domain"** 生成公开访问域名

#### Frontend 服务：
- 在 "Settings" → "Networking"
- **Port**: `3000`
- 勾选 **"Generate Domain"** 生成公开访问域名

#### ChromaDB 服务：
- 在 "Settings" → "Networking"
- **Port**: `8001`
- **不需要**勾选 "Generate Domain"（内部服务）

---

### 步骤 6：连接服务（重要！）

Railway 需要知道服务之间如何通信：

1. 在 Frontend 服务中添加环境变量：
```bash
REACT_APP_API_URL=https://your-backend.up.railway.app
```

2. 在 Backend 服务中添加环境变量：
```bash
CHROMA_HOST=chroma-db.railway.internal
CHROMA_PORT=8001
```

---

### 步骤 7：部署

Railway 会自动开始部署：

1. 构建 Docker 镜像
2. 启动容器
3. 健康检查
4. 生成访问域名

⏱️ **预计时间**：5-8 分钟

---

### 步骤 8：访问应用

部署完成后，Railway 会为你生成访问域名：

```
Frontend: https://ragenius-frontend-xxxx.up.railway.app
Backend:  https://ragenius-backend-xxxx.up.railway.app
```

点击 Frontend 域名即可访问！🎉

---

## 🔍 验证部署

### 1. 检查服务状态

在 Railway Dashboard 中：
- 所有服务应该显示绿色 ✅
- 查看日志确认没有错误

### 2. 测试 API

```bash
# 测试后端健康检查
curl https://your-backend.up.railway.app/api/health

# 应该返回：
{"status": "healthy", ...}
```

### 3. 测试前端

在浏览器打开 Frontend 域名，应该能看到 RAGenius 界面。

---

## 🎨 绑定自定义域名（可选）

### 步骤 1：在 Railway 中添加域名

1. 选择 Frontend 服务
2. 进入 "Settings" → "Domains"
3. 点击 "Add Custom Domain"
4. 输入你的域名：`yourdomain.com`

### 步骤 2：配置 DNS

在你的域名管理后台添加 CNAME 记录：

```
类型: CNAME
主机记录: @
记录值: your-project.up.railway.app
TTL: 600
```

### 步骤 3：等待生效

- DNS 解析需要 5-30 分钟
- Railway 会自动配置 SSL 证书

---

## 📊 监控和日志

### 查看日志

1. 在 Railway Dashboard 选择服务
2. 点击 "Logs" 标签
3. 实时查看日志输出

### 查看性能指标

1. 在 Railway Dashboard 选择服务
2. 点击 "Metrics" 标签
3. 查看 CPU、内存、网络使用情况

---

## 🔄 自动 CI/CD

Railway 已经为你配置好自动部署：

```bash
# 每次推送代码到 GitHub
git add .
git commit -m "feat: new feature"
git push

# Railway 会自动：
# 1. 检测代码变更
# 2. 重新构建镜像
# 3. 部署新版本
# 4. 零停机更新
```

---

## 💰 费用估算

### 免费套餐
- **$5/月** 免费额度
- 适合小项目、演示

### 实际使用（估算）
- Backend: ~$3/月
- Frontend: ~$2/月
- ChromaDB: ~$2/月
- **总计**: ~$7/月（超出免费额度 $2）

### 优化建议
- 使用 Railway 的 **睡眠模式**（免费版自动启用）
- 低流量时自动休眠，节省费用
- 第一次访问需要 10-30 秒唤醒

---

## 🛠️ 常见问题

### Q1: 服务启动失败？

**检查日志**：
```bash
# 在 Railway Dashboard 查看 Logs
# 常见问题：
# - 环境变量未配置
# - API Key 无效
# - 镜像构建失败
```

**解决方法**：
1. 确认所有环境变量已配置
2. 检查 API Key 是否有效
3. 查看构建日志找到具体错误

### Q2: 前端无法连接后端？

**检查环境变量**：
```bash
# Frontend 服务需要配置：
REACT_APP_API_URL=https://your-backend.up.railway.app
```

**重新部署**：
```bash
railway up --service frontend
```

### Q3: ChromaDB 连接失败？

**检查内部网络**：
```bash
# Backend 服务需要配置：
CHROMA_HOST=chroma-db.railway.internal
CHROMA_PORT=8001
```

### Q4: 部署太慢？

**优化构建**：
- Railway 首次部署需要下载所有依赖
- 后续部署会使用缓存，速度更快
- 通常 2-3 分钟完成

### Q5: 超出免费额度？

**查看用量**：
1. 进入 "Usage" 标签
2. 查看当月消费

**降低成本**：
- 启用睡眠模式
- 优化镜像大小
- 减少服务数量

---

## 🔧 高级配置

### 配置健康检查

在 `railway.json` 中：
```json
{
  "deploy": {
    "healthcheckPath": "/api/health",
    "healthcheckTimeout": 300
  }
}
```

### 配置自动重启

```json
{
  "deploy": {
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### 配置环境

```json
{
  "environments": {
    "production": {
      "variables": {
        "FLASK_ENV": "production"
      }
    }
  }
}
```

---

## 📚 相关文档

- [Railway 官方文档](https://docs.railway.app/)
- [Docker Compose on Railway](https://docs.railway.app/deploy/dockerfiles)
- [环境变量配置](https://docs.railway.app/develop/variables)

---

## ✅ 部署检查清单

- [ ] Railway 账号已注册
- [ ] 项目已推送到 GitHub
- [ ] 已创建 Railway 项目
- [ ] 环境变量已配置（尤其是 API Key）
- [ ] 服务端口已配置
- [ ] 服务间网络已配置
- [ ] 部署成功，服务运行正常
- [ ] 前端可访问
- [ ] API 调用正常
- [ ] （可选）自定义域名已绑定
- [ ] （可选）HTTPS 已配置

---

## 🎉 完成！

恭喜！你的 RAGenius 已经部署到 Railway 了！

**访问地址**：
- Frontend: https://your-frontend.up.railway.app
- Backend API: https://your-backend.up.railway.app/api

**下一步**：
1. 测试所有功能
2. 绑定自定义域名
3. 分享给朋友！

---

## 🆘 需要帮助？

- 📖 查看 `DEPLOYMENT_GUIDE.md` 获取其他部署方案
- 💬 提交 Issue: https://github.com/l1anch1/DeepSeek-RAG/issues
- ✉️  Email: asherlii@outlook.com

---

**💡 提示**：Railway 非常适合快速上线和演示项目，如果需要更多控制和更低成本，可以考虑 Vultr 或 DigitalOcean VPS。

