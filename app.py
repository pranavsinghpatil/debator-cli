# app.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import run_debate
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.progress import Progress

def main():
    console = Console()

    console.print(Panel.fit("Debate Simulation", style="bold blue"))

    topic = console.input("Enter topic for debate (default: 'Should AI be regulated like medicine?'): ")
    if not topic:
        topic = "Should AI be regulated like medicine?"

    persona_a = console.input("Enter persona for Agent A (default: 'Scientist'): ")
    if not persona_a:
        persona_a = "Scientist"

    persona_b = console.input("Enter persona for Agent B (default: 'Philosopher'): ")
    if not persona_b:
        persona_b = "Philosopher"

    with Progress() as progress:
        task = progress.add_task("[cyan]Running debate...", total=8)
        def on_round_end(round_num):
            progress.update(task, advance=1)

        summary = run_debate(topic, persona_a, persona_b, on_round_end=on_round_end)

    if summary:
        console.print("\n[bold blue]Judge's Summary[/bold blue]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Winner", style="dim", width=12)
        table.add_column("Rationale")
        table.add_row(summary["winner"], summary["rationale"])
        console.print(table)

if __name__ == "__main__":
    main()
