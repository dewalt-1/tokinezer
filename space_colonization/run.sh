#!/bin/bash
cd "$(dirname "$0")"

# Kill any existing processes on our ports
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:8001 | xargs kill -9 2>/dev/null
sleep 1

# Activate venv
source venv/bin/activate

# Start backend
echo "Starting backend on :8000"
python backend/server.py &
PID1=$!
sleep 2

# Start frontend
echo "Starting frontend on http://localhost:8001"
cd frontend && python -m http.server 8001 &
PID2=$!

trap "kill $PID1 $PID2 2>/dev/null" EXIT
wait
