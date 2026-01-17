#!/usr/bin/env python3
"""
Ollama Token Visualizer 2
Testing verbose output and alternative endpoints for more token information
"""

import requests
import json
import sys
from typing import Iterator, Dict, Any
from colorama import init, Fore, Back, Style

# Initialize colorama for cross-platform colored output
init(autoreset=True)


class OllamaTokenVisualizer2:
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

    def generate_with_options(self, prompt: str, options: Dict[str, Any] = None) -> Iterator[Dict[str, Any]]:
        """
        Stream responses from Ollama API with custom options
        Testing different parameters to see if we can get more token info
        """
        url = f"{self.base_url}/api/generate"

        # Default options to try to get more verbose output
        if options is None:
            options = {}

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": options
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

    def chat_endpoint_test(self, prompt: str) -> Iterator[Dict[str, Any]]:
        """
        Try the /api/chat endpoint instead of /api/generate
        This might expose different information
        """
        url = f"{self.base_url}/api/chat"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "stream": True
        }

        try:
            response = requests.post(url, json=payload, stream=True)
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    yield json.loads(line)
        except requests.exceptions.RequestException as e:
            print(f"{Fore.RED}Error with chat endpoint: {e}")
            sys.exit(1)

    def visualize_detailed(self, prompt: str, use_chat: bool = False):
        """Visualize with detailed analysis of response structure"""
        if not self.verify_model_exists():
            sys.exit(1)

        print(f"\n{Back.BLUE}{Fore.WHITE} EXPERIMENTAL VISUALIZER 2 {Style.RESET_ALL}")
        print(f"{Fore.CYAN}Testing endpoint: {'chat' if use_chat else 'generate'}\n")

        print(f"{Back.BLUE}{Fore.WHITE} PROMPT {Style.RESET_ALL}")
        print(f"{Fore.WHITE}{prompt}\n")

        print(f"{Back.GREEN}{Fore.BLACK} MODEL OUTPUT {Style.RESET_ALL}")
        print(f"{Fore.CYAN}Model: {self.model}\n")

        print(f"{Back.MAGENTA}{Fore.WHITE} TOKENS WITH METADATA {Style.RESET_ALL}")

        full_text = ""
        tokens_list = []
        token_count = 0
        color_index = 0
        metadata_samples = []

        # Choose endpoint
        if use_chat:
            stream_iter = self.chat_endpoint_test(prompt)
        else:
            # Try with verbose options
            options = {
                "temperature": 0.7,
                "top_k": 40,
                "top_p": 0.9,
            }
            stream_iter = self.generate_with_options(prompt, options)

        for chunk in stream_iter:
            # Collect first few chunks for metadata analysis
            if len(metadata_samples) < 3:
                metadata_samples.append(chunk)

            # Extract token (different field for chat vs generate)
            if use_chat:
                token = chunk.get("message", {}).get("content", "")
            else:
                token = chunk.get("response", "")

            if token:
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

                # Show all available fields in the final chunk
                print(f"\n{Back.CYAN}{Fore.BLACK} AVAILABLE FIELDS IN RESPONSE {Style.RESET_ALL}")
                all_fields = set()
                for sample in metadata_samples:
                    all_fields.update(sample.keys())
                for field in sorted(all_fields):
                    print(f"{Fore.CYAN}  - {field}")

                # Show sampling parameters if available
                if "options" in chunk:
                    print(f"\n{Back.CYAN}{Fore.BLACK} SAMPLING PARAMETERS USED {Style.RESET_ALL}")
                    for key, value in chunk["options"].items():
                        print(f"{Fore.CYAN}  {key}: {value}")

                break

        # Display complete text output
        print(f"\n{Back.CYAN}{Fore.BLACK} COMPLETE TEXT {Style.RESET_ALL}")
        print(f"{Fore.WHITE}{full_text}\n")

        # Display sample raw chunks for analysis
        print(f"{Back.YELLOW}{Fore.BLACK} SAMPLE RAW CHUNKS (first 2) {Style.RESET_ALL}")
        for i, sample in enumerate(metadata_samples[:2], 1):
            print(f"{Fore.YELLOW}Chunk {i}:")
            print(f"{Fore.WHITE}{json.dumps(sample, indent=2)}\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Experimental Ollama Token Visualizer - Testing for more metadata",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with generate endpoint
  python ollama_token_visualizer2.py --prompt "Hello!"

  # Test with chat endpoint
  python ollama_token_visualizer2.py --chat --prompt "Hello!"

  # Use different model
  python ollama_token_visualizer2.py --model llama3:latest --prompt "Test"
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
        "--chat",
        action="store_true",
        help="Use /api/chat endpoint instead of /api/generate"
    )

    parser.add_argument(
        "--base-url",
        default="http://localhost:11434",
        help="Ollama API base URL (default: http://localhost:11434)"
    )

    args = parser.parse_args()

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
    visualizer = OllamaTokenVisualizer2(model=args.model, base_url=args.base_url)

    try:
        visualizer.visualize_detailed(prompt, use_chat=args.chat)
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Interrupted by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
