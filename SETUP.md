# Setup Guide - Virtual Environment

## Step-by-Step Setup for "tokenviz" Virtual Environment

### Step 1: Create the Virtual Environment

Navigate to your project directory and create a virtual environment named "tokenviz":

```bash
cd /Users/bendrusinsky/Documents/MicrodosingAI/tokinezer
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
__pycache__/
*.pyc
.DS_Store
```
