# CI 快速参考

## 🎯 CI 检查清单

### ✅ 必须通过（会阻止合并）

| 检查 | 命令 | 说明 |
|------|------|------|
| Python 语法 | `python -m py_compile backend/app.py` | 确保代码可编译 |
| 前端构建 | `cd frontend && npm run build` | 确保应用可构建 |
| Docker 构建 | `docker-compose build` | 确保镜像可构建 |

### ⚠️ 可选检查（仅提供建议）

| 检查 | 命令 | 修复命令 |
|------|------|----------|
| Python 格式 | `black --check backend/` | `black backend/` |
| 导入排序 | `isort --check backend/` | `isort backend/` |
| Python Lint | `flake8 backend/` | 手动修复 |
| JS Lint | `cd frontend && npm run lint` | `npm run lint -- --fix` |

---

## 🚀 推送前快速检查

```bash
# 1. Python 语法（必须）
python -m py_compile backend/app.py

# 2. 前端构建（必须）
cd frontend && npm run build && cd ..

# 3. Docker 构建（必须）
docker-compose build

# 4. 代码格式（可选）
pip install black && black backend/
cd frontend && npm run lint -- --fix
```

---

## 📊 工作流状态

### ci.yml - 主 CI
- **触发**：Push 到 main/develop，PR
- **策略**：必须通过才能合并
- **检查**：语法、构建、Docker

### code-quality.yml - 代码质量
- **触发**：仅 PR
- **策略**：不阻止合并
- **检查**：格式、Lint

### codeql.yml - 安全扫描
- **触发**：Push、PR、每周一
- **策略**：信息性
- **检查**：安全漏洞

---

## 🔧 常用命令

### 查看 CI 状态
```bash
# 在 GitHub 网页
https://github.com/YOUR_USERNAME/REPO/actions
```

### 跳过 CI
```bash
git commit -m "docs: update README [skip ci]"
```

### 本地运行 CI（使用 act）
```bash
# 安装 act
brew install act  # macOS

# 运行 CI
act push
```

---

## 🐛 快速故障排查

### CI 失败？

1. **查看日志**：Actions → 点击失败的运行 → 展开步骤
2. **本地复现**：运行上面的快速检查命令
3. **查看详细指南**：[CI_TROUBLESHOOTING.md](./CI_TROUBLESHOOTING.md)

### 常见错误

| 错误 | 原因 | 解决 |
|------|------|------|
| `SyntaxError` | Python 语法错误 | 检查代码语法 |
| `npm ERR!` | 前端构建失败 | 检查 JSX/依赖 |
| `would reformat` | 格式问题 | `black backend/` |
| `ModuleNotFoundError` | 缺少依赖 | 更新 requirements.txt |

---

## 📞 获取帮助

- 📖 详细指南：[CI_TROUBLESHOOTING.md](./CI_TROUBLESHOOTING.md)
- 📖 工作流文档：[README.md](./README.md)
- 🐛 提交 Issue：[GitHub Issues](https://github.com/l1anch1/DeepSeek-RAG/issues)
- 📧 Email：asherlii@outlook.com

---

## 💡 专业提示

1. **提交前本地测试**：避免 CI 失败
2. **小步提交**：更容易定位问题
3. **阅读日志**：CI 日志包含详细错误信息
4. **使用 pre-commit hooks**：自动格式化代码
5. **关注 Dependabot**：及时更新依赖

---

**记住**：CI 是帮助你的工具，不是障碍！✨

