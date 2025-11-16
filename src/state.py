from typing import TypedDict, List, Optional

class DebateState(TypedDict):
    topic: str
    persona_a: str
    persona_b: str
    round: int
    transcript: List[dict]
    seen_texts: List[str]
    current_agent: str # "AgentA" or "AgentB"
    winner: Optional[str]
    rationale: Optional[str]
    error: Optional[str]
    last_speaker: Optional[str]
    last_text: Optional[str]
