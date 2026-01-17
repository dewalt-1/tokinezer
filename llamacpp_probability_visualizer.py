#!/usr/bin/env python3
"""
LLaMA.cpp Probability Visualizer
Visualizes token probabilities and selection process from llama.cpp server
"""

import requests
import json
import sys
from typing import List, Dict, Any, Tuple
from colorama import init, Fore, Back, Style

# Initialize colorama for cross-platform colored output
init(autoreset=True)


class LlamaCppProbabilityVisualizer:
    def __init__(self, base_url: str = "http://127.0.0.1:8080"):
        self.base_url = base_url
        self.token_colors = [
            Fore.CYAN,
            Fore.GREEN,
            Fore.YELLOW,
            Fore.MAGENTA,
            Fore.BLUE,
            Fore.RED,
        ]

    def check_server(self) -> bool:
        """Check if llama.cpp server is running"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=2)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def generate_with_probs_stream(
        self,
        prompt: str,
        n_probs: int = 5,
        temperature: float = 0.7,
        max_tokens: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Generate text with probability information using streaming

        Args:
            prompt: Input prompt
            n_probs: Number of top probabilities to return per token
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            List of token data with probabilities
        """
        url = f"{self.base_url}/completion"

        payload = {
            "prompt": prompt,
            "n_predict": max_tokens,
            "temperature": temperature,
            "top_k": 40,
            "top_p": 0.9,
            "n_probs": n_probs,  # Key parameter: returns top N token probabilities
            "stream": True,  # MUST use streaming to get probabilities
        }

        try:
            response = requests.post(url, json=payload, stream=True, timeout=120)
            response.raise_for_status()

            tokens_data = []
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data = json.loads(line[6:])  # Strip 'data: ' prefix
                        if 'completion_probabilities' in data:
                            tokens_data.extend(data['completion_probabilities'])

            return tokens_data
        except requests.exceptions.RequestException as e:
            print(f"{Fore.RED}Error communicating with llama.cpp server: {e}")
            sys.exit(1)

    def visualize_probabilities(
        self,
        prompt: str,
        n_probs: int = 5,
        temperature: float = 0.7,
        max_tokens: int = 50,
        show_alternatives: bool = True
    ):
        """Visualize token generation with probabilities"""

        if not self.check_server():
            print(f"{Fore.RED}Error: llama.cpp server is not running")
            print(f"{Fore.YELLOW}Start it with: ./start_llamacpp_server.sh")
            print(f"{Fore.YELLOW}Or manually: llama-server -m ./models/mistral.gguf --port 8080")
            sys.exit(1)

        print(f"\n{Back.BLUE}{Fore.WHITE} LLAMA.CPP PROBABILITY VISUALIZER {Style.RESET_ALL}")
        print(f"{Fore.CYAN}Server: {self.base_url}\n")

        print(f"{Back.BLUE}{Fore.WHITE} PROMPT {Style.RESET_ALL}")
        print(f"{Fore.WHITE}{prompt}\n")

        print(f"{Fore.CYAN}Generating with temperature={temperature}, showing top {n_probs} probabilities per token...\n")

        # Generate text with probabilities (using streaming)
        completion_probs = self.generate_with_probs_stream(prompt, n_probs, temperature, max_tokens)

        if not completion_probs:
            print(f"{Fore.YELLOW}Warning: No probability data returned.")
            return

        print(f"{Back.MAGENTA}{Fore.WHITE} TOKEN GENERATION WITH PROBABILITIES {Style.RESET_ALL}\n")

        # Reconstruct complete text
        content = ""

        # Visualize each token with its alternatives
        for idx, token_data in enumerate(completion_probs):
            # Extract token and probabilities
            selected_token = token_data.get("token", "")
            selected_logprob = token_data.get("logprob", 0.0)
            selected_prob = 2.71828 ** selected_logprob  # Convert logprob to prob

            content += selected_token

            top_logprobs = token_data.get("top_logprobs", [])

            # Color for this token
            color = self.token_colors[idx % len(self.token_colors)]

            # Display selected token with its probability
            print(f"{color}[{idx}] {Fore.WHITE}'{selected_token}'{color} (p={selected_prob:.4f}){Style.RESET_ALL}")

            # Show alternatives if requested
            if show_alternatives and top_logprobs:
                print(f"  {Fore.CYAN}Alternatives:")
                for alt_idx, alt in enumerate(top_logprobs[:n_probs], 1):
                    alt_token = alt.get("token", "")
                    alt_logprob = alt.get("logprob", 0.0)
                    alt_prob = 2.71828 ** alt_logprob

                    # Visual probability bar
                    bar_length = int(alt_prob * 20)
                    bar = "█" * bar_length + "░" * (20 - bar_length)

                    print(f"    {Fore.YELLOW}{alt_idx}. '{alt_token}' {Fore.CYAN}(p={alt_prob:.4f}) {Fore.WHITE}{bar}")
                print()

        # Display statistics
        print(f"\n{Back.YELLOW}{Fore.BLACK} STATISTICS {Style.RESET_ALL}")
        print(f"{Fore.GREEN}Tokens Generated: {len(completion_probs)}")

        # Display complete text
        print(f"\n{Back.CYAN}{Fore.BLACK} COMPLETE TEXT {Style.RESET_ALL}")
        print(f"{Fore.WHITE}{content}\n")

    def visualize_decision_tree(
        self,
        prompt: str,
        n_probs: int = 3,
        temperature: float = 0.7,
        max_tokens: int = 10
    ):
        """
        Visualize token selection as a decision tree
        Shows what the model considered at each step
        """

        if not self.check_server():
            print(f"{Fore.RED}Error: llama.cpp server is not running")
            sys.exit(1)

        print(f"\n{Back.BLUE}{Fore.WHITE} TOKEN SELECTION TREE {Style.RESET_ALL}\n")
        print(f"{Fore.CYAN}Prompt: {Fore.WHITE}{prompt}\n")

        completion_probs = self.generate_with_probs_stream(prompt, n_probs, temperature, max_tokens)

        if not completion_probs:
            print(f"{Fore.YELLOW}No probability data available")
            return

        print(f"{Fore.CYAN}Decision tree (showing top {n_probs} choices at each step):\n")

        cumulative_text = ""
        for idx, token_data in enumerate(completion_probs):
            # Extract token and probabilities
            selected_token = token_data.get("token", "")
            selected_logprob = token_data.get("logprob", 0.0)
            selected_prob = 2.71828 ** selected_logprob

            cumulative_text += selected_token
            top_logprobs = token_data.get("top_logprobs", [])

            # Indent based on depth
            indent = "  " * idx

            # Show the choice
            print(f"{indent}{Fore.GREEN}→ [{selected_prob:.2%}] '{selected_token}' {Fore.CYAN}(chosen)")

            # Show alternatives
            for alt in top_logprobs[:n_probs]:
                alt_token = alt.get("token", "")
                alt_logprob = alt.get("logprob", 0.0)
                alt_prob = 2.71828 ** alt_logprob
                print(f"{indent}  {Fore.YELLOW}  [{alt_prob:.2%}] '{alt_token}'")

            print()

        print(f"{Fore.WHITE}Final text: {cumulative_text}\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Visualize token probabilities from llama.cpp",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic probability visualization
  python llamacpp_probability_visualizer.py --prompt "Hello, my name is"

  # Show more alternatives per token
  python llamacpp_probability_visualizer.py --prompt "The sky is" --n-probs 10

  # Decision tree view
  python llamacpp_probability_visualizer.py --prompt "Once upon a time" --tree

  # Adjust temperature for more/less randomness
  python llamacpp_probability_visualizer.py --prompt "AI is" --temperature 1.0

Note: Make sure llama.cpp server is running first!
  ./start_llamacpp_server.sh
        """
    )

    parser.add_argument(
        "--prompt", "-p",
        required=True,
        help="Prompt to send to the model"
    )

    parser.add_argument(
        "--n-probs", "-n",
        type=int,
        default=5,
        help="Number of top probabilities to show per token (default: 5)"
    )

    parser.add_argument(
        "--temperature", "-t",
        type=float,
        default=0.7,
        help="Sampling temperature (default: 0.7)"
    )

    parser.add_argument(
        "--max-tokens", "-m",
        type=int,
        default=50,
        help="Maximum tokens to generate (default: 50)"
    )

    parser.add_argument(
        "--tree",
        action="store_true",
        help="Show decision tree view (limits to 10 tokens)"
    )

    parser.add_argument(
        "--no-alternatives",
        action="store_true",
        help="Don't show alternative tokens, only the selected ones"
    )

    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8080",
        help="llama.cpp server URL (default: http://127.0.0.1:8080)"
    )

    args = parser.parse_args()

    visualizer = LlamaCppProbabilityVisualizer(base_url=args.base_url)

    try:
        if args.tree:
            visualizer.visualize_decision_tree(
                args.prompt,
                n_probs=args.n_probs,
                temperature=args.temperature,
                max_tokens=10  # Limit for tree view
            )
        else:
            visualizer.visualize_probabilities(
                args.prompt,
                n_probs=args.n_probs,
                temperature=args.temperature,
                max_tokens=args.max_tokens,
                show_alternatives=not args.no_alternatives
            )
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Interrupted by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
