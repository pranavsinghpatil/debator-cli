from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from src.state import DebateState
from src.nodes import ValidationError, clean_and_validate, hf_generate, gemini_generate
from src.logger_util import log_event
import os
import time

# --- LangGraph Nodes ---

def user_input_node(state: DebateState) -> DebateState:
    log_event("node_start", {"node": "user_input", "state_before": state})
    # This node will be called once at the beginning to get user input
    # For now, we assume topic and personas are already in state from main.py
    # In a real CLI, this would involve console.input()
    log_event("user_input_received", {"topic": state["topic"], "persona_a": state["persona_a"], "persona_b": state["persona_b"]})
    new_state = {
        "round": 0, # Initialize round to 0
        "transcript": [],
        "seen_texts": [],
        "current_agent": "AgentA", # AgentA starts
        "winner": None,
        "rationale": None,
        "error": None,
        "last_speaker": None,
        "last_text": None
    }
    log_event("node_end", {"node": "user_input", "state_after": new_state})
    return new_state

def _agent_node(state: DebateState, agent_id: str) -> DebateState:
    log_event("node_start", {"node": f"agent_{agent_id.lower()}", "state_before": state})
    current_round = state["round"] + 1 # Increment round for the current turn
    log_event("agent_turn_start", {"agent": agent_id, "round": current_round})

    persona = state["persona_a"] if agent_id == "AgentA" else state["persona_b"]
    
    # Reimplementing Agent.speak logic
    topic = state["topic"]
    memory_summary = "" # This needs to be generated from the transcript in state
    # For now, I will use a simplified memory summary.
    # In a later step, I will implement the MemoryNode logic.

    # Generate memory summary from state["transcript"]
    agent_msgs = [t["text"] for t in state["transcript"] if t["agent"] == agent_id]
    other_agent_id = "AgentB" if agent_id == "AgentA" else "AgentA"
    other_msgs = [t["text"] for t in state["transcript"] if t["agent"] == other_agent_id]
    claim = agent_msgs[-1] if agent_msgs else ""
    rebuttal = other_msgs[-1] if other_msgs else ""
    question = "Balance safety vs innovation?" if claim and rebuttal else ""
    def short(s, w=25):
        return " ".join(s.split()[:w])
    memory_summary = f"- Claim: {short(claim,25)}\n- Rebuttal: {short(rebuttal,25)}\n- Question: {question}"

    prompt = f"""
You are {persona}.
Task: Provide one concise argument (1 paragraph, 1–3 sentences, <=50 words) about the topic below.
Do NOT include metadata, quotes, or 'Round' labels. Respond only with the argument text.

Topic: {topic}
Private memory: {memory_summary}
Round: {current_round}
"""
    prev_texts = state["seen_texts"] # All texts seen so far

    # Use Gemini by default
    generator = gemini_generate
    gen_params = {}

    raw = ""
    cleaned = None
    for attempt in range(3):
        raw = generator(prompt, **gen_params)
        log_event("agent_speak_raw", {"agent": agent_id, "persona": persona, "round": current_round, "raw_text": raw})
        cleaned = clean_and_validate(raw, prev_texts) # Pass prev_texts from state
        if cleaned:
            break
        time.sleep(0.2)
    
    if not cleaned:
        topic_words = topic.split()[:2]
        topic_snippet = " ".join(topic_words).lower() if topic_words else "this topic"
        fallback = f"As {persona} ({agent_id}): round {current_round} on {topic_snippet} requires careful analysis from my perspective."
        fallback_counter = 0
        all_seen = set(prev_texts) # All texts seen so far
        while fallback in all_seen:
            fallback_counter += 1
            fallback = f"As {persona} ({agent_id}): round {current_round} analysis {fallback_counter} on {topic_snippet} demands nuanced evaluation."
        cleaned = fallback
        log_event("agent_speak_fallback", {"agent": agent_id, "round": current_round, "text": cleaned})

    new_state = {
        "round": current_round,
        "transcript": state["transcript"] + [{"round": current_round, "agent": agent_id, "persona": persona, "text": cleaned}],
        "seen_texts": state["seen_texts"] + [cleaned],
        "current_agent": "AgentB" if agent_id == "AgentA" else "AgentA", # Switch agent
        "last_speaker": agent_id,
        "last_text": cleaned
    }
    log_event("node_end", {"node": f"agent_{agent_id.lower()}", "state_after": new_state})
    return new_state

def agent_a_node(state: DebateState) -> DebateState:
    return _agent_node(state, "AgentA")

def agent_b_node(state: DebateState) -> DebateState:
    return _agent_node(state, "AgentB")

def validator_node(state: DebateState) -> DebateState:
    log_event("node_start", {"node": "validator", "state_before": state})
    current_round = state["round"]
    last_speaker = state["last_speaker"]
    last_text = state["last_text"]
    seen_texts = state["seen_texts"] # All texts seen so far, including the current one

    try:
        # Exclude current text for repeat check, as it's already in seen_texts
        if last_text in seen_texts[:-1]:
            raise ValidationError("Repeated argument detected.")
        if not last_text or len(last_text.split()) < 4:
            raise ValidationError("Argument too short; likely incoherent.")
        
        log_event("validation_success", {"agent": last_speaker, "round": current_round})
        new_state = {"error": None}
    except ValidationError as e:
        log_event("validation_error", {"round": current_round, "error": str(e), "agent": last_speaker, "text": last_text})
        new_state = {"error": str(e)}
    log_event("node_end", {"node": "validator", "state_after": new_state})
    return new_state

def judge_node(state: DebateState) -> DebateState:
    log_event("node_start", {"node": "judge", "state_before": state})
    log_event("judge_review_start", {"round": state["round"]})

    transcript = state["transcript"]
    persona_a = state["persona_a"]
    persona_b = state["persona_b"]

    weighted_keywords = {
        "AgentA": {"risk": 2, "safety": 2, "protocol": 2, "technical": 1, "verification": 1, "data": 1, "evidence": 1, "scientific": 1, "bias": 1, "testing": 1, "impact": 1, "policy": 1},
        "AgentB": {"autonomy": 2, "freedom": 2, "ethics": 2, "moral": 2, "dignity": 1, "philosophy": 1, "consciousness": 1, "agency": 1, "human": 1, "societal": 1, "rights": 1, "knowledge": 1, "wisdom": 1}
    }
    scores = {"AgentA": 0, "AgentB": 0}
    for turn in transcript:
        text = turn["text"].lower()
        agent_id = turn["agent"]
        for keyword, weight in weighted_keywords.get(agent_id, {}).items():
            if keyword in text:
                scores[agent_id] += weight
    
    if scores["AgentA"] > scores["AgentB"]:
        winner = "AgentA"
    elif scores["AgentB"] > scores["AgentA"]:
        winner = "AgentB"
    else:
        winner = "Tie"
    
    # Generate rationale
    transcript_text = "\n".join([f"[{t['persona']} R{t['round']}]: {t['text']}" for t in transcript])
    prompt = f"""
You are an impartial judge. Scores: AgentA={scores['AgentA']:.2f}, AgentB={scores['AgentB']:.2f}.
The winner is {winner}.
Transcript: {transcript_text}
Task: Provide a detailed rationale (3-4 sentences) explaining who won and why. Summarize the key arguments of each agent and then explain the reasoning for the final decision, explicitly mentioning the declared winner. Output only the rationale.
"""
    # Use Gemini by default
    generator = gemini_generate
    gen_params = {}

    raw_rationale = generator(prompt, **gen_params)
    rationale = clean_and_validate(raw_rationale, []) # No previous texts for rationale validation

    log_event("judge_review_end", {"winner": winner, "rationale": rationale})
    new_state = {
        "winner": winner,
        "rationale": rationale,
        "summary": { # Store full summary in state
            "scores": scores,
            "winner": winner,
            "rationale": rationale,
            "persona_a": persona_a,
            "persona_b": persona_b
        }
    }
    log_event("node_end", {"node": "judge", "state_after": new_state})
    return new_state

# --- Graph Definition ---
def create_debate_graph():
    workflow = StateGraph(DebateState)

    # Add nodes
    workflow.add_node("user_input", user_input_node)
    workflow.add_node("agent_a", agent_a_node)
    workflow.add_node("agent_b", agent_b_node)
    workflow.add_node("validator", validator_node)
    workflow.add_node("judge", judge_node)

    # Set entry point
    workflow.set_entry_point("user_input")

    # Define edges
    # After user input, AgentA speaks
    workflow.add_edge("user_input", "agent_a")

    # Agent A speaks -> Validate
    workflow.add_edge("agent_a", "validator")

    # Agent B speaks -> Validate
    workflow.add_edge("agent_b", "validator")

    # Conditional routing after validation
    # If error, end debate
    # If round < 8, alternate agents
    # If round == 8, go to judge
    workflow.add_conditional_edges(
        "validator",
        lambda state: "end_error" if state["error"] else ("judge" if state["round"] == 8 else ("agent_b" if state["current_agent"] == "AgentB" else "agent_a")),
        {"agent_a": "agent_a", "agent_b": "agent_b", "judge": "judge", "end_error": END}
    )

    # After judge, end
    workflow.add_edge("judge", END)

    return workflow.compile()

if __name__ == "__main__":
    # Example usage (for testing the graph directly)
    # In actual use, main.py will call this
    graph = create_debate_graph()
    # For testing, you can invoke with initial state
    initial_state = DebateState(
        topic="Should AI be regulated like medicine?",
        persona_a="Scientist",
        persona_b="Philosopher",
        round=0,
        transcript=[],
        seen_texts=[],
        current_agent="AgentA",
        winner=None,
        rationale=None,
        error=None
    )
    # You would typically run this in a loop or with a specific input
    # For a full debate, you'd iterate through the graph until END state is reached
    # For now, just a single step to demonstrate
    # result = graph.invoke(initial_state)
    # print(result)
    pass
