#!/bin/bash

# AI Chat Assistant Start Script
# Usage: ./start.sh [backend|frontend] [port]
#   backend - Start backend on specified port (default: 6969)
#   frontend - Start frontend on specified port (default: 3000)
#   [port] - Port number to use for the service
# Examples:
#   ./start.sh backend 8001      # Backend on port 8001, frontend on 3000
#   ./start.sh frontend 8080      # Backend on 6969, frontend on 8080
#   ./start.sh 8080           # Frontend only on port 8080

# Show usage if no arguments or invalid arguments
if [ $# -eq 0 ]; then
    echo "Usage: $0 [backend|frontend] [port]"
    echo ""
    echo "Arguments:"
    echo "  backend      - Start backend service only (default port: $DEFAULT_BACKEND_PORT)"
    echo "  frontend      - Start frontend service only (default port: $DEFAULT_FRONTEND_PORT)"
    echo "  [port]        - Custom port for the service"
    echo ""
    echo "Examples:"
    echo "  $0 backend 8001          # Backend on port 8001, frontend on 3000"
    echo "  $0 frontend 8080          # Frontend only on port 8080"
    echo "  $0 8080                   # Backend on 6969, frontend on 8080"
    echo "  [backend|frontend] [port]    # Specify custom port for backend or frontend"
    echo "  Example: ./start.sh frontend 8080    # Frontend on port 8080 (backend uses default 6969)"
    exit 0
fi

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# Default ports
DEFAULT_BACKEND_PORT=6969
DEFAULT_FRONTEND_PORT=3000

# Parse command line arguments
SERVICE=${1:-}
BACKEND_PORT=${2:-$DEFAULT_BACKEND_PORT}
FRONTEND_PORT=${3:-$DEFAULT_FRONTEND_PORT}

# Validate port numbers
if ! [[ "$BACKEND_PORT" =~ ^[0-9]+$ ]]; then
    echo "❌ Error: Backend port must be a number (got: '$BACKEND_PORT')"
    exit 1
fi

if ! [[ "$FRONTEND_PORT" =~ ^[0-9]+$ ]]; then
    echo "❌ Error: Frontend port must be a number (got: '$FRONTEND_PORT')"
    exit 1
fi

echo "🚀 Starting AI Chat Assistant..."
echo ""

# === Backend Setup ===
echo "📦 Setting up backend on port $BACKEND_PORT..."

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
    PORT=$FRONTEND_PORT npm install
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

    # Kill processes more gracefully with proper termination
    if [ ! -z "$BACKEND_PID" ]; then
        # Send SIGTERM to allow graceful shutdown
        kill -TERM $BACKEND_PID 2>/dev/null || true
        # Wait for process to actually terminate
        for i in {1..10}; do
            if ! kill -0 $BACKEND_PID 2>/dev/null; then
                break
            fi
        done
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        # Send SIGTERM to allow graceful shutdown
        kill -TERM $FRONTEND_PID 2>/dev/null || true
        # Wait for process to actually terminate
        for i in {1..10}; do
            if ! kill -0 $FRONTEND_PID 2>/dev/null; then
                break
            fi
        done
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
echo "   Starting frontend on http://localhost:$FRONTEND_PORT (with hot-reload)"
echo "   Frontend will automatically reload when files change"
PORT=$FRONTEND_PORT npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Services started!"
echo ""
echo "   📟 Backend API:  http://localhost:$BACKEND_PORT"
echo "   📟 API Docs:     http://localhost:$BACKEND_PORT/docs"
echo "   📟 Frontend:     http://localhost:$FRONTEND_PORT"
echo ""
echo "   🔥 Hot Reload Enabled:"
echo "      • Backend: Auto-reloads on Python file changes (port $BACKEND_PORT)"
echo "      • Frontend: Auto-reloads on file changes (Next.js) (port $FRONTEND_PORT)"
echo "      • Backend logs: tail -f /tmp/backend.log"
echo "      • Usage: ./start.sh [backend|frontend] [port]"
echo "      • Example: ./start.sh backend 8001 frontend 4000"
echo ""
echo "   Press Ctrl+C to stop all services"
echo ""

# Wait for any background process to exit
wait $BACKEND_PID $FRONTEND_PID
