# Space Colonization Token Visualizer - Raspberry Pi

An interactive token exploration tool using the space colonization algorithm. Watch LLM tokens branch out organically like a growing tree.

## Hardware Requirements

- Raspberry Pi 4 or 5 (4GB+ RAM recommended)
- MicroSD card (32GB+)
- Display (HDMI)
- Keyboard for interaction
- Internet connection (for setup)

## Model Recommendations

Small models that work well on RPi:

| Model | Size | RAM Usage | Speed |
|-------|------|-----------|-------|
| TinyLlama 1.1B Q4 | ~700MB | ~1.5GB | Fast |
| Phi-2 Q4 | ~1.6GB | ~2.5GB | Medium |
| Qwen2 0.5B Q4 | ~400MB | ~1GB | Very Fast |

## Quick Start

```bash
# Clone the repository
git clone -b rpi https://github.com/YOUR_USERNAME/tokinezer.git
cd tokinezer/space_colonization

# Run the installer
chmod +x install.sh
./install.sh

# Download a model (example: TinyLlama)
wget https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf

# Start llama.cpp server (Terminal 1)
./llama.cpp/llama-server -m tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf --port 8080 -c 2048

# Start visualization (Terminal 2)
./run.sh

# Open browser
chromium-browser http://localhost:8001
```

## Controls

| Key | Action |
|-----|--------|
| `↑` / `↓` | Navigate between token options |
| `Space` or `→` | Select token and grow tree |

## Kiosk Mode (Fullscreen)

For installations or displays, run the browser in kiosk mode:

```bash
chromium-browser --kiosk --noerrdialogs --disable-infobars http://localhost:8001
```

## Autostart on Boot

Create a systemd service to start everything automatically:

```bash
sudo nano /etc/systemd/system/tokenvis.service
```

Add:
```ini
[Unit]
Description=Token Visualizer
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/tokinezer/space_colonization
ExecStart=/bin/bash -c './llama.cpp/llama-server -m /home/pi/model.gguf --port 8080 -c 2048 & sleep 5 && ./run.sh'
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable tokenvis
sudo systemctl start tokenvis
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Raspberry Pi                       │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ llama.cpp   │  │ Python       │  │ Chromium   │ │
│  │ server      │──│ Backend      │──│ Browser    │ │
│  │ :8080       │  │ :8000        │  │ :8001      │ │
│  └─────────────┘  └──────────────┘  └────────────┘ │
└─────────────────────────────────────────────────────┘
```

## MQTT Output (Coming Soon)

The selected tokens can be published via MQTT to another device:

```python
# Configure in backend/server.py
MQTT_BROKER = "other-pi.local"
MQTT_TOPIC = "tokens/selected"
```

## Troubleshooting

### "llama.cpp server not detected"
- Ensure llama.cpp is running: `curl http://localhost:8080/health`
- Check model path is correct

### Slow token generation
- Use smaller quantized models (Q4_K_M or Q4_0)
- Reduce context size: `-c 1024`

### Browser freezes
- Reduce attractor count in sketch.js: `NumAttractors = 4000`
- Lower the growth rate

### Out of memory
- Use swap: `sudo dphys-swapfile swapoff && sudo nano /etc/dphys-swapfile` (set CONF_SWAPSIZE=2048)
- Use smaller model

## Files

```
space_colonization/
├── backend/
│   ├── server.py           # WebSocket server wrapping llama.cpp
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── index.html          # Web page
│   ├── sketch.js           # p5.js visualization
│   └── sound.js            # Audio (optional)
├── install.sh              # Setup script
├── run.sh                  # Launch script
└── README.md               # This file
```

## License

MIT
