# 自动部署到 VPS 配置指南

## 🎯 目标

实现：代码 push → 自动测试 → 自动部署到服务器

```
你 push 代码到 GitHub
    ↓
GitHub Actions 自动运行 CI
    ↓
测试全部通过
    ↓
自动部署到你的 VPS
    ↓
访问网站看到更新！
```

---

## 📋 前提条件

- ✅ 已按照 QUICK_DEPLOY.md 部署到 VPS
- ✅ 服务器正常运行
- ✅ 有服务器的 SSH 访问权限

---

## 🔧 配置步骤（5 分钟）

### 步骤 1: 生成 SSH 密钥（如果还没有）

在你的**本地电脑**上运行：

```bash
# 生成专用于部署的 SSH 密钥（不要设置密码）
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_deploy

# 这会生成两个文件：
# ~/.ssh/github_deploy      (私钥)
# ~/.ssh/github_deploy.pub  (公钥)
```

### 步骤 2: 将公钥添加到服务器

```bash
# 复制公钥内容
cat ~/.ssh/github_deploy.pub

# SSH 登录到服务器
ssh root@your-server-ip

# 将公钥添加到 authorized_keys
echo "你刚才复制的公钥内容" >> ~/.ssh/authorized_keys

# 设置权限
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh

# 测试 SSH 连接（在本地）
ssh -i ~/.ssh/github_deploy root@your-server-ip
# 应该能直接登录，不需要密码
```

### 步骤 3: 配置 GitHub Secrets

1. **获取私钥内容**（在本地）：
   ```bash
   cat ~/.ssh/github_deploy
   ```
   复制整个输出（包括 `-----BEGIN` 和 `-----END`）

2. **在 GitHub 添加 Secrets**：
   - 进入你的 GitHub 仓库
   - Settings → Secrets and variables → Actions
   - 点击 "New repository secret"

3. **添加以下 Secrets**：

   | Name | Value | 说明 |
   |------|-------|------|
   | `VPS_HOST` | `123.456.789.0` | 你的服务器 IP |
   | `VPS_USERNAME` | `root` | SSH 用户名（通常是 root） |
   | `VPS_SSH_KEY` | `-----BEGIN...` | 私钥全部内容 |
   | `VPS_PORT` | `22` | SSH 端口（通常是 22） |

### 步骤 4: 启用自动部署工作流

工作流文件已创建：`.github/workflows/deploy-to-vps.yml`

**工作原理**：
1. 你 push 代码到 main 分支
2. CI 工作流自动运行测试
3. **如果测试通过**，自动触发部署工作流
4. 部署工作流 SSH 到服务器，拉取代码，重启服务

### 步骤 5: 测试自动部署

```bash
# 在本地做个小改动
echo "# Auto-deploy test" >> README.md

# 提交并推送
git add README.md
git commit -m "test: trigger auto-deploy"
git push origin main
```

**查看部署过程**：
1. 进入 GitHub 仓库 → Actions 标签页
2. 看到两个工作流：
   - CI（测试）
   - Deploy to VPS（部署）
3. 点击查看实时日志

---

## 🎮 使用方式

### 日常开发

```bash
# 1. 开发新功能
git checkout -b feature/new-feature
# ... 编码 ...

# 2. 提交代码
git add .
git commit -m "feat: add new feature"
git push origin feature/new-feature

# 3. 创建 Pull Request
# 在 GitHub 网页上创建 PR

# 4. CI 自动运行测试
# 等待测试通过

# 5. 合并到 main
# 点击 "Merge pull request"

# 6. 自动部署！
# GitHub Actions 自动部署到服务器
# 几分钟后，访问网站看到新功能
```

### 手动触发部署

如果需要手动部署（不推荐，但有时有用）：

**方法 1：通过 GitHub UI**
1. Actions → Deploy to VPS
2. Run workflow → 选择分支
3. Run workflow

**方法 2：SSH 到服务器手动更新**
```bash
ssh root@your-server-ip
cd /opt/ragenius
git pull
docker compose restart
```

---

## 🔍 监控部署

### 查看部署日志

**GitHub Actions 日志**：
- GitHub → Actions → Deploy to VPS
- 点击最近的运行
- 查看每个步骤的输出

**服务器日志**：
```bash
# SSH 到服务器
ssh root@your-server-ip

# 查看应用日志
cd /opt/ragenius
docker compose logs -f

# 查看 Nginx 日志
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### 部署失败怎么办？

**1. 查看 GitHub Actions 日志**
- 找到失败的步骤
- 查看错误消息

**2. 常见问题**：

| 问题 | 原因 | 解决方法 |
|------|------|----------|
| SSH 连接失败 | SSH Key 配置错误 | 检查 GitHub Secrets |
| git pull 失败 | 服务器代码有冲突 | SSH 到服务器手动解决 |
| docker compose 失败 | 服务启动错误 | 查看服务器日志 |

**3. 回滚到上一个版本**：
```bash
ssh root@your-server-ip
cd /opt/ragenius
git log --oneline  # 查看提交历史
git reset --hard <previous-commit-hash>
docker compose restart
```

---

## 🎯 高级配置

### 1. 添加部署通知

**Slack 通知**：

在 `deploy-to-vps.yml` 末尾添加：
```yaml
- name: Slack Notification
  if: always()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    text: |
      Deployment to production ${{ job.status }}
      Commit: ${{ github.sha }}
      Author: ${{ github.actor }}
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### 2. 多环境部署

**配置 staging 和 production**：

```yaml
# .github/workflows/deploy-staging.yml
name: Deploy to Staging
on:
  push:
    branches: [develop]

# .github/workflows/deploy-production.yml  
name: Deploy to Production
on:
  push:
    branches: [main]
```

添加不同的 Secrets：
- `STAGING_VPS_HOST`
- `PRODUCTION_VPS_HOST`

### 3. 健康检查和自动回滚

在部署后添加健康检查：
```yaml
- name: Health Check
  run: |
    MAX_RETRIES=5
    RETRY_COUNT=0
    
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
      if curl -f https://your-domain.com/api/health; then
        echo "✅ Health check passed"
        exit 0
      fi
      RETRY_COUNT=$((RETRY_COUNT + 1))
      sleep 10
    done
    
    echo "❌ Health check failed, rolling back..."
    # 回滚逻辑
    exit 1
```

---

## 📊 对比

### 手动部署 vs 自动部署

| 特性 | 手动部署 | 自动部署 |
|------|---------|---------|
| **速度** | 慢（需要手动操作） | 快（自动化） |
| **可靠性** | 容易出错 | 一致性高 |
| **测试** | 可能忘记 | 必须通过测试 |
| **记录** | 无 | 完整日志 |
| **回滚** | 手动 | 可以自动 |
| **通知** | 无 | 可配置 |
| **适合场景** | 个人项目 | 团队协作 |

---

## 💡 最佳实践

### 1. 使用分支策略

```
main (生产环境) ← 自动部署
  ↑
develop (开发环境) ← 自动部署到测试服务器
  ↑
feature/* (功能分支) ← 仅运行 CI
```

### 2. 保护 main 分支

GitHub Settings → Branches → Add rule：
- Branch name pattern: `main`
- ✅ Require status checks to pass before merging
- ✅ Require pull request reviews before merging

### 3. 定期备份

在部署前自动备份：
```yaml
- name: Backup before deploy
  run: |
    ssh ${{ secrets.VPS_USERNAME }}@${{ secrets.VPS_HOST }} \
      "cd /opt/ragenius && tar czf backup_$(date +%Y%m%d_%H%M%S).tar.gz data/"
```

### 4. 监控部署频率

避免频繁部署导致服务不稳定：
- 使用 PR 合并，不要直接 push 到 main
- 批量功能一起部署
- 在低峰时段部署

---

## 🆘 故障排查

### SSH 连接失败

```bash
# 测试 SSH Key
ssh -i ~/.ssh/github_deploy root@your-server-ip

# 检查服务器 authorized_keys
ssh root@your-server-ip
cat ~/.ssh/authorized_keys

# 检查 SSH 配置
cat /etc/ssh/sshd_config | grep PubkeyAuthentication
# 应该是: PubkeyAuthentication yes
```

### Git pull 失败

```bash
# 服务器上检查 git 状态
cd /opt/ragenius
git status

# 如果有未提交的改动
git stash
git pull
```

### Docker 服务启动失败

```bash
# 查看详细日志
docker compose logs backend
docker compose logs frontend

# 重新构建
docker compose down
docker compose up -d --build
```

---

## ✅ 配置检查清单

部署自动化前，确保：

- [ ] VPS 已部署并运行正常
- [ ] SSH Key 生成并添加到服务器
- [ ] GitHub Secrets 配置正确
- [ ] 可以从本地用 SSH Key 登录服务器
- [ ] `.github/workflows/deploy-to-vps.yml` 已创建
- [ ] main 分支受保护（可选但推荐）
- [ ] 已测试一次自动部署

---

## 🎉 完成！

配置完成后：

1. ✅ **每次 push 到 main** → 自动测试 → 自动部署
2. ✅ **测试失败** → 不会部署（保护生产环境）
3. ✅ **部署记录** → 在 Actions 页面可查看
4. ✅ **可以回滚** → 简单快速

**享受自动化部署的便利吧！** 🚀

---

**需要帮助？**
- 查看 [CI_TROUBLESHOOTING.md](./CI_TROUBLESHOOTING.md)
- 提交 Issue: https://github.com/l1anch1/DeepSeek-RAG/issues

