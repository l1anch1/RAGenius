#!/bin/bash

# RAGenius Startup Script
# For local development environment

set -e

# Get script directory (project root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting RAGenius..."
echo "📁 Project directory: $SCRIPT_DIR"

# Clean up old processes
echo "🧹 Cleaning up old processes..."
pkill -f "python.*app.py" 2>/dev/null || true
pkill -f "npm run dev" 2>/dev/null || true
sleep 2

# Check Python environment
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Python not found. Please install Python 3.8+"
    exit 1
fi

echo "🐍 Using Python: $($PYTHON_CMD --version)"

# Set PYTHONPATH
export PYTHONPATH="$SCRIPT_DIR/backend:$PYTHONPATH"

# Cleanup function
cleanup() {
    echo ""
    echo "🛑 Stopping all services..."
    if [ ! -z "$FLASK_PID" ]; then
        kill $FLASK_PID 2>/dev/null || true
    fi
    if [ ! -z "$VITE_PID" ]; then
        kill $VITE_PID 2>/dev/null || true
    fi
    pkill -f "python.*app.py" 2>/dev/null || true
    pkill -f "npm run dev" 2>/dev/null || true
    echo "👋 Goodbye!"
    exit 0
}

# Set signal handlers
trap cleanup EXIT INT TERM

# Start backend
echo "🔧 Starting backend..."
cd "$SCRIPT_DIR"
PYTHONPATH="$SCRIPT_DIR/backend" $PYTHON_CMD backend/app.py &
FLASK_PID=$!
echo "✅ Backend started with PID: $FLASK_PID"

# Wait for backend to start
sleep 5

# Check frontend dependencies
if [ ! -d "$SCRIPT_DIR/frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd "$SCRIPT_DIR/frontend"
    npm install
fi

# Start frontend
echo "🎨 Starting frontend..."
cd "$SCRIPT_DIR/frontend"
npm run dev &
VITE_PID=$!
echo "✅ Frontend started with PID: $VITE_PID"

echo ""
echo "=========================================="
echo "🎉 All services started!"
echo "📡 Backend:  http://localhost:8000"
echo "🌐 Frontend: http://localhost:3000"
echo "=========================================="
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for processes
wait
