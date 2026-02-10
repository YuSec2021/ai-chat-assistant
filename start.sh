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
echo "   Starting backend on http://localhost:6969 (with auto-reload)"
echo "   Backend will automatically reload when Python files change"
.venv/bin/python3 -m uvicorn src.main:app --host 0.0.0.0 --port 6969 --reload > /tmp/backend.log 2>&1 &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 2

# Check if backend started successfully
if ps -p $BACKEND_PID > /dev/null; then
    echo "   ✓ Backend started successfully (PID: $BACKEND_PID)"
    echo "   → Backend logs: tail -f /tmp/backend.log"
else
    echo "   ✗ Backend failed to start. Check logs: cat /tmp/backend.log"
    exit 1
fi

# Start frontend
cd "$FRONTEND_DIR"
echo "   Starting frontend on http://localhost:3000 (with hot-reload)"
echo "   Frontend will automatically reload when files change"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Services started!"
echo ""
echo "   📟 Backend API:  http://localhost:6969"
echo "   📟 API Docs:     http://localhost:6969/docs"
echo "   🎨 Frontend:     http://localhost:3000"
echo ""
echo "   🔥 Hot Reload Enabled:"
echo "      • Backend: Auto-reloads on Python file changes"
echo "      • Frontend: Auto-reloads on file changes (Next.js)"
echo "      • Backend logs: tail -f /tmp/backend.log"
echo ""
echo "   Press Ctrl+C to stop all services"
echo ""

# Wait for any background process to exit
wait $BACKEND_PID $FRONTEND_PID
