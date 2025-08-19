#!/bin/bash

# 定义颜色用于输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # 无颜色

echo -e "${YELLOW}正在清理 RAGenius 相关进程...${NC}"

# 查找并显示相关进程
echo -e "${GREEN}查找相关进程:${NC}"
FLASK_PROCESSES=$(pgrep -f "python3.*app.py" 2>/dev/null || true)
VITE_PROCESSES=$(pgrep -f "vite --open" 2>/dev/null || true)
NODE_VITE_PROCESSES=$(pgrep -f "node.*vite" 2>/dev/null || true)

if [ ! -z "$FLASK_PROCESSES" ]; then
    echo "Flask 进程: $FLASK_PROCESSES"
fi

if [ ! -z "$VITE_PROCESSES" ]; then
    echo "Vite 进程: $VITE_PROCESSES"
fi

if [ ! -z "$NODE_VITE_PROCESSES" ]; then
    echo "Node Vite 进程: $NODE_VITE_PROCESSES"
fi

# 清理进程
echo -e "${RED}终止进程...${NC}"
pkill -f "python3.*app.py" 2>/dev/null && echo "已终止 Flask 进程" || true
pkill -f "vite --open" 2>/dev/null && echo "已终止 Vite 进程" || true  
pkill -f "node.*vite" 2>/dev/null && echo "已终止 Node Vite 进程" || true

# 检查端口占用
echo -e "${GREEN}检查端口占用:${NC}"
PORT_3000=$(lsof -ti:3000 2>/dev/null || true)
PORT_8000=$(lsof -ti:8000 2>/dev/null || true)

if [ ! -z "$PORT_3000" ]; then
    echo "端口 3000 被进程 $PORT_3000 占用"
    kill -9 $PORT_3000 2>/dev/null && echo "已强制终止占用端口 3000 的进程" || true
fi

if [ ! -z "$PORT_8000" ]; then
    echo "端口 8000 被进程 $PORT_8000 占用"
    kill -9 $PORT_8000 2>/dev/null && echo "已强制终止占用端口 8000 的进程" || true
fi

# 等待进程完全退出
sleep 2

echo -e "${GREEN}清理完成！${NC}"
echo "现在可以重新运行 ./run.sh"
