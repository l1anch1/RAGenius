# RAG System Evaluation - 使用指南

## ⚠️ 重要前提

**Ragas 需要 OpenAI API Key** 来评估答案质量。请确保：

```bash
# 方式 1: 在 .env 文件中设置
OPENAI_API_KEY=sk-your-openai-key-here

# 方式 2: 临时设置环境变量
export OPENAI_API_KEY=sk-your-key-here

# 方式 3: 使用现有的 RAGenius key
export OPENAI_API_KEY=$(grep LLM_OPENAI_API_KEY .env | cut -d '=' -f2)
```

💡 **为什么需要？** Ragas 使用 LLM 作为"评判者"来评估答案的忠实度和相关性。

---

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

### Step 2: 配置 API Key（如果还没有）

```bash
# 添加到 .env 文件
echo "OPENAI_API_KEY=sk-your-key-here" >> .env
```

### Step 3: 测试后端连接

```bash
# 测试连接
python3 evaluation/test_connection.py

# 应该看到：
# ✅ Health check passed
# ✅ System info retrieved
# ✅ Documents retrieved
# ✅ Query successful
```

### Step 4: 运行评估

```bash
# 方式 A: 使用脚本（推荐）
./evaluation/run_evaluation.sh

# 方式 B: 直接运行 Python
python3 evaluation/scripts/evaluate_rag.py
```

## 📋 详细流程

### 1. 完整评估（首次运行）

```bash
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

