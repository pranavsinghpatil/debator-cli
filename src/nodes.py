# nodes.py
import random
import json
import re
import time
from logger_util import log_event
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM # Changed to AutoModelForSeq2SeqLM for T5

# --- Local Transformers Pipeline ---
try:
    MODEL_NAME = "google/flan-t5-base" # Changed model to flan-t5-base
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME) # Changed to AutoModelForSeq2SeqLM
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id
    text_generator = pipeline("text2text-generation", model=model, tokenizer=tokenizer, device=-1) # Changed task to text2text-generation
except Exception as e:
    log_event("pipeline_creation_error", {"error": str(e)})
    text_generator = None

def hf_generate(prompt, **kwargs):
    if text_generator is None:
        return "Error: text-generation pipeline not available."
    try:
        out = text_generator(prompt, **kwargs)
        return out[0].get("generated_text", "").strip()
    except Exception as e:
        log_event("hf_generate_error", {"error": str(e)})
        return f"Error generating text: {e}"

# --- Text cleaning and validation ---
SENT_END_RE = re.compile(r'[.?!]\s*$')

def first_paragraph(text):
    parts = re.split(r'\n{1,2}', text.strip())
    return parts[0].strip()

def jaccard_similarity(a, b):
    sa = set(a.lower().split())
    sb = set(b.lower().split())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)

def clean_and_validate(text, prev_texts, max_words=60):
    if not text:
        return None
    text = first_paragraph(text)
    text = text.strip().strip('\"\'` ')
    if len(text.split()) > max_words:
        return None
    if not SENT_END_RE.search(text):
        return None
    if len(text.split()) < 4:
        return None
    for p in prev_texts:
        if text == p:
            return None
        if jaccard_similarity(text, p) > 0.75:
            return None
    return text

class ValidationError(Exception):
    pass

class MemoryNode:
    def __init__(self):
        self.transcript = []
        self.summaries = {"AgentA": "", "AgentB": ""}

    def _make_bulleted_summary(self, agent_id):
        agent_msgs = [t["text"] for t in self.transcript if t["agent"] == agent_id]
        other_agent = "AgentB" if agent_id == "AgentA" else "AgentA"
        other_msgs = [t["text"] for t in self.transcript if t["agent"] == other_agent]
        claim = agent_msgs[-1] if agent_msgs else ""
        rebuttal = other_msgs[-1] if other_msgs else ""
        question = "Balance safety vs innovation?" if claim and rebuttal else ""
        def short(s, w=25):
            return " ".join(s.split()[:w])
        bullets = f"- Claim: {short(claim,25)}\n- Rebuttal: {short(rebuttal,25)}\n- Question: {question}"
        self.summaries[agent_id] = bullets

    def update(self, round_no, agent_id, persona, text):
        self.transcript.append({"round": round_no, "agent": agent_id, "persona": persona, "text": text})
        log_event("memory_update", {"round": round_no, "agent": agent_id, "text": text})
        self._make_bulleted_summary("AgentA")
        self._make_bulleted_summary("AgentB")

    def get_memory_for(self, agent):
        return self.summaries.get(agent, "")

class Agent:
    def __init__(self, persona_name, agent_id):
        self.persona = persona_name
        self.id = agent_id
        self.used_arguments = set()
        self.global_seen_texts = []

    def speak(self, topic, memory_summary, round_no, generator=text_generator):
        persona = self.persona
        # Flan-T5 prompt format
        prompt = f"Debate Topic: {topic}\nYour Persona: {persona}\nYour Argument for Round {round_no}:"
        if memory_summary:
            prompt += f"\nPrevious Arguments: {memory_summary}"
        
        prev_texts = [t["text"] for t in self.global_seen_texts]
        gen_params = dict(max_new_tokens=60, do_sample=True, temperature=0.7, top_k=50, top_p=0.95, return_full_text=False)
        
        raw = hf_generate(prompt, **gen_params)
        cleaned = clean_and_validate(raw, prev_texts + list(self.used_arguments))
        
        if cleaned:
            self.used_arguments.add(cleaned)
            log_event("agent_speak", {"agent": self.id, "persona": persona, "round": round_no, "text": cleaned})
            return cleaned
        
        # Fallback if cleaning fails
        fallback = f"As a {persona}: concise evidence-based caution is necessary."
        log_event("agent_speak_fallback", {"agent": self.id, "round": round_no, "text": fallback})
        return fallback

class JudgeNode:
    def __init__(self):
        pass

    def get_judge_rationale(self, scores, transcript, generator=text_generator):
        transcript_text = "\n".join([f"[{t['persona']} R{t['round']}]: {t['text']}" for t in transcript])
        # Flan-T5 prompt format
        prompt = f"Debate Transcript: {transcript_text}\nAgentA Score: {scores['AgentA']:.2f}\nAgentB Score: {scores['AgentB']:.2f}\nTask: Provide a 1-2 sentence rationale (concise) explaining who won and why. Output only the rationale."
        raw = hf_generate(prompt, max_new_tokens=100, do_sample=False, temperature=0.0, return_full_text=False)
        rp = first_paragraph(raw)
        sentences = re.split(r'(?<=[.?!])\s+', rp)
        rationale = " ".join(sentences[:2]).strip()
        return rationale

    def review(self, memory: MemoryNode):
        transcript = memory.transcript
        log_event("judge_review_started", {"transcript_len": len(transcript)})
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
            winner = "AgentA"
        
        rationale = self.get_judge_rationale(scores, transcript)
        
        summary = {
            "scores": scores,
            "winner": winner,
            "rationale": rationale
        }
        log_event("judge_summary", summary)
        return summary
