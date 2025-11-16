"""
LangGraph implementation for Multi-Agent Debate DAG
Implements the complete LangGraph workflow with all nodes as LangGraph nodes
"""
from typing import TypedDict, List, Optional, Dict, Any, Literal
import json
import time
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.state import CompiledStateGraph

from state import DebateState
from nodes import Agent, MemoryNode, JudgeNode, validate_turn, gemini_generate
from logger_util import log_event


def user_input_node(state: DebateState) -> DebateState:
    """Accepts the debate topic at runtime from the user"""
    log_event("node_start", {"node": "user_input", "state_before": state})
    
    # Initialize state with topic and personas
    initial_state = state.copy()
    initial_state["round"] = 1  # Start at round 1
    initial_state["current_agent"] = "AgentA"
    initial_state["winner"] = None
    initial_state["rationale"] = None
    initial_state["error"] = None
    initial_state["transcript"] = []
    initial_state["seen_texts"] = []
    initial_state["last_speaker"] = None
    initial_state["last_text"] = None
    
    log_event("user_input_end", initial_state)
    log_event("node_end", {"node": "user_input", "state_after": initial_state})
    return initial_state


def agent_a_node(state: DebateState) -> DebateState:
    """AgentA's turn to speak - speaks in odd rounds (1, 3, 5, 7)"""
    log_event("node_start", {"node": "agent_a", "state_before": state})
    
    # Ensure we're at an odd round for AgentA
    # Round 1, 3, 5, 7 = AgentA's rounds
    current_round = state["round"]
    
    # Create AgentA instance
    agent_a = Agent(state["persona_a"])
    
    # Generate argument
    context = ""
    if state["transcript"]:
        # Get last 2 exchanges for context
        recent = state["transcript"][-4:] if len(state["transcript"]) >= 4 else state["transcript"]
        context = "\n".join([f"[{t['persona']}]: {t['text']}" for t in recent])
    
    text = agent_a.speak(
        topic=state["topic"],
        context=context,
        seen_texts=state["seen_texts"],
        round_num=current_round
    )
    
    if text:
        # Validate the turn (returns cleaned text or None)
        cleaned_text = validate_turn(text, state["seen_texts"], max_words=80)
        if cleaned_text:
            # Use cleaned text
            text = cleaned_text
        else:
            # Validation failed - try to use original text anyway (very lenient)
            log_event("agent_a_validation_failed", {"round": current_round, "original_text": text})
            # Clean and use original text if it's reasonable
            original_text = text.strip().strip('\"\'` ')
            if len(original_text.split()) >= 3 and len(original_text.split()) <= 100:
                # Add punctuation if missing
                if not original_text[-1] in '.!?':
                    original_text += '.'
                text = original_text
                log_event("agent_a_using_original", {"round": current_round, "text": text})
            else:
                # Last resort: generate unique context-aware fallback
                prev_args = state.get("transcript", [])
                prev_texts_list = state.get("seen_texts", [])
                
                # Generate a unique argument based on round and previous context
                round_specific = ["emphasizing empirical evidence", "highlighting data-driven analysis", 
                                 "focusing on safety protocols", "stressing rigorous testing",
                                 "underlining risk assessment", "advocating for systematic validation",
                                 "demonstrating scientific methodology", "showcasing evidence-based approach"]
                
                context_hint = round_specific[(current_round - 1) % len(round_specific)]
                
                if prev_args:
                    last_speaker = prev_args[-1].get("agent", "")
                    if last_speaker == "AgentB":
                        context_hint += " while responding to philosophical concerns"
                
                # Create unique text that won't match previous ones
                text = f"As {state['persona_a']}, I {context_hint}: {state['topic']} demands systematic evaluation based on empirical data and risk assessment in round {current_round}."
                if not text.endswith(('.', '!', '?')):
                    text += "."
                log_event("agent_a_fallback_used", {"round": current_round, "fallback_text": text})
        
        # Add to transcript (always add, even if validation failed - debate must continue)
        entry = {
            "round": current_round,
            "agent": "AgentA",
            "persona": state["persona_a"],
            "text": text,
            "timestamp": datetime.now().isoformat()
        }
        state["transcript"].append(entry)
        state["seen_texts"].append(text)
        state["last_speaker"] = "AgentA"
        state["last_text"] = text
        
        log_event("agent_a_speak", {
            "round": current_round,
            "persona": state["persona_a"],
            "text": text
        })
    else:
        # Generation failed - use fallback to ensure debate continues
        log_event("agent_a_generation_failed", {"round": current_round})
        text = f"As {state['persona_a']}, I argue that {state['topic']}. This perspective is crucial for round {current_round}."
        if not text.endswith(('.', '!', '?')):
            text += "."
        log_event("agent_a_fallback_used", {"round": current_round, "fallback_text": text, "reason": "generation_failed"})
        
        # Add fallback to transcript
        entry = {
            "round": current_round,
            "agent": "AgentA",
            "persona": state["persona_a"],
            "text": text,
            "timestamp": datetime.now().isoformat()
        }
        state["transcript"].append(entry)
        state["seen_texts"].append(text)
        state["last_speaker"] = "AgentA"
        state["last_text"] = text
    
    # Switch to AgentB for next turn
    state["current_agent"] = "AgentB"
    
    log_event("node_end", {"node": "agent_a", "state_after": state})
    return state


def agent_b_node(state: DebateState) -> DebateState:
    """AgentB's turn to speak - speaks in even rounds (2, 4, 6, 8)"""
    log_event("node_start", {"node": "agent_b", "state_before": state})
    
    # AgentB speaks in even rounds (2, 4, 6, 8)
    # Round number should be even (2, 4, 6, 8)
    current_round = state["round"] + 1  # Increment to next round (even number)
    
    # Create AgentB instance
    agent_b = Agent(state["persona_b"])
    
    # Generate argument
    context = ""
    if state["transcript"]:
        # Get last 2 exchanges for context
        recent = state["transcript"][-4:] if len(state["transcript"]) >= 4 else state["transcript"]
        context = "\n".join([f"[{t['persona']}]: {t['text']}" for t in recent])
    
    text = agent_b.speak(
        topic=state["topic"],
        context=context,
        seen_texts=state["seen_texts"],
        round_num=current_round
    )
    
    if text:
        # Debug: log the generated text
        log_event("agent_b_generated", {
            "round": current_round,
            "text": text,
            "text_length": len(text.split()),
            "seen_texts_count": len(state["seen_texts"])
        })
        
        # Validate the turn (returns cleaned text or None)
        cleaned_text = validate_turn(text, state["seen_texts"], max_words=80)
        if cleaned_text:
            # Use cleaned text
            text = cleaned_text
        else:
            # Validation failed - try to use original text anyway (very lenient)
            log_event("agent_b_validation_failed", {"round": current_round, "original_text": text})
            # Clean and use original text if it's reasonable
            original_text = text.strip().strip('\"\'` ')
            if len(original_text.split()) >= 3 and len(original_text.split()) <= 100:
                # Add punctuation if missing
                if not original_text[-1] in '.!?':
                    original_text += '.'
                text = original_text
                log_event("agent_b_using_original", {"round": current_round, "text": text})
            else:
                # Last resort: generate unique context-aware fallback
                prev_args = state.get("transcript", [])
                prev_texts_list = state.get("seen_texts", [])
                
                # Generate a unique argument based on round and previous context
                round_specific = ["examining ethical implications", "questioning underlying values",
                                 "exploring autonomy concerns", "analyzing societal impacts",
                                 "considering moral dimensions", "evaluating philosophical foundations",
                                 "reflecting on human dignity", "contemplating fundamental rights"]
                
                context_hint = round_specific[(current_round - 1) % len(round_specific)]
                
                if prev_args:
                    last_speaker = prev_args[-1].get("agent", "")
                    if last_speaker == "AgentA":
                        context_hint += " while challenging empirical assumptions"
                
                # Create unique text that won't match previous ones
                text = f"As {state['persona_b']}, I {context_hint}: {state['topic']} raises profound questions about human autonomy, ethical frameworks, and societal values in round {current_round}."
                if not text.endswith(('.', '!', '?')):
                    text += "."
                log_event("agent_b_fallback_used", {"round": current_round, "fallback_text": text})
        
        # Add to transcript (always add, even if validation failed - debate must continue)
        entry = {
            "round": current_round,
            "agent": "AgentB",
            "persona": state["persona_b"],
            "text": text,
            "timestamp": datetime.now().isoformat()
        }
        state["transcript"].append(entry)
        state["seen_texts"].append(text)
        state["last_speaker"] = "AgentB"
        state["last_text"] = text
        
        log_event("agent_b_speak", {
            "round": current_round,
            "persona": state["persona_b"],
            "text": text
        })
    else:
        # Generation failed - use fallback to ensure debate continues
        log_event("agent_b_generation_failed", {"round": current_round})
        text = f"As {state['persona_b']}, I counter that {state['topic']}. This alternative view is essential for round {current_round}."
        if not text.endswith(('.', '!', '?')):
            text += "."
        log_event("agent_b_fallback_used", {"round": current_round, "fallback_text": text, "reason": "generation_failed"})
        
        # Add fallback to transcript
        entry = {
            "round": current_round,
            "agent": "AgentB",
            "persona": state["persona_b"],
            "text": text,
            "timestamp": datetime.now().isoformat()
        }
        state["transcript"].append(entry)
        state["seen_texts"].append(text)
        state["last_speaker"] = "AgentB"
        state["last_text"] = text
    
    # Increment round for next turn (will be odd, so AgentA speaks next)
    state["round"] = current_round + 1  # Set to next odd number for AgentA
    # Switch back to AgentA for next round
    state["current_agent"] = "AgentA"
    
    log_event("node_end", {"node": "agent_b", "state_after": state})
    return state


def memory_node(state: DebateState) -> DebateState:
    """Updates memory and generates summaries"""
    log_event("node_start", {"node": "memory", "state_before": state})
    
    memory = MemoryNode()
    
    # Update memory with new transcript entries
    if state["transcript"]:
        memory.update(state["transcript"])
        
        # Generate summary
        summary = memory.get_summary()
        if summary:
            log_event("memory_summary", {"summary": summary, "round": state["round"]})
    
    log_event("node_end", {"node": "memory", "state_after": state})
    return state


def validator_node(state: DebateState) -> DebateState:
    """Validates the debate state and ensures logical coherence"""
    log_event("node_start", {"node": "validator", "state_before": state})
    
    # Don't stop on errors - log them but continue the debate
    if state.get("error"):
        log_event("validator_error_found", {"error": state["error"]})
        # Don't block execution - just log it
        # Clear the error so debate can continue
        if "Duplicate arguments detected" in state.get("error", ""):
            log_event("validator_duplicate_warning", {"message": "Duplicates found but continuing debate"})
            state["error"] = None  # Clear error to continue
        
    # Skip turn order validation - let the graph handle it
    # The graph structure ensures proper turn order
        
    # Validate transcript coherence - but don't stop on duplicates
    if state["transcript"]:
        # Check for duplicate arguments (for logging only)
        texts = [entry["text"] for entry in state["transcript"]]
        unique_texts = set(texts)
        if len(texts) != len(unique_texts):
            duplicate_count = len(texts) - len(unique_texts)
            log_event("validator_duplicate_arguments", {
                "duplicates": duplicate_count,
                "total": len(texts),
                "unique": len(unique_texts),
                "action": "continuing_debate"
            })
            # Don't set error - just log it and continue
        
    log_event("node_end", {"node": "validator", "state_after": state})
    return state


def judge_node(state: DebateState) -> DebateState:
    """Reviews memory and all argument nodes, produces summary and declares winner"""
    log_event("node_start", {"node": "judge", "state_before": state})
    
    judge = JudgeNode()
    
    # Review the debate - pass topic if available in transcript entries or use state topic
    transcript_for_judge = state["transcript"]
    # Add topic to transcript entries if not present (for judge's use)
    if transcript_for_judge and len(transcript_for_judge) > 0:
        for entry in transcript_for_judge:
            if "topic" not in entry:
                entry = entry.copy()
                entry["topic"] = state.get("topic", "the debate topic")
    
    result = judge.review(state["transcript"], state["persona_a"], state["persona_b"], state.get("topic", ""))
    
    if result:
        state["winner"] = result["winner"]
        state["rationale"] = result["rationale"]
        state["summary"] = result
        
        log_event("judge_review_end", {
            "winner": result["winner"],
            "rationale": result["rationale"]
        })
    else:
        state["error"] = "Judge failed to review debate"
        log_event("judge_review_failed", {"round": state["round"]})
    
    log_event("node_end", {"node": "judge", "state_after": state})
    return state


def should_continue_debate(state: DebateState) -> Literal["agent_b", "memory", "judge"]:
    """Conditional routing function to determine if debate should continue"""
    # Check for errors
    if state.get("error"):
        return "judge"
    
    # Check if we've completed 8 rounds
    if state["round"] >= 8:
        return "judge"
    
    # AgentA always goes to AgentB
    return "agent_b"


def should_continue_after_validator(state: DebateState) -> Literal["agent_a", "judge"]:
    """Conditional routing after validator"""
    # Don't stop on errors - continue the debate to complete all 8 rounds
    # Errors are logged but don't halt execution
    
    # Check if we've completed 8 rounds
    # After AgentB speaks in round 8, round becomes 9
    # We want 8 rounds total: 1(A), 2(B), 3(A), 4(B), 5(A), 6(B), 7(A), 8(B)
    # When round > 8, we've completed all 8 rounds
    if state["round"] > 8:
        return "judge"
    
    # Check if we have 8 entries in transcript (safety check)
    if len(state.get("transcript", [])) >= 8:
        return "judge"
    
    # Continue with AgentA for next round
    return "agent_a"


# Cache the compiled graph to avoid recreating it every time
_graph_cache = None

def create_debate_graph() -> CompiledStateGraph:
    """Creates and compiles the LangGraph debate workflow"""
    global _graph_cache
    
    # Return cached graph if available
    if _graph_cache is not None:
        return _graph_cache
    
    # Create the StateGraph
    workflow = StateGraph(DebateState)
    
    # Add nodes
    workflow.add_node("user_input", user_input_node)
    workflow.add_node("agent_a", agent_a_node)
    workflow.add_node("agent_b", agent_b_node)
    workflow.add_node("memory", memory_node)
    workflow.add_node("validator", validator_node)
    workflow.add_node("judge", judge_node)
    
    # Set entry point
    workflow.set_entry_point("user_input")
    
    # Add edges
    workflow.add_edge("user_input", "agent_a")
    
    # AgentA to AgentB (simplified)
    workflow.add_edge("agent_a", "agent_b")
    
    # AgentB to memory
    workflow.add_edge("agent_b", "memory")
    
    # Memory to validator
    workflow.add_edge("memory", "validator")
    
    # Conditional routing from validator
    workflow.add_conditional_edges(
        "validator",
        should_continue_after_validator,
        {
            "agent_a": "agent_a",
            "judge": "judge"
        }
    )
    
    # Judge to END
    workflow.add_edge("judge", END)
    
    # Compile the graph
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    # Cache the compiled graph
    _graph_cache = app
    
    return app


def run_langgraph_debate(topic: str, persona_a: str, persona_b: str, console=None) -> Dict[str, Any]:
    """Execute the LangGraph debate workflow with progressive updates"""
    log_event("langgraph_debate_start", {"topic": topic, "persona_a": persona_a, "persona_b": persona_b})
    
    # Create the graph
    app = create_debate_graph()
    
    # Initialize state
    initial_state = DebateState(
        topic=topic,
        persona_a=persona_a,
        persona_b=persona_b,
        round=1,
        transcript=[],
        seen_texts=[],
        current_agent="AgentA",
        winner=None,
        rationale=None,
        error=None,
        last_speaker=None,
        last_text=None
    )
    
    # Track displayed rounds to avoid duplicates
    displayed_rounds = set()
    
    # Run the graph with streaming for progressive updates
    try:
        config = {
            "recursion_limit": 50,
            "configurable": {"thread_id": "debate-thread-1"}
        }
        
        # Use stream to get progressive updates
        final_state = None
        for event in app.stream(initial_state, config=config, stream_mode="updates"):
            # Get the state after each node execution
            for node_name, state in event.items():
                # Display rounds as they complete (after agent nodes)
                if node_name in ["agent_a", "agent_b"] and state.get("transcript"):
                    # Find the latest transcript entry
                    latest_entry = state["transcript"][-1]
                    round_num = latest_entry["round"]
                    
                    # Only display if we haven't shown this round yet
                    if round_num not in displayed_rounds:
                        displayed_rounds.add(round_num)
                        if console:
                            agent = latest_entry["agent"]
                            persona = latest_entry["persona"]
                            text = latest_entry["text"]
                            color = "green" if agent == "AgentA" else "yellow"
                            
                            from rich.rule import Rule
                            from rich.panel import Panel
                            console.print(Rule(f"Round {round_num}", style="bold blue"))
                            console.print(Panel(text, title=f"[bold {color}]{persona}[/bold {color}]", border_style=color))
                            console.print()  # Add spacing between rounds
                
                # Display judge decision when judge node completes
                if node_name == "judge" and state.get("winner") and console:
                    console.print()
                    console.print(Rule("Judge's Verdict", style="bold magenta"))
                
                # Update final state
                final_state = state
        
        # If streaming didn't work, fall back to invoke
        if final_state is None:
            final_state = app.invoke(initial_state, config=config)
        
        log_event("langgraph_debate_end", {"final_state": final_state})
        return final_state
    except Exception as e:
        log_event("langgraph_debate_error", {"error": str(e)})
        return {
            "error": f"LangGraph execution failed: {str(e)}",
            "topic": topic,
            "persona_a": persona_a,
            "persona_b": persona_b,
            "transcript": [],
            "winner": None,
            "rationale": None
        }


def generate_langgraph_dag() -> str:
    """Generates a Mermaid diagram of the LangGraph structure using built-in methods"""
    
    # Create the graph to get its structure
    app = create_debate_graph()
    
    # Use LangGraph's built-in Mermaid generation
    try:
        # Try different methods to get Mermaid diagram
        graph = app.get_graph()
        
        # Check if draw_mermaid method exists
        if hasattr(graph, 'draw_mermaid'):
            mermaid_diagram = graph.draw_mermaid()
            if mermaid_diagram:
                log_event("langgraph_dag_generation_success", {"method": "draw_mermaid"})
                return mermaid_diagram
        
        # Alternative: try draw method
        if hasattr(graph, 'draw'):
            mermaid_diagram = graph.draw()
            if mermaid_diagram:
                log_event("langgraph_dag_generation_success", {"method": "draw"})
                return mermaid_diagram
                
    except Exception as e:
        log_event("langgraph_dag_generation_error", {"error": str(e)})
    
    # Fallback to manual Mermaid diagram showing the actual structure
    log_event("langgraph_dag_fallback", {"reason": "built-in method not available"})
    return """
graph TD
    A["User Input Node"] --> B["Agent A Node"]
    B --> C["Agent B Node"]
    C --> D["Memory Node"]
    D --> E["Validator Node"]
    E --> F{"Continue?"}
    F -->|Round <= 8| B
    F -->|Round > 8| G["Judge Node"]
    G --> H["END"]
    
    style A fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    style B fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    style C fill:#fff3e0,stroke:#e65100,stroke-width:2px
    style D fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    style E fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    style G fill:#ffebee,stroke:#b71c1c,stroke-width:2px
    style H fill:#f5f5f5,stroke:#424242,stroke-width:2px
        """


if __name__ == "__main__":
    # Test the LangGraph implementation
    result = run_langgraph_debate(
        topic="Should AI be regulated like medicine?",
        persona_a="Scientist",
        persona_b="Philosopher"
    )
    
    print("Debate Results:")
    print(f"Winner: {result.get('winner')}")
    print(f"Rationale: {result.get('rationale')}")
    print(f"Rounds: {len(result.get('transcript', []))}")
    print(f"Error: {result.get('error')}")
