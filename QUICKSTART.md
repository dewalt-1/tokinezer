# Quick Start Guide

Get up and running in 5 minutes!

## What Do You Want to See?

### Just Token Numbers and Text? → Use Ollama Visualizer

✅ **Easiest option** - works with your existing Ollama setup

```bash
# Activate your venv
source tokenviz/bin/activate

# Run it (Ollama already running in your menu bar)
python ollama_token_visualizer.py --prompt "Hello, world!"
```

### Want to See Probabilities and Alternatives? → Use LLaMA.cpp Visualizer

🎯 **More powerful** - shows how the model makes decisions

**Terminal 1 - Start llama.cpp server:**
```bash
cd /Users/bendrusinsky/Documents/MicrodosingAI/tokinezer
./start_llamacpp_server.sh
```

**Terminal 2 - Run visualizer:**
```bash
source tokenviz/bin/activate
python llamacpp_probability_visualizer.py --prompt "The capital of France is"
```

## Example Output

### Ollama Visualizer
```
TOKENS WITH NUMBERS
[0: Hello][1:,][2: how][3: are][4: you][5:?]

COMPLETE TEXT
Hello, how are you?
```

### LLaMA.cpp Probability Visualizer
```
[0] ' The' (p=0.9234)
  Alternatives:
    1. ' It' (p=0.0421) ████░░░░░░░░░░░░░░░░
    2. ' Paris' (p=0.0156) ███░░░░░░░░░░░░░░░░░
    3. ' France' (p=0.0089) █░░░░░░░░░░░░░░░░░░░

[1] ' capital' (p=0.8567)
  Alternatives:
    1. ' city' (p=0.0876) █████████░░░░░░░░░░░
    2. ' main' (p=0.0234) ██░░░░░░░░░░░░░░░░░░
```

Shows:
- **Selected token** with its probability
- **Alternative tokens** the model considered
- **Visual probability bars**

## File Guide

- **[README.md](README.md)** - Main documentation
- **[SETUP.md](SETUP.md)** - Virtual environment setup
- **[LLAMACPP_GUIDE.md](LLAMACPP_GUIDE.md)** - Detailed llama.cpp usage
- **This file** - Quick start (you are here!)

## Scripts

1. **ollama_token_visualizer.py** - Basic token visualization with Ollama
2. **ollama_token_visualizer2.py** - Experimental (explores Ollama API)
3. **llamacpp_probability_visualizer.py** - Advanced probability visualization
4. **start_llamacpp_server.sh** - Starts llama.cpp server

## Common Issues

### "Error connecting to Ollama"
- Check Ollama is running (icon in menu bar)
- Default model is `mistral:latest` - change with `--model`

### "Error: llama.cpp server is not running"
- Run `./start_llamacpp_server.sh` in a separate terminal
- Wait ~10 seconds for server to load the model

### "ModuleNotFoundError: No module named 'requests'"
- Activate your venv: `source tokenviz/bin/activate`
- Install deps: `pip install -r requirements.txt`

## Next Steps

- Try different prompts to see how tokenization works
- Experiment with temperature settings in llama.cpp visualizer
- Compare outputs between different models
- Use decision tree view (`--tree`) to understand model choices

Enjoy exploring how LLMs generate text! 🚀
