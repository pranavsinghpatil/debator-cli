# nodes.py
import random
from logger_util import log_event

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

    def update(self, round_no, agent, text):
        # append transcript
        self.transcript.append({"round": round_no, "agent": agent, "text": text})
        log_event("memory_update", {"round": round_no, "agent": agent, "text": text})
        # update summaries (simple abstractive heuristic: keep last 2 statements)
        agent_messages = [t["text"] for t in self.transcript if t["agent"] == agent]
        summary = " | ".join(agent_messages[-2:])
        self.summaries[agent] = summary
        log_event("memory_summary", {"agent": agent, "summary": summary})

    def get_memory_for(self, agent):
        # Only return the agent's summary (no other agent's full state)
        return self.summaries.get(agent, "")

class Agent:
    """
    Agent that produces an argument string given topic, memory, and turn_no.
    For production you can replace body with an LLM call.
    persona_name: e.g., "Scientist" or "Philosopher"
    id: "AgentA" or "AgentB"
    """
    def __init__(self, persona_name, agent_id):
        self.persona = persona_name
        self.id = agent_id
        self.used_arguments = set()

    def speak(self, topic, memory_summary, round_no):
        # Example deterministic-ish generation for reproducibility.
        # Replace this logic with an LLM call (OpenAI/Anthropic etc.) in real solution.
        base = f"[{self.persona} R{round_no}] On '{topic}',"
        # produce variant arguments with some templates
        templates = [
            "we must consider the practical risks and safety protocols.",
            "this touches deep values like autonomy and freedom.",
            "historical precedent warns us against ignoring unintended consequences.",
            "technical feasibility and verification are central to responsible adoption.",
            "overregulation can stifle innovation but under-regulation risks harm.",
            "ethical frameworks and public health analogies are instructive."
        ]
        # choose a phrase not used before
        for t in templates:
            candidate = base + " " + t
            if candidate not in self.used_arguments:
                self.used_arguments.add(candidate)
                log_event("agent_speak", {"agent": self.id, "persona": self.persona, "round": round_no, "text": candidate})
                return candidate
        # fallback (shouldn't happen for 4 rounds)
        fallback = base + " concluding with a call for balanced oversight."
        self.used_arguments.add(fallback)
        log_event("agent_speak", {"agent": self.id, "persona": self.persona, "round": round_no, "text": fallback})
        return fallback

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
        # Build full debate text
        transcript = memory.transcript
        log_event("judge_review_started", {"transcript_len": len(transcript)})
        # simple scoring based on keyword counts
        keywords = {
            "AgentA": ["risk", "safety", "verification", "public", "health", "protocol"],
            "AgentB": ["autonomy", "freedom", "philosophy", "innovation", "ethics", "progress"]
        }
        scores = {"AgentA": 0, "AgentB": 0}
        for turn in transcript:
            text = turn["text"].lower()
            agent = turn["agent"]
            for kw in keywords[agent]:
                if kw in text:
                    scores[agent] += 1
        # novelty bonus: unique sentence count
        unique_texts = len({t["text"] for t in transcript})
        # simplistic tie-break: higher score wins, else prefer AgentA
        if scores["AgentA"] > scores["AgentB"]:
            winner = "AgentA"
        elif scores["AgentB"] > scores["AgentA"]:
            winner = "AgentB"
        else:
            # tie-breaker by unique contribution or pick AgentA
            winner = "AgentA" if unique_texts % 2 == 1 else "AgentB"
        summary = {
            "scores": scores,
            "winner": winner,
            "rationale": f"Scores computed from keyword matches: {scores}"
        }
        log_event("judge_summary", summary)
        return summary
