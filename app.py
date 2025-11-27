# app.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.runner import run_debate
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.progress import Progress
from rich.rule import Rule

def main():
    console = Console()
    # Create a big, centered title with decorative elements
    console.print(Rule("🎭", style="blue"), justify="center")
    title = Text("  DEBATE SIMULATION  ", style="bold blue", justify="center")
    console.print(title, justify="center")
    console.print(Rule("🎭", style="blue"), justify="center")
    console.print()  

    # Get debate parameters
    topic = console.input("Enter topic for debate (default: 'Should AI be regulated like medicine?'): ")
    if not topic:
        topic = "Should AI be regulated like medicine?"

    persona_a = console.input("Enter persona for Agent A (default: 'Scientist'): ")
    if not persona_a:
        persona_a = "Scientist"

    persona_b = console.input("Enter persona for Agent B (default: 'Philosopher'): ")
    if not persona_b:
        persona_b = "Philosopher"

    # Clear screen and show agents matchup title
    console.clear()
    console.print()
    # console.print(Rule("🎭", style="blue"), justify="center")
    # title = Text("  DEBATE SIMULATION  ", style="bold blue", justify="center")
    # console.print(title, justify="center")
    # console.print(Rule("🎭", style="blue"), justify="center")
    
    # Show agents matchup
    matchup_title = Text(f"{persona_a} Vs {persona_b}", style="bold cyan", justify="center")
    console.print(matchup_title, justify="center")
    console.print(Rule("", style="cyan"), justify="center")
    console.print()

    # Create records folder
    records_dir = "records"
    if not os.path.exists(records_dir):
        os.makedirs(records_dir)

    # Sanitize topic for folder name
    sanitized_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '_')).rstrip()
    debate_dir = os.path.join(records_dir, sanitized_topic)
    if not os.path.exists(debate_dir):
        os.makedirs(debate_dir)

    summary = run_debate(topic, persona_a, persona_b, debate_dir)

    if summary and "winner" in summary:
        table = Table(show_header=True, header_style="bold magenta", border_style="magenta")
        table.add_column("Winner", style="dim", width=20)
        table.add_column("Rationale")
        
        # Extract agent identifier from winner string (e.g., "Scientist (AgentA)" -> "AgentA")
        winner = summary["winner"]
        winner_agent = None
        if winner and '(' in winner and ')' in winner:
            winner_agent = winner.split('(')[1].split(')')[0]
        elif winner in ['AgentA', 'AgentB']:
            winner_agent = winner
        
        if winner_agent == "AgentA":
            winner_display = f"[bold green]{summary['persona_a']} (AgentA)[/bold green]"
        elif winner_agent == "AgentB":
            winner_display = f"[bold yellow]{summary['persona_b']} (AgentB)[/bold yellow]"
        else:
            winner_display = "[bold blue]Tie[/bold blue]"

        table.add_row(winner_display, summary["rationale"])
        console.print(Panel(table, title="[bold magenta]Judge's Summary[/bold magenta]", border_style="magenta"))
    elif summary:
        console.print(Panel.fit("[bold red]Debate concluded without a clear winner or due to an error.[/bold red]", style="bold red"))

  

if __name__ == "__main__":
    main()
