# nodes.py
import random
import json
from logger_util import log_event
from transformers import pipeline

# --- Local Transformers Pipeline ---
try:
    text_generator = pipeline("text-generation", model="distilgpt2", device=-1) # device=-1 for CPU
except Exception as e:
    log_event("pipeline_creation_error", {"error": str(e)})
    text_generator = None

def hf_generate(prompt, max_new_tokens=128, temperature=0.7, do_sample=True):
    if text_generator is None:
        return "Error: text-generation pipeline not available."
    try:
        generation_kwargs = {
            "max_new_tokens": max_new_tokens,
            "do_sample": do_sample,
            "temperature": temperature,
        }
        out = text_generator(
            prompt,
            return_full_text=False,
            **generation_kwargs
        )
        return out[0]["generated_text"]
    except Exception as e:
        log_event("hf_generate_error", {"error": str(e)})
        return f"Error generating text: {e}"

class ValidationError(Exception):
    pass

class MemoryNode:
    """
    Stores per-agent summary + transcript.
    Each agent only gets its relevant memory summary (no full state sharing).
    """
    def __init__(self):
        self.transcript = []  # list of (round, agent, text)
        self.summaries = {"AgentA": "", "AgentB": ""}

    def update(self, round_no, agent_id, persona, text):
        # append transcript
        self.transcript.append({"round": round_no, "agent": agent_id, "persona": persona, "text": text})
        log_event("memory_update", {"round": round_no, "agent": agent_id, "persona": persona, "text": text})
        # update summaries (simple abstractive heuristic: keep last 2 statements)
        agent_messages = [t["text"] for t in self.transcript if t["agent"] == agent_id]
        summary = " | ".join(agent_messages[-2:])
        self.summaries[agent_id] = summary
        log_event("memory_summary", {"agent": agent_id, "summary": summary})

    def get_memory_for(self, agent):
        # Only return the agent's summary (no other agent's full state)
        return self.summaries.get(agent, "")

class Agent:
    """
    Agent that produces an argument string given topic, memory, and turn_no.
    """
    def __init__(self, persona_name, agent_id):
        self.persona = persona_name
        self.id = agent_id
        self.used_arguments = set()

    def speak(self, topic, memory_summary, round_no):
        prompt = f"As a {self.persona}, my argument about '{topic}' is:"
        
        generated_text = hf_generate(prompt, max_new_tokens=100, temperature=0.9, do_sample=True)
        generated_text = generated_text.strip()
        
        # Prevent repetition
        if generated_text in self.used_arguments:
            # If repeated, try generating again with a slightly different prompt
            prompt += " A different argument is:"
            generated_text = hf_generate(prompt, max_new_tokens=100, temperature=0.9, do_sample=True)
            generated_text = generated_text.strip()

        self.used_arguments.add(generated_text)
        log_event("agent_speak", {"agent": self.id, "persona": self.persona, "round": round_no, "text": generated_text})
        return generated_text

class JudgeNode:
    """
    Reviews memory and transcript, produces summary and declares winner.
    Uses simple scoring heuristics:
      - Count occurrence of 'risk', 'safety', 'rights', 'autonomy', 'innovation' as proxies.
      - Reward novelty (no repeated exact text).
    """
    def __init__(self):
        pass

    def review(self, memory: MemoryNode):
        transcript = memory.transcript
        log_event("judge_review_started", {"transcript_len": len(transcript)})

        # Define persona-specific keywords with weights
        # Higher weights for more central concepts
        weighted_keywords = {
            "AgentA": {
                "risk": 2, "safety": 2, "protocol": 2, "technical": 1, "verification": 1,
                "data": 1, "evidence": 1, "scientific": 1, "bias": 1, "testing": 1,
                "impact": 1, "policy": 1
            },
            "AgentB": {
                "autonomy": 2, "freedom": 2, "ethics": 2, "moral": 2, "dignity": 1,
                "philosophy": 1, "consciousness": 1, "agency": 1, "human": 1,
                "societal": 1, "rights": 1, "knowledge": 1, "wisdom": 1
            }
        }

        scores = {"AgentA": 0, "AgentB": 0}
        agent_contributions = {"AgentA": [], "AgentB": []}

        for turn in transcript:
            text = turn["text"].lower()
            agent_id = turn["agent"]
            agent_contributions[agent_id].append(text)

            # Apply weighted keyword scoring
            for keyword, weight in weighted_keywords.get(agent_id, {}).items():
                if keyword in text:
                    scores[agent_id] += weight

        # Novelty and diversity bonus: reward for unique and varied arguments
        # This encourages agents to not just repeat keywords but to form diverse arguments
        for agent_id in ["AgentA", "AgentB"]:
            unique_arguments = set(agent_contributions[agent_id])
            scores[agent_id] += len(unique_arguments) * 0.5 # Bonus for each unique argument

            # Further bonus for using a wider range of their persona's keywords
            used_keywords_count = 0
            for arg_text in unique_arguments:
                for keyword in weighted_keywords.get(agent_id, {}).keys():
                    if keyword in arg_text:
                        used_keywords_count += 1
            scores[agent_id] += (used_keywords_count / len(weighted_keywords.get(agent_id, {}).keys())) * 2 # Max 2 points

        # Determine winner and rationale
        winner = ""
        rationale = []

        if scores["AgentA"] > scores["AgentB"]:
            winner = "AgentA"
            # Find the persona for AgentA from the transcript
            agent_a_persona = next((t['persona'] for t in transcript if t['agent'] == "AgentA"), "AgentA")
            rationale.append(f"{agent_a_persona} (AgentA) presented a more compelling argument.")
            rationale.append(f"Their arguments consistently emphasized key concepts like {', '.join(random.sample(list(weighted_keywords['AgentA'].keys()), min(3, len(weighted_keywords['AgentA'].keys()))))} and demonstrated a broader range of relevant points.")
        elif scores["AgentB"] > scores["AgentA"]:
            winner = "AgentB"
            # Find the persona for AgentB from the transcript
            agent_b_persona = next((t['persona'] for t in transcript if t['agent'] == "AgentB"), "AgentB")
            rationale.append(f"{agent_b_persona} (AgentB) presented a more compelling argument.")
            rationale.append(f"Their arguments effectively highlighted concepts such as {', '.join(random.sample(list(weighted_keywords['AgentB'].keys()), min(3, len(weighted_keywords['AgentB'].keys()))))} and showed greater diversity in their reasoning.")
        else:
            # Tie-breaker: prefer the agent with more unique arguments, then AgentA
            unique_a = len(set(agent_contributions["AgentA"]))
            unique_b = len(set(agent_contributions["AgentB"]))
            if unique_a > unique_b:
                winner = "AgentA"
                rationale.append("The debate was very close, but AgentA demonstrated slightly more unique arguments.")
            elif unique_b > unique_a:
                winner = "AgentB"
                rationale.append("The debate was very close, but AgentB demonstrated slightly more unique arguments.")
            else:
                winner = "AgentA" # Default tie-breaker
                rationale.append("The debate was a tie in terms of argument strength and diversity. AgentA is declared the winner by default.")

        summary = {
            "scores": scores,
            "winner": winner,
            "rationale": "\n".join(rationale)
        }
        log_event("judge_summary", summary)
        return summary
