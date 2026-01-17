#!/usr/bin/env python3
"""
Ollama Token Visualizer
Displays both tokens and text output from Ollama models in real-time
"""

import requests
import json
import sys
from typing import Iterator, Dict, Any
from colorama import init, Fore, Back, Style

# Initialize colorama for cross-platform colored output
init(autoreset=True)


class OllamaTokenVisualizer:
    def __init__(self, model: str = "mistral:latest", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.token_colors = [
            Fore.CYAN,
            Fore.GREEN,
            Fore.YELLOW,
            Fore.MAGENTA,
            Fore.BLUE,
            Fore.RED,
        ]

    def verify_model_exists(self) -> bool:
        """Check if the specified model exists"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]

            if self.model not in model_names:
                print(f"{Fore.RED}Error: Model '{self.model}' not found")
                print(f"{Fore.CYAN}Available models:")
                for name in model_names:
                    print(f"  - {name}")
                return False
            return True
        except requests.exceptions.RequestException as e:
            print(f"{Fore.RED}Error connecting to Ollama: {e}")
            print(f"{Fore.YELLOW}Make sure Ollama is running")
            return False

    def generate_stream(self, prompt: str) -> Iterator[Dict[str, Any]]:
        """Stream responses from Ollama API"""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True
        }

        try:
            response = requests.post(url, json=payload, stream=True)
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    yield json.loads(line)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"{Fore.RED}Error: Model '{self.model}' not found")
                print(f"{Fore.YELLOW}Use --list-models to see available models")
            else:
                print(f"{Fore.RED}HTTP Error: {e}")
            sys.exit(1)
        except requests.exceptions.RequestException as e:
            print(f"{Fore.RED}Error connecting to Ollama: {e}")
            print(f"{Fore.YELLOW}Make sure Ollama is running")
            sys.exit(1)

    def visualize(self, prompt: str):
        """Visualize tokens and text output"""
        # Verify model exists first
        if not self.verify_model_exists():
            sys.exit(1)

        print(f"\n{Back.BLUE}{Fore.WHITE} PROMPT {Style.RESET_ALL}")
        print(f"{Fore.WHITE}{prompt}\n")

        print(f"{Back.GREEN}{Fore.BLACK} MODEL OUTPUT {Style.RESET_ALL}")
        print(f"{Fore.CYAN}Model: {self.model}\n")

        # Token visualization section
        print(f"{Back.MAGENTA}{Fore.WHITE} TOKENS WITH NUMBERS {Style.RESET_ALL}")

        full_text = ""
        tokens_list = []
        token_count = 0
        color_index = 0

        for chunk in self.generate_stream(prompt):
            if "response" in chunk:
                token = chunk["response"]
                full_text += token
                tokens_list.append(token)

                # Display token with number and alternating colors
                color = self.token_colors[color_index % len(self.token_colors)]
                print(f"{color}[{token_count}:{token}]{Style.RESET_ALL}", end="", flush=True)

                token_count += 1
                color_index += 1

            if chunk.get("done", False):
                # Display final statistics
                print(f"\n\n{Back.YELLOW}{Fore.BLACK} STATISTICS {Style.RESET_ALL}")

                if "total_duration" in chunk:
                    duration_s = chunk["total_duration"] / 1e9
                    print(f"{Fore.GREEN}Total Duration: {duration_s:.2f}s")

                if "eval_count" in chunk:
                    print(f"{Fore.GREEN}Tokens Generated: {chunk['eval_count']}")

                if "eval_duration" in chunk and "eval_count" in chunk:
                    tokens_per_sec = chunk["eval_count"] / (chunk["eval_duration"] / 1e9)
                    print(f"{Fore.GREEN}Tokens/Second: {tokens_per_sec:.2f}")

                break

        # Display complete text output
        print(f"\n{Back.CYAN}{Fore.BLACK} COMPLETE TEXT {Style.RESET_ALL}")
        print(f"{Fore.WHITE}{full_text}\n")


def list_available_models(base_url: str = "http://localhost:11434"):
    """List all available Ollama models"""
    try:
        response = requests.get(f"{base_url}/api/tags")
        response.raise_for_status()
        models = response.json().get("models", [])

        if not models:
            print(f"{Fore.YELLOW}No models found. Pull a model with: ollama pull llama2")
            return []

        print(f"\n{Back.GREEN}{Fore.BLACK} AVAILABLE MODELS {Style.RESET_ALL}")
        for idx, model in enumerate(models, 1):
            print(f"{Fore.CYAN}{idx}. {model['name']}")

        return [model['name'] for model in models]
    except requests.exceptions.RequestException as e:
        print(f"{Fore.RED}Error connecting to Ollama: {e}")
        print(f"{Fore.YELLOW}Make sure Ollama is running with: ollama serve")
        return []


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Visualize tokens from Ollama LLM output",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python ollama_token_visualizer.py

  # Direct prompt
  python ollama_token_visualizer.py --prompt "Explain quantum computing in simple terms"

  # Specific model
  python ollama_token_visualizer.py --model llama2 --prompt "Hello, world!"

  # List available models
  python ollama_token_visualizer.py --list-models
        """
    )

    parser.add_argument(
        "--model", "-m",
        default="mistral:latest",
        help="Ollama model to use (default: mistral:latest)"
    )

    parser.add_argument(
        "--prompt", "-p",
        help="Prompt to send to the model"
    )

    parser.add_argument(
        "--base-url",
        default="http://localhost:11434",
        help="Ollama API base URL (default: http://localhost:11434)"
    )

    parser.add_argument(
        "--list-models", "-l",
        action="store_true",
        help="List all available models and exit"
    )

    args = parser.parse_args()

    # List models if requested
    if args.list_models:
        list_available_models(args.base_url)
        return

    # Get prompt from args or interactively
    prompt = args.prompt
    if not prompt:
        print(f"{Fore.CYAN}Enter your prompt (Ctrl+C to exit):")
        try:
            prompt = input(f"{Fore.GREEN}> {Style.RESET_ALL}")
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Exiting...")
            sys.exit(0)

    if not prompt.strip():
        print(f"{Fore.RED}Error: Empty prompt")
        sys.exit(1)

    # Create visualizer and run
    visualizer = OllamaTokenVisualizer(model=args.model, base_url=args.base_url)

    try:
        visualizer.visualize(prompt)
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Interrupted by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
