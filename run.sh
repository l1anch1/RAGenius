#!/bin/bash

# 确保脚本在发生错误时停止
set -e

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

# 启动后端 Flask 应用
echo -e "${GREEN}启动 Flask 后端...${NC}"
( cd backend && python app.py ) &

# 启动 Vite 前端
echo -e "${GREEN}启动 Vite 前端...${NC}"
( cd frontend && npm run dev ) &

# 读取进程的 PID
FLASK_PID=$!

# 在后台运行后，给予用户提示以停止服务
trap 'kill $FLASK_PID' EXIT  # 在脚本退出时杀死后端进程

# 等待后台进程完成
wait $FLASK_PID

echo -e "${GREEN}所有服务已停止！${NC}"