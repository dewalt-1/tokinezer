#!/bin/bash
cd "$(dirname "$0")"

echo "========================================"
echo "  Space Colonization Token Visualizer"
echo "========================================"
echo ""

# Check if llama.cpp server is running
if ! curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo "WARNING: llama.cpp server not detected on port 8080"
    echo "Start it with: ./llama.cpp/build/bin/llama-server -m /path/to/model.gguf --port 8080"
    echo ""
fi

# Kill any existing processes on our ports (Linux compatible)
fuser -k 8000/tcp 2>/dev/null || true
fuser -k 8001/tcp 2>/dev/null || true
sleep 1

# Activate venv
source venv/bin/activate

# Start backend
echo "Starting backend on :8000..."
python backend/server.py &
PID1=$!
sleep 2

# Start frontend
echo "Starting frontend on :8001..."
cd frontend && python -m http.server 8001 &
PID2=$!

echo ""
echo "========================================"
echo "  Open in browser: http://localhost:8001"
echo "========================================"
echo ""
echo "Controls:"
echo "  UP/DOWN  - Navigate token options"
echo "  SPACE    - Select token"
echo ""
echo "Press Ctrl+C to stop"
echo ""

trap "kill $PID1 $PID2 2>/dev/null" EXIT
wait
