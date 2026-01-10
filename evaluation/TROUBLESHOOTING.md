# 🔧 RAG 评估故障排查指南

## ❌ 错误 1: Python 版本兼容性问题

### 症状
```
TypeError: Unable to evaluate type annotation 'str | Path'
```

### 原因
- 你使用的是 Python 3.9
- `ragas` 依赖的 `instructor` 库使用了 Python 3.10+ 的新语法

### 解决方案（2 选 1）

#### 🚀 方案 1：安装兼容包（最快）
```bash
pip install eval_type_backport
./evaluation/run_evaluation.sh
```

#### ⭐ 方案 2：升级 Python（推荐）
```bash
# 创建 Python 3.11 环境
conda create -n ragenius_py311 python=3.11 -y
conda activate ragenius_py311

# 重新安装依赖
pip install -r evaluation/requirements.txt
pip install -r backend/requirements.txt

# 运行评估
./evaluation/run_evaluation.sh
```

---

## ❌ 错误 2: 模块未找到

### 症状
```
ModuleNotFoundError: No module named 'xxx'
```

### 解决方案
```bash
# 确保在正确的环境中
conda activate ragenius  # 或 ragenius_py311

# 安装依赖
pip install -r evaluation/requirements.txt
```

---

## ❌ 错误 3: 连接失败

### 症状
```
ConnectionError: Cannot connect to backend
```

### 解决方案
```bash
# 检查服务状态
docker compose ps

# 如果没运行，启动服务
docker compose up -d

# 等待 10 秒让服务启动
sleep 10

# 测试连接
python3 evaluation/test_connection.py
```

---

## ❌ 错误 4: Ragas 需要 OpenAI API Key

### 症状
```
The api_key client option must be set either by passing api_key to the client 
or by setting the OPENAI_API_KEY environment variable
```

### 原因
- **Ragas 框架需要调用 OpenAI API 来评估答案质量**
- 这个 API key 是给 Ragas 用的（作为"评判者"）
- 不是给你的 RAGenius 系统用的

### 解决方案

#### 方法 1: 在 .env 文件中添加
```bash
# 编辑 .env 文件
echo "OPENAI_API_KEY=sk-your-openai-key-here" >> .env

# 如果使用代理
echo "OPENAI_API_KEY=sk-your-proxy-key" >> .env
echo "OPENAI_API_BASE=https://your-proxy-url/v1" >> .env
```

#### 方法 2: 临时设置环境变量
```bash
# 设置并运行
export OPENAI_API_KEY=sk-your-key-here
./evaluation/run_evaluation.sh
```

#### 方法 3: 使用你现有的 RAGenius API Key
如果你的 `.env` 已经有 `LLM_OPENAI_API_KEY`：
```bash
# 复制一份给 Ragas 用
export OPENAI_API_KEY=$(grep LLM_OPENAI_API_KEY .env | cut -d '=' -f2)
./evaluation/run_evaluation.sh
```

---

## ❌ 错误 5: RAGenius 系统 API Key 错误

### 症状
```
Incorrect API key provided: sk-YOUR-********HERE
```

### 解决方案
```bash
# 检查 .env 文件
cat .env | grep LLM_OPENAI_API_KEY

# 如果使用 Docker，需要重启容器
docker compose down
docker compose up -d
```

---

## 📋 快速诊断命令

### 检查 Python 版本
```bash
python3 --version
# 应该是 3.10 或更高
```

### 检查依赖安装
```bash
pip list | grep -E "ragas|datasets|requests|matplotlib"
```

### 检查服务状态
```bash
docker compose ps
curl http://localhost:8000/api/health
```

### 完整诊断
```bash
# 一键诊断所有问题
python3 evaluation/test_connection.py
```

---

## 💡 常见问题 FAQ

### Q: 为什么推荐 Python 3.10+？
- ✅ 更好的类型系统
- ✅ 更快的性能
- ✅ 大部分现代库的最低要求

### Q: 不想升级 Python 怎么办？
```bash
# 安装兼容包即可
pip install eval_type_backport
```

### Q: 评估太慢怎么办？
```bash
# 只测试前 20 题
python3 evaluation/scripts/evaluate_rag.py --num-questions 20

# 跳过文档上传
python3 evaluation/scripts/evaluate_rag.py --skip-upload
```

### Q: 如何验证问题已解决？
```bash
# 先测试连接
python3 evaluation/test_connection.py

# 测试导入
python3 -c "from ragas import evaluate; print('✅ ragas OK')"

# 快速测试 5 题
python3 evaluation/scripts/evaluate_rag.py --num-questions 5
```

---

## 🆘 还是不行？

### 完全重置环境
```bash
# 1. 删除旧环境
conda deactivate
conda env remove -n ragenius

# 2. 创建新环境（Python 3.11）
conda create -n ragenius python=3.11 -y
conda activate ragenius

# 3. 安装依赖
cd /Users/lianchi/Documents/CS/RAGenius
pip install -r evaluation/requirements.txt
pip install -r backend/requirements.txt

# 4. 测试
python3 evaluation/test_connection.py
./evaluation/run_evaluation.sh
```

---

## 📞 联系支持

如果以上方法都不行，请提供以下信息：

```bash
# 收集诊断信息
echo "=== Python 版本 ===" > diagnostic.txt
python3 --version >> diagnostic.txt
echo -e "\n=== 已安装包 ===" >> diagnostic.txt
pip list >> diagnostic.txt
echo -e "\n=== Docker 状态 ===" >> diagnostic.txt
docker compose ps >> diagnostic.txt
echo -e "\n=== 服务健康检查 ===" >> diagnostic.txt
curl http://localhost:8000/api/health >> diagnostic.txt 2>&1

cat diagnostic.txt
```

然后把 `diagnostic.txt` 的内容发给我。
