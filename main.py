# main.py
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
from logger_util import log_event, set_log_file
from dag_gen import generate_debate_artifacts
from rich.rule import Rule
from rich.panel import Panel
from rich.console import Console
from langgraph_debate import create_debate_graph
from state import DebateState
from nodes import ValidationError
from IPython.display import Image

def run_debate(topic, persona_a="Scientist", persona_b="Philosopher", debate_dir="."):
    set_log_file(os.path.join(debate_dir, "debate_log.txt"))
    console = Console()
    console.print(f"Starting debate between [bold green]{persona_a}[/bold green] (AgentA) and [bold yellow]{persona_b}[/bold yellow] (AgentB)...")
    log_event("debate_started", {"topic": topic, "persona_a": persona_a, "persona_b": persona_b})

    # Initialize LangGraph
    graph = create_debate_graph()
    initial_state = DebateState(
        topic=topic,
        persona_a=persona_a,
        persona_b=persona_b,
        round=0,
        transcript=[],
        seen_texts=[],
        current_agent="AgentA",
        winner=None,
        rationale=None,
        error=None,
        last_speaker=None,
        last_text=None
    )

    final_state = None
    current_full_state = initial_state.copy()
    
    # Stream through the graph and merge state updates
    try:
        for node_output in graph.stream(initial_state):
            # node_output is a dict like {"node_name": {partial_state_updates}}
            for node_name, partial_state in node_output.items():
                # Merge partial state updates into full state (preserving existing fields)
                if partial_state:
                    current_full_state = {**current_full_state, **partial_state}
                final_state = current_full_state.copy()
                
                # Print current round's output if it's an agent node
                if node_name in ["agent_a", "agent_b"] and final_state.get("round", 0) > 0:
                    if final_state.get("transcript"):
                        current_round = final_state["round"]
                        last_entry = final_state["transcript"][-1]
                        last_speaker = last_entry["agent"]
                        last_text = last_entry["text"]
                        persona = last_entry["persona"]
                        color = "green" if last_speaker == "AgentA" else "yellow"
                        console.print(Rule(f"Round {current_round}", style="bold blue"))
                        console.print(Panel(last_text, title=f"[bold {color}]{persona}[/bold {color}]", border_style=color))
                
                # Check for validation errors
                if final_state.get("error"):
                    console.print(f"[bold red]Validation failed: {final_state['error']}[/bold red]")
                    break
    except Exception as e:
        console.print(f"[bold red]Error during debate execution: {e}[/bold red]")
        log_event("debate_error", {"error": str(e)})
        if current_full_state:
            final_state = current_full_state.copy()

    if final_state:
        summary = {
            "winner": final_state.get("winner"),
            "rationale": final_state.get("rationale"),
            "persona_a": final_state.get("persona_a"),
            "persona_b": final_state.get("persona_b")
        }
        
        # Generate LangGraph visualization
        # try:
        #     graph_image = graph.get_graph().draw_mermaid_png()
        #     with open(os.path.join(debate_dir, "langgraph_dag.png"), "wb") as f:
        #         f.write(graph_image)
        #     print(f"LangGraph DAG generated successfully: {os.path.join(debate_dir, 'langgraph_dag.png')}")
        # except Exception as e:
        #     print(f"[Warning] LangGraph DAG rendering skipped: {e}")

        generate_debate_artifacts(final_state, os.path.join(debate_dir, "debate_dag"))
        return summary
    return None

if __name__ == "__main__":
    from app import main
    main()
