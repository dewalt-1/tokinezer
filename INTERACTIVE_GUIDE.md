# Interactive Token Tree Selector Guide

Build text by choosing tokens step-by-step with a live tree visualization of your path. Perfect for artistic installations and understanding how LLMs work.

## Quick Start

### Step 1: Make sure llama.cpp server is running

**Terminal 1:**
```bash
cd /Users/bendrusinsky/Documents/MicrodosingAI/tokinezer
./start_llamacpp_server.sh
```

Wait 10 seconds for the model to load.

### Step 2: Run the interactive selector

**Terminal 2:**
```bash
source tokenviz/bin/activate
python interactive_token_selector.py --prompt "The sky is"
```

## How It Works

1. You provide an initial prompt
2. The system shows:
   - **Path tree** - Visual tree of your choices so far
   - **Current text** - What you've built
   - **5 alternative tokens** (you can change this)
3. Each token shows:
   - The token text
   - Probability percentage
   - Visual probability bar
4. You type a number (1-5) to select that token
5. The token is added to your text and tree
6. Repeat until you type 'done'
7. See your final path tree and created text

## Example Session

```
============================================================
         INTERACTIVE TOKEN TREE SELECTOR
============================================================

Initial prompt: "The sky is"
Temperature: 0.7
Alternatives per token: 4

============================================================
TOKEN #0
============================================================

Current path tree:
------------------------------------------------------------
The sky is
------------------------------------------------------------

Current text: "The sky is"

Choose next token:
------------------------------------------------------------
  [1] ' falling' (9.72%) █░░░░░░░░░░░░░░░░░░░
  [2] ' the' (14.41%) ██░░░░░░░░░░░░░░░░░░
  [3] ' a' (9.80%) █░░░░░░░░░░░░░░░░░░░
  [4] ' blue' (7.04%) █░░░░░░░░░░░░░░░░░░░
------------------------------------------------------------

Your choice (1-4 or 'done'): 2

============================================================
TOKEN #1
============================================================

Current path tree:
------------------------------------------------------------
The sky is
    └─[2]  the (14.41%)
------------------------------------------------------------

Current text: "The sky is the"

Choose next token:
------------------------------------------------------------
  [1] ' limit' (94.13%) ██████████████████░░
  [2] ' same' (0.62%) ░░░░░░░░░░░░░░░░░░░░
  [3] ' only' (0.36%) ░░░░░░░░░░░░░░░░░░░░
  [4] ' most' (0.31%) ░░░░░░░░░░░░░░░░░░░░
------------------------------------------------------------

Your choice (1-4 or 'done'): 1

============================================================
TOKEN #2
============================================================

Current path tree:
------------------------------------------------------------
The sky is
    └─[2]  the (14.41%)
        └─[1]  limit (94.13%)
------------------------------------------------------------

Your choice (1-4 or 'done'): done

============================================================
         FINAL PATH TREE
============================================================

Current path tree:
------------------------------------------------------------
The sky is
    └─[2]  the (14.41%)
        └─[1]  limit (94.13%)
------------------------------------------------------------

============================================================
         FINAL TEXT
============================================================

The sky is the limit
```

**Reading the tree:**
- Each `└─` shows a choice you made
- `[2]` means you selected option 2
- The token and its probability are shown
- Indentation shows the depth/order of choices

## Command Line Options

```bash
# Basic usage
python interactive_token_selector.py --prompt "Your prompt here"

# Show more alternatives (up to 10)
python interactive_token_selector.py --prompt "Hello" --n-alternatives 10

# Adjust temperature for more/less randomness
python interactive_token_selector.py --prompt "Once upon" --temperature 1.0

# Help
python interactive_token_selector.py --help
```

### Options:

- `--prompt, -p` - Initial text to start with (required)
- `--n-alternatives, -n` - Number of alternatives to show (default: 5)
- `--temperature, -t` - Temperature 0.0-2.0 (default: 0.7)
- `--base-url` - Server URL (default: http://127.0.0.1:8080)

## Understanding the Output

### Probability Bars
```
██████████░░░░░░░░░░  = 50% probability
████░░░░░░░░░░░░░░░░  = 20% probability
█░░░░░░░░░░░░░░░░░░░  = 5% probability
```

Each █ represents ~5% probability.

### Making Choices

- **High probability tokens** (>30%) = What the model "wants" to say
- **Medium probability** (10-30%) = Valid alternatives
- **Low probability** (<10%) = Unusual but possible choices

Choosing low-probability tokens can lead to interesting, unexpected text!

## Tips for Installation Use

### Raspberry Pi Setup

1. Install llama.cpp on Raspberry Pi
2. Copy your GGUF model to the Pi
3. Run the server with a smaller model for better performance
4. Use over SSH or connect keyboard directly

### Artistic Installation Ideas

**Audience Participation:**
- Display options on screen
- Let audience vote/choose (buttons, keypad, etc.)
- Show the evolving text on a display

**Automated Mode:**
- Random selection (modify script to auto-pick)
- Always pick highest probability (deterministic)
- Always pick lowest probability (chaos mode)

**Multiple Paths:**
- Run several instances simultaneously
- Compare different audience choices
- Show diverging narratives

## Customization

The script is intentionally simple (~200 lines) so you can easily modify it:

- Change display format
- Add colors (uncomment colorama imports)
- Save output to file
- Connect to hardware buttons instead of keyboard
- Auto-select based on external input

## Troubleshooting

**"Error: llama.cpp server is not running"**
- Start server: `./start_llamacpp_server.sh`
- Check: `curl http://127.0.0.1:8080/health`

**"Could not get alternatives from server"**
- Server might be busy
- Check server terminal for errors
- Restart server

**Slow response**
- Normal on first request (model loading)
- Subsequent requests should be faster
- Consider smaller model for Raspberry Pi

## Next Steps

- Try different starting prompts
- Experiment with temperature settings
- Build longer texts by choosing more tokens
- Export your creations
- Modify for your installation needs

Enjoy creating! 🎨
