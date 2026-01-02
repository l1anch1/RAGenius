# CI 故障排查指南

## 🔍 CI 失败了怎么办？

### 查看失败原因

1. 进入 GitHub 仓库的 **Actions** 标签页
2. 点击失败的工作流运行
3. 展开失败的步骤查看详细日志

---

## 常见失败原因及解决方案

### 1. Python 语法错误

**错误信息**：
```
SyntaxError: invalid syntax
```

**原因**：Python 代码有语法错误

**解决方法**：
```bash
# 本地检查语法
python -m py_compile backend/app.py
find backend -name "*.py" -exec python -m py_compile {} +
```

---

### 2. 前端构建失败

**错误信息**：
```
npm ERR! code ELIFECYCLE
npm ERR! errno 1
```

**原因**：前端代码有错误或依赖问题

**解决方法**：
```bash
cd frontend
npm install
npm run build

# 如果有 ESLint 错误
npm run lint
# 自动修复部分问题
npm run lint -- --fix
```

---

### 3. Docker 构建失败

**错误信息**：
```
ERROR: failed to solve: process "/bin/sh -c ..." did not complete successfully
```

**原因**：Dockerfile 有问题或依赖安装失败

**解决方法**：
```bash
# 本地测试 Docker 构建
docker build -t test-backend ./backend
docker build -t test-frontend ./frontend

# 或使用 docker-compose
docker-compose build
```

---

### 4. 代码格式问题（可选检查）

**错误信息**：
```
would reformat backend/app.py
```

**原因**：代码格式不符合 Black 标准

**解决方法**：
```bash
# 安装格式化工具
pip install black isort

# 自动格式化 Python 代码
black backend/
isort backend/

# 前端代码格式化
cd frontend
npm run lint -- --fix
```

**注意**：这是可选检查，不会阻止 PR 合并

---

### 5. 导入错误

**错误信息**：
```
ModuleNotFoundError: No module named 'xxx'
```

**原因**：缺少依赖或导入路径错误

**解决方法**：
```bash
# 确保 requirements.txt 包含所有依赖
pip install -r backend/requirements.txt

# 检查导入
cd backend
python -c "import app"
```

---

## 本地预检查清单

在推送代码前，运行这些检查：

### Python 检查
```bash
# 1. 语法检查（必须通过）
python -m py_compile backend/app.py

# 2. 安装依赖
pip install -r backend/requirements.txt

# 3. 测试导入
cd backend && python -c "import app" && cd ..

# 4. 代码格式（可选）
pip install black flake8
black --check backend/
flake8 backend/ --exclude=models_cache,__pycache__
```

### 前端检查
```bash
cd frontend

# 1. 安装依赖
npm install

# 2. 构建测试（必须通过）
npm run build

# 3. Lint 检查（可选）
npm run lint

cd ..
```

### Docker 检查
```bash
# 测试 Docker 构建
docker-compose build

# 验证配置
docker-compose config
```

---

## CI 工作流说明

### 主 CI (ci.yml) - 必须通过

这些检查必须通过才能合并：

- ✅ **Python 语法检查**：确保代码可以编译
- ✅ **前端构建**：确保应用可以构建
- ✅ **Docker 构建**：确保镜像可以构建

### 代码质量 (code-quality.yml) - 可选

这些检查提供建议，但不阻止合并：

- ⚠️ **Black 格式检查**：代码格式建议
- ⚠️ **Flake8 Linting**：代码质量建议
- ⚠️ **ESLint**：JavaScript 代码质量

### 安全扫描 - 信息性

- 🔒 **CodeQL**：安全漏洞扫描
- 🔒 **Trivy**：依赖漏洞扫描
- 🔒 **Dependabot**：依赖更新建议

---

## 跳过 CI

如果你只是更新文档，可以在提交消息中添加 `[skip ci]`：

```bash
git commit -m "docs: update README [skip ci]"
```

---

## 禁用某个检查

如果某个检查总是失败且你暂时无法修复，可以：

### 方法 1：在工作流中添加 continue-on-error

编辑 `.github/workflows/ci.yml`：

```yaml
- name: 某个步骤
  run: some command
  continue-on-error: true  # 添加这一行
```

### 方法 2：临时禁用整个工作流

在工作流文件开头添加条件：

```yaml
name: CI

on:
  push:
    branches: [ main, develop ]
    paths-ignore:
      - '**.md'  # 忽略 Markdown 文件变更
```

---

## 获取帮助

1. **查看工作流日志**：Actions 标签页 → 点击失败的运行
2. **本地复现问题**：使用 [act](https://github.com/nektos/act) 本地运行工作流
3. **提出 Issue**：如果是 CI 配置问题，请开 Issue

---

## 常见问题 FAQ

### Q: CI 一直失败，但本地运行正常？

A: 可能的原因：
- Python/Node 版本不同（CI 使用 3.9-3.11 和 Node 18-20）
- 依赖版本不同（使用 `pip freeze` 和 `npm ci` 锁定版本）
- 环境变量缺失（CI 没有 `.env` 文件）

### Q: 可以完全禁用 CI 吗？

A: 可以，但不推荐。如果必须：
1. 删除 `.github/workflows/` 目录
2. 或在 Settings → Actions 中禁用

### Q: 为什么有些检查是 "Skipped"？

A: 某些检查依赖其他检查完成（`needs` 关键字）。如果前置检查失败，后续检查会被跳过。

### Q: 如何加快 CI 速度？

A: 
- 使用缓存（已配置）
- 减少矩阵测试版本
- 使用 `fail-fast: false` 并行运行

---

## 联系支持

如果问题仍未解决：

- 📧 Email: asherlii@outlook.com
- 🐛 GitHub Issues: https://github.com/l1anch1/DeepSeek-RAG/issues

