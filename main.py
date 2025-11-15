# main.py
import sys
from nodes import MemoryNode, Agent, JudgeNode, ValidationError
from logger_util import log_event
from dag_gen import generate_dag

def validate_turn(expected_agent, current_agent, turn_text, seen_texts):
    # ensure correct turn
    if expected_agent != current_agent:
        raise ValidationError(f"Turn order violated: expected {expected_agent}, got {current_agent}")
    # ensure not repeated argument
    if turn_text in seen_texts:
        raise ValidationError("Repeated argument detected.")
    # basic coherence check: short statements flagged
    if len(turn_text.split()) < 4:
        raise ValidationError("Argument too short; likely incoherent.")
    return True

def run_debate(topic, persona_a="Scientist", persona_b="Philosopher"):
    memory = MemoryNode()
    a = Agent(persona_a, "AgentA")
    b = Agent(persona_b, "AgentB")
    judge = JudgeNode()
    seen_texts = set()

    log_event("debate_started", {"topic": topic, "personas": [persona_a, persona_b]})
    print(f"Starting debate between {persona_a} (AgentA) and {persona_b} (AgentB)...")
    rounds = 8
    current_agent_id = "AgentA"
    for r in range(1, rounds+1):
        expected = "AgentA" if r % 2 == 1 else "AgentB"
        # select agent
        agent = a if expected == "AgentA" else b
        mem_for_agent = memory.get_memory_for(agent.id)
        # generate text
        text = agent.speak(topic, mem_for_agent, r)
        # validate
        try:
            validate_turn(expected, agent.id, text, seen_texts)
        except ValidationError as e:
            log_event("validation_error", {"round": r, "error": str(e), "agent": agent.id, "text": text})
            print(f"[Validation failed at round {r} for {agent.id}]: {e}")
            # terminate with failure
            return False
        # record
        seen_texts.add(text)
        memory.update(r, agent.id, agent.persona, text)
        # print to CLI and log
        print(f"[Round {r}] {agent.persona}: {text}")
    # After 8 rounds -> judge
    summary = judge.review(memory)
    print("\n[Judge] Summary of debate:")
    print(summary["rationale"])
    print(f"[Judge] Winner: {summary['winner']}")
    log_event("debate_completed", {"winner": summary["winner"], "scores": summary["scores"]})
    # generate DAG image
    generate_dag(memory, summary["winner"])
    return True

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        topic = " ".join(sys.argv[1:])
    else:
        topic = input("Enter topic for debate: ").strip()
    run_debate(topic)
