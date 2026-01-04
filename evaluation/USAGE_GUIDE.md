# RAG System Evaluation - 使用指南

## 🎯 快速开始

### Step 1: 启动后端服务

```bash
# 进入项目根目录
cd /path/to/RAGenius

# 启动 Docker 服务
docker compose up -d

# 等待服务启动（约 30 秒）
docker compose logs -f backend

# 看到 "Running on http://0.0.0.0:8000" 表示启动成功
# 按 Ctrl+C 退出日志查看
```

### Step 2: 测试后端连接

```bash
# 测试连接
python3 evaluation/test_connection.py

# 应该看到：
# ✅ Health check passed
# ✅ System info retrieved
# ✅ Documents retrieved
# ✅ Query successful
```

### Step 3: 运行评估

```bash
# 方式 A: 使用脚本（推荐）
./evaluation/run_evaluation.sh

# 方式 B: 直接运行 Python
python3 evaluation/scripts/evaluate_rag.py
```

## 📋 详细流程

### 1. 完整评估（首次运行）

```bash
# 这会：
# 1. 检查后端连接
# 2. 上传示例文档（evaluation/data/sample_docs/）
# 3. 重建知识库
# 4. 运行 20 个测试问题
# 5. 生成评估报告和可视化

./evaluation/run_evaluation.sh
```

**预计时间**：5-10 分钟（取决于 API 速度）

**输出文件**：
- `evaluation/results/EVALUATION_REPORT.md` - 详细报告
- `evaluation/results/evaluation_results.svg` - 可视化图表
- `evaluation/results/evaluation_report.json` - 机器可读结果

### 2. 快速评估（使用现有知识库）

```bash
# 如果已经上传过文档，可以跳过上传步骤
./evaluation/run_evaluation.sh --skip-upload
```

**预计时间**：3-5 分钟

### 3. 评估远程部署

```bash
# 评估部署在服务器上的系统
./evaluation/run_evaluation.sh --backend-url http://your-server.com:8000
```

### 4. 自定义评估

```python
# 创建自己的评估脚本
from pathlib import Path
from evaluation.scripts.evaluate_rag import RAGEvaluator

# 初始化评估器
evaluator = RAGEvaluator(
    test_data_path="evaluation/data/test_dataset.json",
    output_dir="evaluation/results",
    backend_url="http://localhost:8000"
)

# 运行评估
evaluator.run_full_evaluation(skip_upload=False)
```

## 🔧 高级用法

### 自定义测试数据集

编辑 `evaluation/data/test_dataset.json`:

```json
{
  "test_cases": [
    {
      "question": "你的问题？",
      "ground_truth": "标准答案",
      "context_keywords": ["关键词1", "关键词2"]
    }
  ]
}
```

### 使用自己的知识库

```python
# 1. 上传你的文档
evaluator.upload_knowledge_base(Path("/path/to/your/docs"))

# 2. 重建知识库
evaluator.rebuild_knowledge_base()

# 3. 运行评估
dataset = evaluator.prepare_evaluation_dataset()
results = evaluator.evaluate_with_ragas(dataset)
```

### 调整评估指标

编辑 `evaluation/scripts/evaluate_rag.py`:

```python
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
    answer_similarity,      # 添加新指标
    answer_correctness,     # 添加新指标
)

# 在 evaluate_with_ragas 函数中
result = evaluate(
    dataset,
    metrics=[
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
        answer_similarity,   # 使用新指标
        answer_correctness,
    ],
)
```

## 🐛 故障排查

### 问题 1: 后端连接失败

```
❌ Backend not available at http://localhost:8000
```

**解决方案**:

```bash
# 检查后端是否运行
docker compose ps

# 如果没有运行，启动它
docker compose up -d

# 检查日志
docker compose logs backend

# 测试连接
curl http://localhost:8000/api/health
```

### 问题 2: 依赖安装失败

```
❌ Failed to install dependencies
```

**解决方案**:

```bash
# 升级 pip
python3 -m pip install --upgrade pip

# 单独安装依赖
pip3 install requests tqdm
pip3 install ragas datasets
pip3 install matplotlib seaborn pandas
```

### 问题 3: 查询超时

```
⚠️  请求超时
```

**解决方案**:

```python
# 在 evaluate_rag.py 中增加超时时间
response = requests.post(
    f"{self.backend_url}/api/query",
    json={"query": question},
    timeout=60  # 增加到 60 秒
)
```

### 问题 4: Ragas 评估失败

```
❌ 评估失败: OpenAI API key not found
```

**解决方案**:

```bash
# 设置 OpenAI API Key（Ragas 需要）
export OPENAI_API_KEY=your_key_here

# 或者在 .env 文件中设置
echo "OPENAI_API_KEY=your_key_here" >> .env
```

如果没有 OpenAI API，评估器会自动使用简化指标。

### 问题 5: 文档上传失败

```
❌ 上传失败: File already exists
```

**解决方案**:

```bash
# 清空现有文档
curl -X POST http://localhost:8000/api/documents/clear

# 或者使用 --skip-upload 跳过上传
./evaluation/run_evaluation.sh --skip-upload
```

## 📊 结果解读

### 指标含义

| 指标 | 说明 | 良好阈值 |
|------|------|---------|
| **Faithfulness** | 答案是否基于检索的上下文 | ≥ 85% |
| **Answer Relevancy** | 答案是否回答了问题 | ≥ 80% |
| **Context Precision** | 检索文档的相关性 | ≥ 75% |
| **Context Recall** | 是否检索到所有必要信息 | ≥ 80% |

### 性能等级

- **🟢 Excellent** (≥85%): 生产就绪
- **🟡 Good** (75-84%): 可用，有优化空间
- **🔴 Needs Improvement** (<75%): 需要优化

### 优化建议

**如果 Faithfulness 低**:
- 优化 prompt，强调使用上下文
- 降低 temperature (0.0-0.2)
- 检查文档质量

**如果 Answer Relevancy 低**:
- 改进 prompt 引导
- 使用 few-shot examples
- 优化答案格式

**如果 Context Precision 低**:
- 调整 chunk size
- 启用/优化 reranking
- 增加 score threshold

**如果 Context Recall 低**:
- 增加检索文档数量
- 优化 query expansion
- 检查嵌入模型质量

## 🚀 持续评估

### 设置定期评估

```bash
# 创建 cron 任务
crontab -e

# 每天凌晨 2 点运行评估
0 2 * * * cd /path/to/RAGenius && ./evaluation/run_evaluation.sh --skip-upload
```

### CI/CD 集成

```yaml
# .github/workflows/evaluation.yml
name: RAG Evaluation

on:
  schedule:
    - cron: '0 0 * * 0'  # 每周运行

jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Start backend
        run: docker compose up -d
      - name: Run evaluation
        run: |
          pip install -r evaluation/requirements.txt
          ./evaluation/run_evaluation.sh --skip-upload
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: evaluation-results
          path: evaluation/results/
```

## 💡 最佳实践

1. **首次评估**: 使用完整流程，上传示例文档
2. **日常评估**: 使用 `--skip-upload` 快速评估
3. **生产评估**: 评估前备份知识库
4. **对比评估**: 保存每次结果，追踪趋势
5. **A/B 测试**: 修改配置后重新评估，对比结果

## 📚 相关资源

- [Ragas 文档](https://docs.ragas.io/)
- [评估完整报告](./results/EVALUATION_REPORT.md)
- [测试数据集](./data/test_dataset.json)
- [主 README](../README.md)

---

**有问题？** 查看 [FAQ](./README.md#-常见问题) 或提 Issue

