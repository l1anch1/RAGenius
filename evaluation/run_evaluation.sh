#!/bin/bash

# RAG System Evaluation Script
# 运行 RAG 系统评估（连接真实后端）

set -e

# 默认参数
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
SKIP_UPLOAD="${SKIP_UPLOAD:-false}"

# 显示帮助
show_help() {
    cat << EOF
RAGenius RAG System Evaluation

用法: 
  ./run_evaluation.sh [选项]

选项:
  --backend-url URL    后端 API 地址 (默认: http://localhost:8000)
  --skip-upload        跳过文档上传（使用现有知识库）
  -h, --help           显示此帮助信息

环境变量:
  BACKEND_URL          后端 API 地址
  SKIP_UPLOAD          是否跳过上传 (true/false)

示例:
  # 评估本地后端
  ./run_evaluation.sh

  # 评估远程后端
  ./run_evaluation.sh --backend-url http://your-server:8000

  # 跳过文档上传（使用现有知识库）
  ./run_evaluation.sh --skip-upload

  # 评估 Docker 部署
  BACKEND_URL=http://localhost:8000 ./run_evaluation.sh

EOF
}

# 解析命令行参数
EXTRA_ARGS=""
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        --backend-url)
            BACKEND_URL="$2"
            EXTRA_ARGS="$EXTRA_ARGS --backend-url $2"
            shift 2
            ;;
        --skip-upload)
            SKIP_UPLOAD="true"
            EXTRA_ARGS="$EXTRA_ARGS --skip-upload"
            shift
            ;;
        *)
            echo "❌ Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

echo "========================================================"
echo "🚀 RAGenius - Real RAG System Evaluation"
echo "========================================================"
echo ""
echo "🔗 Backend URL: $BACKEND_URL"
echo "📚 Skip Upload: $SKIP_UPLOAD"
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
if ! python3 -c "import requests" 2>/dev/null; then
    echo "⚠️  Installing required dependencies..."
    pip3 install requests tqdm 2>/dev/null || {
        echo "❌ Failed to install dependencies"
        exit 1
    }
fi

if ! python3 -c "import ragas" 2>/dev/null; then
    echo "⚠️  Ragas not installed. Installing all dependencies..."
    pip3 install -r evaluation/requirements.txt 2>/dev/null || {
        echo "⚠️  Failed to install optional dependencies (ragas)"
        echo "💡 Evaluation will use simplified metrics"
    }
else
    echo "✅ All dependencies installed"
fi

echo ""

# 检查后端是否可用
echo "🔍 Checking backend availability..."
if curl -s -f "$BACKEND_URL/api/health" > /dev/null 2>&1; then
    echo "✅ Backend is running at $BACKEND_URL"
else
    echo "❌ Backend not available at $BACKEND_URL"
    echo ""
    echo "💡 Please start the backend first:"
    echo "   cd /path/to/RAGenius"
    echo "   docker compose up -d"
    echo ""
    exit 1
fi

echo ""
echo "▶️  Running evaluation..."
echo ""

# 运行评估
cd "$(dirname "$0")/.." || exit
python3 evaluation/scripts/evaluate_rag.py $EXTRA_ARGS

echo ""
echo "========================================================"
echo "✅ Evaluation Complete!"
echo "========================================================"
echo ""
echo "📁 Results saved in: evaluation/results/"
echo "📊 View the report: evaluation/results/EVALUATION_REPORT.md"
echo "🖼️  View the chart: evaluation/results/evaluation_results.svg"
echo ""

