# 🚀 RAG 评估 - 一键运行指南

## 最简单的运行方式（3 步）

### 1️⃣ 启动服务
```bash
cd /Users/lianchi/Documents/CS/RAGenius
docker compose up -d
```

### 2️⃣ 激活环境
```bash
conda activate ragenius
```

### 3️⃣ 运行评估
```bash
./evaluation/run_evaluation.sh
```

**就这么简单！** ✨

---

## ⏱️ 等待时间

- **100 个问题**：约 9-10 分钟
- 每题平均：5-6 秒
- 喝杯咖啡回来就好了 ☕

---

## 📊 结果在哪里？

评估完成后，自动生成：

```bash
evaluation/results/
├── evaluation_results.png          # 📊 可视化图表
├── evaluation_results.svg          # 📊 矢量图（高清）
├── EVALUATION_REPORT.md            # 📄 详细报告
└── evaluation_report.json          # 📊 原始数据
```

**查看图表**：
```bash
open evaluation/results/evaluation_results.png
```

**查看报告**：
```bash
cat evaluation/results/EVALUATION_REPORT.md
```

---

## 🎯 快捷命令

### 测试连接（不运行评估）
```bash
python3 evaluation/test_connection.py
```

### 快速测试（只测 20 题）
```bash
python3 evaluation/scripts/evaluate_rag.py --num-questions 20
```

### 跳过文档上传（更快）
```bash
python3 evaluation/scripts/evaluate_rag.py --skip-upload
```

### 指定服务器地址
```bash
python3 evaluation/scripts/evaluate_rag.py --backend-url http://你的IP:8000
```

---

## ❓ 遇到问题？

### 问题 1: `ModuleNotFoundError`
```bash
# 解决：安装依赖
pip install -r evaluation/requirements.txt
```

### 问题 2: 连接失败
```bash
# 解决：检查服务是否运行
docker compose ps

# 如果没运行，启动它
docker compose up -d
```

### 问题 3: 权限错误
```bash
# 解决：添加执行权限
chmod +x evaluation/run_evaluation.sh
```

---

## 📝 完成后提交

```bash
# 提交评估结果
git add evaluation/
git commit -m "feat: RAG 评估数据集扩充至 100 题"
git push
```

---

## 💡 Pro Tips

1. **首次运行**会上传知识库（~20秒），后续可以用 `--skip-upload` 跳过
2. **没安装 ragas** 也能跑，会用简化版评估
3. **定期运行**（如每周），跟踪系统改进效果
4. **结果可视化**自动更新到 README 徽章

---

**就是这么简单！现在就试试吧！** 🎉
