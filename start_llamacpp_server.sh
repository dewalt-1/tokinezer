#!/bin/bash

# Start llama.cpp server with probability output enabled
# This runs on port 8080 (different from Ollama's 11434)

MODEL_PATH="./models/mistral.gguf"
PORT=8080
HOST="127.0.0.1"

echo "Starting llama.cpp server with probability output..."
echo "Model: $MODEL_PATH"
echo "URL: http://$HOST:$PORT"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start server with options:
# -m: model path
# --host: bind address
# --port: port number
# -c: context size
# -n: max tokens to predict
# --log-format: log format (text is more readable)

llama-server \
  -m "$MODEL_PATH" \
  --host "$HOST" \
  --port "$PORT" \
  -c 2048
