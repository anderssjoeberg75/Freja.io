#!/bin/bash

echo "🚀 Starting DAA - Mainframe & Client"
echo "===================================="

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Kill any existing processes on our ports (prevents "address already in use")
echo "🧹 Cleaning up old processes..."
pkill -f "python3 main.py" 2>/dev/null
fuser -k 8000/tcp 2>/dev/null
sleep 2
lsof -ti:5173 | xargs -r kill -9 2>/dev/null
sleep 1

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $BACKEND_PID $CLIENT_PID 2>/dev/null
    exit 0
}

# Trap SIGINT (Ctrl+C) and SIGTERM
trap cleanup SIGINT SIGTERM

# Setup virtual environment if needed
VENV_DIR="$SCRIPT_DIR/venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo "📦 Installing dependencies..."
    "$VENV_DIR/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"
fi

# Start Backend with venv
echo "📡 Starting Backend (Mainframe)..."
cd "$SCRIPT_DIR"
mkdir -p logs
"$VENV_DIR/bin/python" main.py > logs/daa.log 2>&1 &
BACKEND_PID=$!

# Wait a moment for backend to initialize
sleep 3

# Start Client
echo "🖥️  Starting Client (Vite Dev Server)..."
cd "$SCRIPT_DIR/client"
npm run dev &
CLIENT_PID=$!

echo ""
echo "✅ Services started!"
echo "   Backend PID:  $BACKEND_PID"
echo "   Client PID:   $CLIENT_PID"
echo ""
echo "Press Ctrl+C to stop both services"

# Wait for both processes
wait $BACKEND_PID $CLIENT_PID
