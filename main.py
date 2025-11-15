# main.py
import sys
import os
import argparse
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
from nodes import MemoryNode, Agent, JudgeNode, ValidationError
from logger_util import log_event
from dag_gen import generate_dag

def validate_turn(expected_agent, actual_agent, text, seen_texts):
    if expected_agent != actual_agent:
        raise ValidationError(f"Wrong agent turn. Expected {expected_agent}, got {actual_agent}")
    if text in seen_texts:
        raise ValidationError("Repeated argument detected.")
    if not text or len(text.split()) < 5:
        raise ValidationError("Argument too short; likely incoherent.")

def run_debate(topic, persona_a="Scientist", persona_b="Philosopher"):
    print(f"Starting debate between {persona_a} (AgentA) and {persona_b} (AgentB)...")
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
            print(f"[Validation failed at round {r} for {agent.id}]: {e}")
            return False
            
        seen_texts.add(text)
        memory.update(r, agent.id, agent.persona, text)
        
        print(f"[Round {r}] {agent.persona}: {text}")

    # Judge's turn
    summary = judge.review(memory)
    print("\n[Judge] Summary of debate:")
    print(summary["rationale"])
    print(f"[Judge] Winner: {summary['winner']}")
    
    generate_dag(memory.transcript, summary)
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a debate between two AI agents.")
    parser.add_argument("--topic", type=str, help="The topic of the debate.")
    parser.add_argument("--persona-a", type=str, default="Scientist", help="The persona for Agent A.")
    parser.add_argument("--persona-b", type=str, default="Philosopher", help="The persona for Agent B.")
    args = parser.parse_args()

    topic = args.topic
    if not topic:
        topic = "Should AI be regulated like medicine?"
        print(f"No topic provided. Using default topic: '{topic}'")

    run_debate(topic, args.persona_a, args.persona_b)
