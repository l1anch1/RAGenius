#!/bin/bash

# 确保脚本在发生错误时停止
set -e

# 激活 conda 环境
source ~/miniconda3/etc/profile.d/conda.sh
conda activate RAG

# 定义颜色用于输出
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # 无颜色

# 确保 backend 和 frontend 目录存在
if [ ! -d "./backend" ]; then
    echo -e "${RED}错误: backend 目录不存在${NC}"
    exit 1
fi

if [ ! -d "./frontend" ]; then
    echo -e "${RED}错误: frontend 目录不存在${NC}"
    exit 1
fi

# 清理可能残留的进程
echo -e "${GREEN}清理残留进程...${NC}"
pkill -f "python3.*app.py" 2>/dev/null || true
pkill -f "vite --open" 2>/dev/null || true
pkill -f "node.*vite" 2>/dev/null || true
sleep 1

# 启动后端 Flask 应用
echo -e "${GREEN}启动 Flask 后端...${NC}"
( PYTHONPATH=backend python3 backend/app.py ) &
FLASK_PID=$!

# 启动 Vite 前端
echo -e "${GREEN}启动 Vite 前端...${NC}"
( cd frontend && npm run dev ) &
VITE_PID=$!

# 清理函数
cleanup() {
    echo -e "\n${RED}正在停止所有服务...${NC}"
    
    # 杀死启动的进程
    if [ ! -z "$FLASK_PID" ]; then
        kill $FLASK_PID 2>/dev/null
        echo "停止 Flask 后端 (PID: $FLASK_PID)"
    fi
    
    if [ ! -z "$VITE_PID" ]; then
        kill $VITE_PID 2>/dev/null
        echo "停止 Vite 前端 (PID: $VITE_PID)"
    fi
    
    # 强制清理可能残留的进程
    pkill -f "python3.*app.py" 2>/dev/null
    pkill -f "vite --open" 2>/dev/null
    pkill -f "node.*vite" 2>/dev/null
    
    # 等待进程完全退出
    sleep 2
    
    echo -e "${GREEN}所有服务已停止！${NC}"
    exit 0
}

# 设置信号处理
trap cleanup EXIT INT TERM

echo -e "${GREEN}服务已启动！${NC}"
echo "Flask 后端: http://localhost:8000"
echo "Vite 前端: http://localhost:3000"
echo "按 Ctrl+C 停止所有服务"

# 等待任一进程完成
wait