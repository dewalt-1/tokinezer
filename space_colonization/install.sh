#!/bin/bash
# Raspberry Pi Installation Script for Space Colonization Token Visualizer

set -e

echo "========================================"
echo "  RPi Token Visualizer Setup"
echo "========================================"
echo ""

# Check if running on ARM
ARCH=$(uname -m)
if [[ "$ARCH" != "aarch64" && "$ARCH" != "armv7l" ]]; then
    echo "WARNING: This script is designed for Raspberry Pi (ARM architecture)"
    echo "Detected: $ARCH"
    echo ""
fi

# Install system dependencies
echo "[1/4] Installing system dependencies..."
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git cmake build-essential curl psmisc

# Clone and build llama.cpp
if [ ! -d "llama.cpp" ]; then
    echo "[2/4] Cloning and building llama.cpp..."
    git clone https://github.com/ggerganov/llama.cpp
    cd llama.cpp
    make -j$(nproc)
    cd ..
else
    echo "[2/4] llama.cpp already exists, skipping..."
fi

# Setup Python virtual environment
echo "[3/4] Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt

# Make run script executable
chmod +x run.sh

echo ""
echo "[4/4] Setup complete!"
echo ""
echo "========================================"
echo "  Next Steps"
echo "========================================"
echo ""
echo "1. Download a GGUF model (recommended: TinyLlama, Phi-2, or Qwen2 0.5B)"
echo "   Example: wget https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
echo ""
echo "2. Start the llama.cpp server:"
echo "   ./llama.cpp/llama-server -m /path/to/model.gguf --port 8080 -c 2048"
echo ""
echo "3. In another terminal, start the visualization:"
echo "   ./run.sh"
echo ""
echo "4. Open Chromium browser to: http://localhost:8001"
echo ""
echo "For kiosk mode (fullscreen), run:"
echo "   chromium-browser --kiosk http://localhost:8001"
echo ""
