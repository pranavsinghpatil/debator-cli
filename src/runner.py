# src/runner.py
import sys
import os
# Ensure src is in path if run directly, though usually run via app.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Use relative imports since this is inside the src package
try:
    from .logger_util import log_event, set_log_file
    from .dag_gen import generate_debate_artifacts
    from .langgraph_debate import run_langgraph_debate, generate_langgraph_dag
    from .state import DebateState
    from .nodes import ValidationError
except ImportError:
    # Fallback for direct execution
    from logger_util import log_event, set_log_file
    from dag_gen import generate_debate_artifacts
    from langgraph_debate import run_langgraph_debate, generate_langgraph_dag
    from state import DebateState
    from nodes import ValidationError

from rich.rule import Rule
from rich.panel import Panel
from rich.console import Console
from IPython.display import Image

def run_debate(topic, persona_a="Scientist", persona_b="Philosopher", debate_dir="."):
    set_log_file(os.path.join(debate_dir, "debate_log.txt"))
    console = Console()
    console.print(f"Starting debate between [bold green]{persona_a}[/bold green] (AgentA) and [bold yellow]{persona_b}[/bold yellow] (AgentB)...")
    console.print("[dim]Initializing debate system...[/dim]")
    log_event("debate_started", {"topic": topic, "persona_a": persona_a, "persona_b": persona_b})

    # Run the complete LangGraph debate with progressive display
    console.print("[dim]Beginning debate rounds...[/dim]\n")
    final_state = run_langgraph_debate(topic, persona_a, persona_b, console=console)
    
    if final_state:
        # Check for errors
        if final_state.get("error"):
            console.print(f"[bold red]Error during debate: {final_state['error']}[/bold red]")
        
        # Generate summary
        summary = {
            "winner": final_state.get("winner"),
            "rationale": final_state.get("rationale"),
            "persona_a": final_state.get("persona_a"),
            "persona_b": final_state.get("persona_b")
        }
        
        # Generate LangGraph DAG diagram using built-in methods
        dag_mermaid = generate_langgraph_dag()
        dag_mmd_path = os.path.join(debate_dir, "langgraph_dag.mmd")
        with open(dag_mmd_path, "w", encoding="utf-8") as f:
            f.write(dag_mermaid)
        console.print(f"[green]LangGraph DAG diagram saved: {dag_mmd_path}[/green]")
        
        # Also try to generate PNG if mermaid-cli is available (skip silently if it fails)
        try:
            from mermaid_cli import render_mermaid
            import asyncio
            import threading
            
            def render_in_thread():
                """Render PNG in a separate thread to avoid event loop conflicts"""
                try:
                    # Create new event loop for this thread
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    
                    async def render_dag():
                        _, _, png_data = await render_mermaid(
                            definition=dag_mermaid,
                            output_format="png",
                            mermaid_config={"scale": 2}
                        )
                        png_path = os.path.join(debate_dir, "langgraph_dag.png")
                        with open(png_path, "wb") as f:
                            f.write(png_data)
                        console.print(f"[green]LangGraph DAG PNG saved: {png_path}[/green]")
                    
                    new_loop.run_until_complete(render_dag())
                    new_loop.close()
                except Exception:
                    pass  # Silently fail
            
            # Run in separate thread to avoid event loop conflicts
            thread = threading.Thread(target=render_in_thread, daemon=True)
            thread.start()
            thread.join(timeout=10)  # Wait max 10 seconds
            
        except Exception:
            # Silently skip PNG generation if it fails
            pass
        
        # Generate debate artifacts
        generate_debate_artifacts(final_state, os.path.join(debate_dir, "debate_dag"))
        
        return summary
    return None
