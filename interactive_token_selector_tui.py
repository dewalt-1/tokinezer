#!/usr/bin/env python3
"""
Interactive Token Selector with Rich TUI
Beautiful, fluid interface for token-by-token text building
"""

import requests
import json
import sys
from typing import List, Dict, Any
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.tree import Tree
from rich.table import Table
from rich.layout import Layout
from rich.text import Text
from rich.prompt import Prompt
from rich import box


class InteractiveTokenSelectorTUI:
    def __init__(self, base_url: str = "http://127.0.0.1:8080"):
        self.base_url = base_url
        self.console = Console()

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
            self.console.print(f"[red]Error: {e}[/red]")
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

    def _make_prob_bar(self, prob: float, width: int = 20) -> str:
        """Create a visual probability bar"""
        filled = int(prob * width)
        bar = "█" * filled + "░" * (width - filled)
        return bar

    def _build_horizontal_tree(self, initial_prompt: str, history: List[Dict]) -> str:
        """Build a true horizontal tree (grows left to right)"""
        if not history:
            return initial_prompt

        # Build tree structure as a 2D grid
        lines = []
        self._render_sideways_tree(lines, history, 0, 0)

        return "\n".join(lines)

    def _render_sideways_tree(self, lines: List[str], history: List[Dict], depth: int, row_offset: int):
        """Recursively render tree growing left-to-right"""
        if depth >= len(history):
            return row_offset

        step = history[depth]
        all_alts = step['all_alternatives']
        selected_idx = step['selected_idx']

        # Calculate vertical spacing for alternatives
        num_alts = len(all_alts)
        current_row = row_offset

        for idx, alt in enumerate(all_alts):
            is_chosen = (idx == selected_idx)
            token = alt['token']
            prob = alt['prob']
            prob_bar = self._make_prob_bar(prob, width=8)

            # Ensure we have enough lines
            while len(lines) <= current_row:
                lines.append("")

            # Calculate column position (grows to the right)
            col = depth * 30  # Each level is 30 chars wide

            # Pad the line to the right column
            line = lines[current_row]
            if len(line) < col:
                line += " " * (col - len(line))

            # Build the node content
            if is_chosen:
                if depth < len(history) - 1:
                    marker = "[green]✓[/green]"
                else:
                    marker = "[green]✓ CHO[/green]"
                node = f"─{marker}[{idx+1}]'{token}' {prob_bar}"
            else:
                node = f"─[dim][{idx+1}]'{token}' {prob_bar}[/dim]"

            # Add connector from parent
            if depth > 0:
                connector = "├─"
                if idx == len(all_alts) - 1:
                    connector = "└─"
                node = connector + node
            else:
                node = "──" + node

            # Update the line
            lines[current_row] = line[:col] + node

            # If chosen, continue growing to the right
            if is_chosen and depth < len(history) - 1:
                # Draw vertical line continuation for chosen path
                if idx < len(all_alts) - 1:
                    # Not the last item, need vertical continuation
                    for vert_row in range(current_row + 1, current_row + 3):
                        if vert_row < len(lines):
                            vert_line = lines[vert_row]
                            if len(vert_line) < col:
                                vert_line += " " * (col - len(vert_line))
                            if len(vert_line) >= col:
                                vert_line = vert_line[:col] + "│" + vert_line[col+1:]
                            lines[vert_row] = vert_line

                current_row = self._render_sideways_tree(lines, history, depth + 1, current_row)
            else:
                current_row += 2  # Space between alternatives

        return current_row

    def _build_choices_table(self, alternatives: List[Dict]) -> Table:
        """Build a table showing token choices"""
        table = Table(show_header=False, box=box.SIMPLE, padding=(0, 1))
        table.add_column("Choice", style="bold yellow", width=5)
        table.add_column("Token", style="white")
        table.add_column("Probability", style="cyan")
        table.add_column("Bar", style="white")

        for idx, alt in enumerate(alternatives, 1):
            token = alt['token']
            prob = alt['prob']
            prob_bar = self._make_prob_bar(prob, width=20)

            table.add_row(
                f"[{idx}]",
                f"'{token}'",
                f"({prob:.2%})",
                prob_bar
            )

        return table

    def _build_layout(
        self,
        initial_prompt: str,
        history: List[Dict],
        current_text: str,
        alternatives: List[Dict],
        token_count: int
    ) -> Layout:
        """Build the complete TUI layout"""
        from rich.console import Group

        layout = Layout()

        # Split into header, main, and footer
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=8)
        )

        # Header
        header_text = Text.from_markup(
            f"[bold cyan]TOKEN TREE BUILDER[/bold cyan] | Token #{token_count}",
            justify="center"
        )
        layout["header"].update(Panel(header_text, style="bold cyan"))

        # Main area - split into tree and current text
        layout["main"].split_column(
            Layout(name="tree", ratio=2),
            Layout(name="current", size=5)
        )

        # Tree view with scrollable content
        if history:
            # Start with initial prompt
            tree_lines = [f"[bold cyan]{initial_prompt}[/bold cyan]"]
            # Add horizontal tree
            tree_content = self._build_horizontal_tree(initial_prompt, history)
            tree_lines.append(tree_content)

            tree_display = "\n".join(tree_lines)
            layout["tree"].update(Panel(
                tree_display,
                title="[bold]Decision Tree (Scrollable)[/bold]",
                border_style="cyan"
            ))
        else:
            layout["tree"].update(Panel(
                f"[bold cyan]{initial_prompt}[/bold cyan]",
                title="[bold]Decision Tree[/bold]",
                border_style="cyan"
            ))

        # Current text
        current_panel = Panel(
            f"[bold white]{current_text}[/bold white]",
            title="[bold]Current Text[/bold]",
            border_style="green"
        )
        layout["current"].update(current_panel)

        # Footer - token choices
        choices_table = self._build_choices_table(alternatives)
        footer_panel = Panel(
            choices_table,
            title="[bold]Choose Next Token[/bold]",
            subtitle="[dim]Enter number (1-{}) or 'done'[/dim]".format(len(alternatives)),
            border_style="yellow"
        )
        layout["footer"].update(footer_panel)

        return layout

    def run_interactive_session(
        self,
        initial_prompt: str,
        n_alternatives: int = 5,
        temperature: float = 0.7
    ):
        """Run the interactive token selection session with Rich TUI"""

        # Check server
        if not self.check_server():
            self.console.print("[red]Error: llama.cpp server is not running[/red]")
            self.console.print("[yellow]Start it with: ./start_llamacpp_server.sh[/yellow]")
            sys.exit(1)

        self.console.clear()
        self.console.print("[bold cyan]╔══════════════════════════════════════════════════════╗[/bold cyan]")
        self.console.print("[bold cyan]║     INTERACTIVE TOKEN TREE SELECTOR (TUI)           ║[/bold cyan]")
        self.console.print("[bold cyan]╚══════════════════════════════════════════════════════╝[/bold cyan]")
        self.console.print(f"\n[cyan]Initial prompt:[/cyan] [white]{initial_prompt}[/white]")
        self.console.print(f"[cyan]Temperature:[/cyan] {temperature}")
        self.console.print(f"[cyan]Alternatives:[/cyan] {n_alternatives}\n")
        self.console.input("[dim]Press Enter to begin...[/dim]")

        # Initialize state
        current_text = initial_prompt
        token_count = 0
        history = []

        while True:
            # Get alternatives for next token
            alternatives = self.get_next_token_alternatives(
                current_text,
                n_alternatives,
                temperature
            )

            if not alternatives:
                self.console.print("[red]Error: Could not get alternatives from server[/red]")
                break

            # Build and display the layout
            layout = self._build_layout(
                initial_prompt,
                history,
                current_text,
                alternatives,
                token_count
            )

            self.console.clear()
            self.console.print(layout)

            # Get user choice
            while True:
                choice = Prompt.ask(
                    "\n[bold yellow]Your choice[/bold yellow]",
                    default="done"
                ).strip().lower()

                if choice == 'done':
                    break

                try:
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(alternatives):
                        break
                    else:
                        self.console.print(f"[red]Please enter 1-{len(alternatives)} or 'done'[/red]")
                except ValueError:
                    self.console.print(f"[red]Please enter 1-{len(alternatives)} or 'done'[/red]")

            if choice == 'done':
                break

            # Add selected token to text
            selected_idx = int(choice) - 1
            selected_token = alternatives[selected_idx]["token"]
            selected_prob = alternatives[selected_idx]["prob"]

            # Track this step in history
            history.append({
                "all_alternatives": alternatives,
                "selected_idx": selected_idx
            })

            current_text += selected_token
            token_count += 1

        # Show final result
        self.console.clear()
        self.console.print("\n[bold cyan]═══════════════════════════════════════════════════════[/bold cyan]")
        self.console.print("[bold cyan]                 FINAL RESULT                          [/bold cyan]")
        self.console.print("[bold cyan]═══════════════════════════════════════════════════════[/bold cyan]\n")

        # Final tree
        if history:
            tree_lines = [f"[bold cyan]{initial_prompt}[/bold cyan]"]
            tree_content = self._build_horizontal_tree(initial_prompt, history)
            tree_lines.append(tree_content)
            tree_display = "\n".join(tree_lines)

            self.console.print(Panel(
                tree_display,
                title="[bold]Final Decision Tree[/bold]",
                border_style="cyan"
            ))

        # Final text
        self.console.print(Panel(
            f"[bold white]{current_text}[/bold white]",
            title="[bold]Final Text[/bold]",
            border_style="green"
        ))
        self.console.print()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Interactively select tokens with beautiful TUI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python interactive_token_selector_tui.py --prompt "The sky is"
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

    selector = InteractiveTokenSelectorTUI(base_url=args.base_url)

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
