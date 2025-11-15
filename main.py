# main.py
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
from nodes import MemoryNode, Agent, JudgeNode, ValidationError
from logger_util import log_event
from dag_gen import generate_dag
from rich.console import Console

def validate_turn(expected_agent, actual_agent, text, seen_texts):
    if expected_agent != actual_agent:
        raise ValidationError(f"Wrong agent turn. Expected {expected_agent}, got {actual_agent}")
    if text in seen_texts:
        raise ValidationError("Repeated argument detected.")
    if not text or len(text.split()) < 5:
        raise ValidationError("Argument too short; likely incoherent.")

def run_debate(topic, persona_a="Scientist", persona_b="Philosopher", on_round_end=None):
    console = Console()
    console.print(f"Starting debate between [bold green]{persona_a}[/bold green] (AgentA) and [bold yellow]{persona_b}[/bold yellow] (AgentB)...")
    log_event("debate_started", {"topic": topic, "persona_a": persona_a, "persona_b": persona_b})

    memory = MemoryNode()
    a = Agent(persona_a, "AgentA")
    b = Agent(persona_b, "AgentB")
    a.global_seen_texts = []
    b.global_seen_texts = []
    
    judge = JudgeNode()
    seen_texts = set()

    for r in range(1, 9): # 8 rounds
        is_a_turn = (r % 2 != 0)
        expected = "AgentA" if is_a_turn else "AgentB"
        
        agent = a if is_a_turn else b
        mem_for_agent = memory.get_memory_for(agent.id)
        
        text = agent.speak(topic, mem_for_agent, r)
        
        a.global_seen_texts.append({"text": text})
        b.global_seen_texts.append({"text": text})
        
        try:
            validate_turn(expected, agent.id, text, seen_texts)
        except ValidationError as e:
            log_event("validation_error", {"round": r, "error": str(e), "agent": agent.id, "text": text})
            console.print(f"[bold red]Validation failed at round {r} for {agent.id}: {e}[/bold red]")
            return None
            
        seen_texts.add(text)
        memory.update(r, agent.id, agent.persona, text)
        
        color = "green" if is_a_turn else "yellow"
        console.print(f"[bold {color}][Round {r}] {agent.persona}:[/bold {color}] {text}")
        if on_round_end:
            on_round_end(r)

    # Judge's turn
    summary = judge.review(memory)
    
    generate_dag(memory.transcript, summary)
    return summary

if __name__ == "__main__":
    from app import main
    main()
