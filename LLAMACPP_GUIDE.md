# LLaMA.cpp Probability Visualization Guide

This guide shows you how to visualize **token probabilities** and see **how the model selects each token** using llama.cpp.

## What You Get

Unlike Ollama (which hides internals), llama.cpp exposes:
- **Top-N token probabilities** at each generation step
- **Alternative tokens** the model considered but didn't choose
- **Probability scores** showing how confident the model was
- **Decision tree view** of the generation process

## Quick Start

### 1. Start the llama.cpp Server

In one terminal, start the server:

```bash
cd /Users/bendrusinsky/Documents/MicrodosingAI/tokinezer
./start_llamacpp_server.sh
```

The server will run on `http://127.0.0.1:8080` (different from Ollama's port 11434).

### 2. Run the Probability Visualizer

In another terminal (with your venv activated):

```bash
# Activate venv
source tokenviz/bin/activate

# Basic usage - shows top 5 alternatives per token
python llamacpp_probability_visualizer.py --prompt "Hello, my name is"

# Show more alternatives (top 10)
python llamacpp_probability_visualizer.py --prompt "The capital of France is" --n-probs 10

# Decision tree view (shows choices at each step)
python llamacpp_probability_visualizer.py --prompt "Once upon a time" --tree

# Adjust temperature for randomness
python llamacpp_probability_visualizer.py --prompt "AI is" --temperature 1.0
```

## What the Output Shows

### Standard View

For each generated token, you'll see:

```
[0] ' Hello' (p=0.8532)
  Alternatives:
    1. ' Hi' (p=0.0821) ████████░░░░░░░░░░░░
    2. ' Hey' (p=0.0234) ████░░░░░░░░░░░░░░░░
    3. ' Good' (p=0.0156) ███░░░░░░░░░░░░░░░░░
```

This shows:
- The **selected token** (' Hello') with its probability (85.32%)
- **Alternative tokens** the model considered
- Visual **probability bars** showing relative likelihood

### Decision Tree View

Shows the generation as a branching tree:

```
→ [85.32%] ' Hello' (chosen)
    [8.21%] ' Hi'
    [2.34%] ' Hey'

  → [72.15%] ',' (chosen)
      [15.23%] '!'
      [5.67%] ' there'

    → [91.45%] ' my' (chosen)
        [3.21%] ' I'
        [2.11%] ' how'
```

## Command Line Options

```
--prompt, -p         Prompt text (required)
--n-probs, -n        Number of alternatives to show (default: 5)
--temperature, -t    Sampling temperature 0.0-2.0 (default: 0.7)
--max-tokens, -m     Maximum tokens to generate (default: 50)
--tree               Show decision tree view
--no-alternatives    Only show selected tokens, hide alternatives
--base-url          Server URL (default: http://127.0.0.1:8080)
```

## Understanding the Output

### Temperature Effects

- **Low temperature (0.1-0.5)**: More deterministic, higher probabilities for top choices
- **Medium temperature (0.6-0.9)**: Balanced, creative but coherent
- **High temperature (1.0-2.0)**: More random, lower probabilities spread across options

### Probability Interpretation

- **p > 0.5**: Model is very confident in this choice
- **p = 0.2-0.5**: Moderate confidence, strong alternative exists
- **p < 0.2**: Low confidence, many viable alternatives

## Comparing with Ollama Visualizers

| Feature | Ollama Visualizer | LLaMA.cpp Visualizer |
|---------|------------------|---------------------|
| Token numbers | ✅ Yes | ✅ Yes |
| Token text | ✅ Yes | ✅ Yes |
| Token probabilities | ❌ No | ✅ Yes |
| Alternative tokens | ❌ No | ✅ Yes |
| Decision tree | ❌ No | ✅ Yes |
| Sampling params visible | ⚠️ Limited | ✅ Full control |

## Tips

1. **Start with small max-tokens** when exploring probabilities (10-20 tokens)
2. **Use --tree view** for understanding decision-making on short generations
3. **Increase --n-probs** to see more alternatives (useful for creative writing)
4. **Lower temperature** to see what the model is "most sure" about
5. **Higher temperature** to see the full range of possibilities

## Troubleshooting

### "Error: llama.cpp server is not running"
- Start the server: `./start_llamacpp_server.sh`
- Make sure it's on port 8080: `curl http://127.0.0.1:8080/health`

### "No probability data returned"
- The server needs to support `n_probs` parameter
- Make sure you're using a recent version of llama.cpp
- Try updating: `brew upgrade llama.cpp`

### Server is slow
- The Mistral model is ~4GB and runs on CPU by default
- On M1/M2/M3 Macs, Metal acceleration should be automatic
- Reduce context size in `start_llamacpp_server.sh` (change `-c 2048` to `-c 1024`)

## Advanced: Using Different Models

To use a different GGUF model:

1. Download or link a GGUF model to `./models/`
2. Edit `start_llamacpp_server.sh` to point to the new model
3. Restart the server

Example with a smaller model:
```bash
# Download a smaller model (faster)
curl -L -o models/tinyllama.gguf \
  https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
```

## Next Steps

- Experiment with different prompts to see how the model "thinks"
- Compare high vs low temperature outputs
- Try creative writing prompts to see alternative narrative paths
- Use for educational purposes to understand LLM behavior
