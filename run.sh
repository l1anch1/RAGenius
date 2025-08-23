#!/bin/bash

# RAGenius 启动脚本
echo "Starting RAGenius..."

# 清理旧进程
echo "Cleaning up old processes..."
pkill -f "python.*app" 2>/dev/null
pkill -f "npm run dev" 2>/dev/null
sleep 2

# 激活conda环境
source ~/miniconda3/etc/profile.d/conda.sh
conda activate RAG

# 设置PYTHONPATH
export PYTHONPATH=/Users/lianchi/Documents/CS/RAGenius/backend:$PYTHONPATH

# 清理函数
cleanup() {
    echo "Stopping all services..."
    if [ ! -z "$FLASK_PID" ]; then
        kill $FLASK_PID 2>/dev/null
    fi
    if [ ! -z "$VITE_PID" ]; then
        kill $VITE_PID 2>/dev/null
    fi
    pkill -f "python.*app" 2>/dev/null
    pkill -f "npm run dev" 2>/dev/null
    exit 0
}

# 设置信号处理
trap cleanup EXIT INT TERM

# 启动后端
echo "Starting backend..."
cd /Users/lianchi/Documents/CS/RAGenius
( PYTHONPATH=/Users/lianchi/Documents/CS/RAGenius/backend python3 backend/app.py ) &
FLASK_PID=$!
echo "Backend started with PID: $FLASK_PID"

# 等待后端启动
sleep 5

# 启动前端
echo "Starting frontend..."
cd /Users/lianchi/Documents/CS/RAGenius/frontend
npm run dev &
VITE_PID=$!
echo "Frontend started with PID: $VITE_PID"

echo "All services started!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "Press Ctrl+C to stop all services"

# 等待进程
wait
