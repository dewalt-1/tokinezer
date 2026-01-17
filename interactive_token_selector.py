#!/usr/bin/env python3
"""
Interactive Token Selector
Simple tool to manually select tokens and build text step by step
"""

import requests
import json
import sys
from typing import List, Dict, Any


class InteractiveTokenSelector:
    def __init__(self, base_url: str = "http://127.0.0.1:8080"):
        self.base_url = base_url

    def check_server(self) -> bool:
        """Check if llama.cpp server is running"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=2)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def get_next_token_alternatives(
        self,
        prompt: str,
        n_alternatives: int = 5,
        temperature: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Get alternative tokens for the next position
        Returns list of alternatives with tokens and probabilities
        """
        url = f"{self.base_url}/completion"

        payload = {
            "prompt": prompt,
            "n_predict": 1,  # Only generate 1 token
            "temperature": temperature,
            "top_k": 40,
            "top_p": 0.9,
            "n_probs": n_alternatives,
            "stream": True,
        }

        try:
            response = requests.post(url, json=payload, stream=True, timeout=30)
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data = json.loads(line[6:])
                        if 'completion_probabilities' in data:
                            # Get the first (and only) token's alternatives
                            token_data = data['completion_probabilities'][0]
                            return self._extract_alternatives(token_data, n_alternatives)

            return []
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            return []

    def _extract_alternatives(self, token_data: Dict, n_alternatives: int) -> List[Dict]:
        """Extract and format alternative tokens"""
        alternatives = []

        # Get the selected token (first in top_logprobs)
        selected_token = token_data.get("token", "")
        selected_logprob = token_data.get("logprob", 0.0)
        selected_prob = 2.71828 ** selected_logprob

        alternatives.append({
            "token": selected_token,
            "prob": selected_prob
        })

        # Get other alternatives
        top_logprobs = token_data.get("top_logprobs", [])
        for alt in top_logprobs[:n_alternatives]:
            alt_token = alt.get("token", "")
            alt_logprob = alt.get("logprob", 0.0)
            alt_prob = 2.71828 ** alt_logprob

            # Avoid duplicates
            if alt_token != selected_token:
                alternatives.append({
                    "token": alt_token,
                    "prob": alt_prob
                })

        return alternatives[:n_alternatives]

    def display_path_tree(self, initial_prompt: str, selected_tokens: List[Dict]):
        """Display the path tree of selected tokens"""
        print("\nCurrent path tree:")
        print("-" * 60)
        print(initial_prompt)

        for i, token_info in enumerate(selected_tokens):
            # Indentation based on depth
            indent = "    " * (i + 1)

            # Branch character (always use └─ for simplicity)
            branch = "└─"

            # Display token
            print(f"{indent}{branch}[{token_info['choice_num']}] {token_info['token']} ({token_info['prob']:.2%})")

        print("-" * 60)

    def display_alternatives(self, alternatives: List[Dict], current_text: str):
        """Display alternatives in a simple numbered list"""
        print(f"\nCurrent text: \"{current_text}\"")
        print("\nChoose next token:")
        print("-" * 60)

        for idx, alt in enumerate(alternatives, 1):
            token = alt["token"]
            prob = alt["prob"]

            # Create probability bar
            bar_length = int(prob * 20)
            bar = "█" * bar_length + "░" * (20 - bar_length)

            # Display option
            print(f"  [{idx}] '{token}' ({prob:.2%}) {bar}")

        print("-" * 60)

    def get_user_choice(self, num_alternatives: int) -> str:
        """Get user's choice"""
        while True:
            choice = input(f"\nYour choice (1-{num_alternatives} or 'done'): ").strip().lower()

            if choice == 'done':
                return 'done'

            try:
                choice_num = int(choice)
                if 1 <= choice_num <= num_alternatives:
                    return str(choice_num)
                else:
                    print(f"Please enter a number between 1 and {num_alternatives}, or 'done'")
            except ValueError:
                print(f"Please enter a number between 1 and {num_alternatives}, or 'done'")

    def run_interactive_session(
        self,
        initial_prompt: str,
        n_alternatives: int = 5,
        temperature: float = 0.7
    ):
        """Run the interactive token selection session"""

        # Check server
        if not self.check_server():
            print("Error: llama.cpp server is not running")
            print("Start it with: ./start_llamacpp_server.sh")
            sys.exit(1)

        print("=" * 60)
        print("         INTERACTIVE TOKEN TREE SELECTOR")
        print("=" * 60)
        print(f"\nInitial prompt: \"{initial_prompt}\"")
        print(f"Temperature: {temperature}")
        print(f"Alternatives per token: {n_alternatives}")

        # Start with initial prompt
        current_text = initial_prompt
        token_count = 0
        selected_tokens = []  # Track selected tokens for tree display

        while True:
            print(f"\n{'=' * 60}")
            print(f"TOKEN #{token_count}")
            print('=' * 60)

            # Display current path tree
            self.display_path_tree(initial_prompt, selected_tokens)

            # Get alternatives for next token
            alternatives = self.get_next_token_alternatives(
                current_text,
                n_alternatives,
                temperature
            )

            if not alternatives:
                print("Error: Could not get alternatives from server")
                break

            # Display alternatives
            self.display_alternatives(alternatives, current_text)

            # Get user choice
            choice = self.get_user_choice(len(alternatives))

            if choice == 'done':
                break

            # Add selected token to text
            selected_idx = int(choice) - 1
            selected_token = alternatives[selected_idx]["token"]
            selected_prob = alternatives[selected_idx]["prob"]

            # Track this selection
            selected_tokens.append({
                "token": selected_token,
                "prob": selected_prob,
                "choice_num": selected_idx + 1
            })

            current_text += selected_token
            token_count += 1

        # Show final result with tree
        print("\n" + "=" * 60)
        print("         FINAL PATH TREE")
        print("=" * 60)
        self.display_path_tree(initial_prompt, selected_tokens)

        print("\n" + "=" * 60)
        print("         FINAL TEXT")
        print("=" * 60)
        print(f"\n{current_text}\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Interactively select tokens to build text",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python interactive_token_selector.py --prompt "The sky is"
        """
    )

    parser.add_argument(
        "--prompt", "-p",
        required=True,
        help="Initial prompt to start with"
    )

    parser.add_argument(
        "--n-alternatives", "-n",
        type=int,
        default=5,
        help="Number of alternatives to show (default: 5)"
    )

    parser.add_argument(
        "--temperature", "-t",
        type=float,
        default=0.7,
        help="Sampling temperature (default: 0.7)"
    )

    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8080",
        help="llama.cpp server URL (default: http://127.0.0.1:8080)"
    )

    args = parser.parse_args()

    selector = InteractiveTokenSelector(base_url=args.base_url)

    try:
        selector.run_interactive_session(
            args.prompt,
            args.n_alternatives,
            args.temperature
        )
    except KeyboardInterrupt:
        print("\n\nSession interrupted by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
