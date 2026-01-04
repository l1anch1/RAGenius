#!/bin/bash

# RAG System Evaluation Script
# 运行 RAG 系统评估

set -e

echo "=================================================="
echo "🚀 RAGenius - RAG System Evaluation"
echo "=================================================="
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.8+."
    exit 1
fi

echo "✅ Python3 found: $(python3 --version)"
echo ""

# 检查并安装依赖
echo "📦 Checking dependencies..."
if ! python3 -c "import ragas" 2>/dev/null; then
    echo "⚠️  Ragas not installed. Installing dependencies..."
    pip3 install -r evaluation/requirements.txt
else
    echo "✅ Dependencies already installed"
fi

echo ""
echo "▶️  Running evaluation..."
echo ""

# 运行评估
cd "$(dirname "$0")/.." || exit
python3 evaluation/scripts/evaluate_rag.py

echo ""
echo "=================================================="
echo "✅ Evaluation Complete!"
echo "=================================================="
echo ""
echo "📁 Results saved in: evaluation/results/"
echo "📊 View the report: evaluation/results/EVALUATION_REPORT.md"
echo "🖼️  View the chart: evaluation/results/evaluation_results.png"
echo ""

