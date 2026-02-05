#!/bin/bash

# AI Chat Assistant Start Script

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

echo "🚀 Starting AI Chat Assistant..."
echo ""

# === Backend Setup ===
echo "📦 Setting up backend..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please install it first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Install backend dependencies
cd "$BACKEND_DIR"
echo "   Installing Python dependencies..."
uv pip install -e . --quiet

# === Frontend Setup ===
echo "📦 Setting up frontend..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install it first:"
    echo "   Visit https://nodejs.org/"
    exit 1
fi

# Install frontend dependencies
cd "$FRONTEND_DIR"
if [ ! -d "node_modules" ] || [ ! -f "node_modules/.bin/next" ]; then
    echo "   Installing npm dependencies..."
    npm install
else
    echo "   ✓ Frontend dependencies already installed"
fi

# === Start Services ===
echo ""
echo "🌐 Starting services..."
echo ""

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    echo "✓ All services stopped"
    exit 0
}

# Set trap to cleanup on exit
trap cleanup SIGINT SIGTERM

# Start backend
cd "$BACKEND_DIR"
echo "   Starting backend on http://localhost:6969"
uv run uvicorn src.main:app --host 0.0.0.0 --port 6969 --reload &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 2

# Start frontend
cd "$FRONTEND_DIR"
echo "   Starting frontend on http://localhost:3000"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Services started!"
echo ""
echo "   📟 Backend API:  http://localhost:6969"
echo "   📟 API Docs:     http://localhost:6969/docs"
echo "   🎨 Frontend:     http://localhost:3000"
echo ""
echo "   Press Ctrl+C to stop all services"
echo ""

# Wait for any background process to exit
wait $BACKEND_PID $FRONTEND_PID
