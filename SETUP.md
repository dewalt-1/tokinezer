# Setup Guide

This guide covers setup for all visualizers in this suite.

---

## Space Colonization Token Visualizer (Recommended)

An interactive, visual token exploration tool using the space colonization algorithm. Tokens branch out organically like a growing tree.

### Prerequisites

1. **llama.cpp** - Install via Homebrew:
   ```bash
   brew install llama.cpp
   ```

2. **A GGUF model** - Download or convert a model to GGUF format. You can use models from:
   - [Hugging Face](https://huggingface.co/models?search=gguf)
   - Convert Ollama models (stored in `~/.ollama/models/`)

### Setup

```bash
# Navigate to the space colonization directory
cd space_colonization

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install fastapi uvicorn websockets requests
```

### Running

**Terminal 1 - Start llama.cpp server:**
```bash
llama-server -m /path/to/your/model.gguf --port 8080
```

**Terminal 2 - Start the visualization:**
```bash
cd space_colonization
source venv/bin/activate
./run.sh
```

**Terminal 3 - Open browser:**
Navigate to `http://localhost:8001`

### Controls

| Key | Action |
|-----|--------|
| `↑` / `↓` | Navigate between token options |
| `Space` or `→` | Select token and grow tree |

### What You'll See

- **White branches** - Your selected path (the text you're building)
- **Gray branches** - Missed options growing in the background
- **Yellow dot** - Current position
- **Probability bars** - `████░░░░` showing relative likelihood
- **Token labels** - Text along your selected path

### Architecture

```
Browser (p5.js)  <-->  Python Backend (FastAPI)  <-->  llama.cpp server
   :8001                    :8000                         :8080
```

---

## Ollama Visualizers Setup

### Step-by-Step Setup for "tokenviz" Virtual Environment

### Step 1: Create the Virtual Environment

Navigate to your project directory and create a virtual environment named "tokenviz":

```bash
cd /path/to/tokinezer
python3 -m venv tokenviz
```

### Step 2: Activate the Virtual Environment

**On macOS/Linux:**
```bash
source tokenviz/bin/activate
```

**On Windows:**
```bash
tokenviz\Scripts\activate
```

You should see `(tokenviz)` appear at the beginning of your terminal prompt.

### Step 3: Upgrade pip (optional but recommended)

```bash
pip install --upgrade pip
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `requests` - For communicating with Ollama API
- `colorama` - For colored terminal output

### Step 5: Verify Installation

```bash
pip list
```

You should see the installed packages.

### Step 6: Make Sure Ollama is Running

In a **separate terminal** (don't activate the venv here), start Ollama:

```bash
ollama serve
```

### Step 7: Pull an Ollama Model (if needed)

Check if you have models:
```bash
ollama list
```

If no models are available, pull one:
```bash
ollama pull llama2
```

Other popular options:
- `ollama pull mistral`
- `ollama pull codellama`
- `ollama pull phi`

### Step 8: Run the Token Visualizer

Now back in your terminal with the activated venv:

```bash
python ollama_token_visualizer.py
```

Or with a direct prompt:
```bash
python ollama_token_visualizer.py --prompt "Hello, world!"
```

## Quick Reference Commands

### Activate venv
```bash
source tokenviz/bin/activate  # macOS/Linux
tokenviz\Scripts\activate      # Windows
```

### Deactivate venv
```bash
deactivate
```

### Run the visualizer
```bash
# Interactive mode
python ollama_token_visualizer.py

# With prompt
python ollama_token_visualizer.py -p "Your prompt here"

# Different model
python ollama_token_visualizer.py -m mistral -p "Your prompt"

# List models
python ollama_token_visualizer.py --list-models
```

## Troubleshooting

### "python3: command not found"
Try `python` instead of `python3`:
```bash
python -m venv tokenviz
```

### "No module named 'requests'" or "'colorama'"
Make sure you:
1. Activated the venv: `source tokenviz/bin/activate`
2. Installed dependencies: `pip install -r requirements.txt`

### "Error connecting to Ollama"
1. Make sure Ollama is running: `ollama serve`
2. Check it's accessible: `curl http://localhost:11434/api/tags`

## .gitignore Recommendation

If using git, add this to your `.gitignore`:
```
tokenviz/
venv/
space_colonization/venv/
__pycache__/
*.pyc
.DS_Store
```

---

## Troubleshooting

### Space Colonization Visualizer

**"WebSocket connection failed"**
- Make sure the backend is running: `cd space_colonization && ./run.sh`
- Check that port 8000 is free

**"llama_cpp disconnected" in health check**
- Make sure llama.cpp server is running on port 8080
- Test with: `curl http://localhost:8080/health`

**Tree not growing / stuck**
- The algorithm uses attractors placed with Perlin noise
- If near edges, the tree will naturally turn away
- Refresh the page to get new attractor distribution

**Slow token generation**
- Depends on your model size and hardware
- Smaller models (7B) are faster than larger ones
