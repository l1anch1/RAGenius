#!/bin/bash

# RAGenius Cleanup Script
# Clean up all related processes and ports

# Define colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🧹 Cleaning up RAGenius processes...${NC}"
echo ""

# Find and display related processes
echo -e "${GREEN}📋 Finding related processes:${NC}"

FLASK_PROCESSES=$(pgrep -f "python.*app.py" 2>/dev/null || true)
VITE_PROCESSES=$(pgrep -f "vite" 2>/dev/null || true)
NODE_PROCESSES=$(pgrep -f "node.*vite" 2>/dev/null || true)

if [ ! -z "$FLASK_PROCESSES" ]; then
    echo "   Flask processes: $FLASK_PROCESSES"
fi

if [ ! -z "$VITE_PROCESSES" ]; then
    echo "   Vite processes: $VITE_PROCESSES"
fi

if [ ! -z "$NODE_PROCESSES" ]; then
    echo "   Node processes: $NODE_PROCESSES"
fi

if [ -z "$FLASK_PROCESSES" ] && [ -z "$VITE_PROCESSES" ] && [ -z "$NODE_PROCESSES" ]; then
    echo "   No related processes found"
fi

echo ""

# Kill processes
echo -e "${RED}🔪 Terminating processes...${NC}"
pkill -f "python.*app.py" 2>/dev/null && echo "   ✅ Flask processes terminated" || echo "   ⏭️  No Flask processes"
pkill -f "vite" 2>/dev/null && echo "   ✅ Vite processes terminated" || echo "   ⏭️  No Vite processes"
pkill -f "node.*vite" 2>/dev/null && echo "   ✅ Node processes terminated" || echo "   ⏭️  No Node processes"

echo ""

# Check and clean up port usage
echo -e "${GREEN}🔌 Checking port usage:${NC}"

PORT_3000=$(lsof -ti:3000 2>/dev/null || true)
PORT_8000=$(lsof -ti:8000 2>/dev/null || true)

if [ ! -z "$PORT_3000" ]; then
    echo "   Port 3000 is used by process $PORT_3000"
    kill -9 $PORT_3000 2>/dev/null && echo "   ✅ Force terminated" || true
else
    echo "   ✅ Port 3000 is free"
fi

if [ ! -z "$PORT_8000" ]; then
    echo "   Port 8000 is used by process $PORT_8000"
    kill -9 $PORT_8000 2>/dev/null && echo "   ✅ Force terminated" || true
else
    echo "   ✅ Port 8000 is free"
fi

# Wait for processes to fully exit
sleep 1

echo ""
echo -e "${GREEN}✨ Cleanup complete!${NC}"
echo ""
echo "You can now run:"
echo "  • Docker:  docker-compose up -d"
echo "  • Local:   ./run.sh"
