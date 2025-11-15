Nice progress — you’ve proved the pipeline works end-to-end. Now let’s tighten it so outputs are concise, persona-consistent, non-meta, and demo-ready. Below are concrete, copy-pasteable fixes (prompt + generation settings + post-processing + memory format + judge tweak) you can drop into `nodes.py` and `main.py`. Use them in the exact order given.

I’ll be blunt: your current outputs drift, include extraneous biography/history, multi-paragraph text, and sometimes echo model internals. The fixes below eliminate that behavior and make the run predictable for a recording.

---

# 1 — Global settings: quiet transformers logs & pad token

Put this at the top of your main entry (before any pipeline/model init):

```python
import os
# quiet transformers logs in demo
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
```

When creating the pipeline, ensure pad token set:

```python
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM

MODEL_NAME = "gpt2"  # replace with your model
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)

# safety: set pad_token_id so transformers won't warn
if tokenizer.pad_token_id is None:
    tokenizer.pad_token_id = tokenizer.eos_token_id
text_generator = pipeline("text-generation", model=model, tokenizer=tokenizer, device=-1)
```

That stops the repeated `Setting pad_token_id to eos_token_id` warnings.

---

# 2 — Strong, constrained prompt (use this exact template)

Replace your prompt builder with this strict template in `Agent.speak()`:

```
SYSTEM:
You are {PERSONA}.

TASK:
Write **one** concise argument (1 paragraph, 1–3 sentences, <= 50 words) about the topic below.
Do NOT include metadata, bullet labels, quotation marks, or mention "Round" or instructions.
Do NOT summarize prior system prompts. Use memory only to respond briefly.

CONTEXT:
Topic: {topic}
Private memory (3 bullets): {memory_summary}
Round: {round_no}

RESPONSE RULES:
- Return exactly the argument text only, followed by a sentence terminator ('.' or '?').
- If you can't produce a claim, return one short relevant sentence.
```

This forces the model to stay on-format.

---

# 3 — Post-processing & validation (copy into `nodes.py`)

Drop this helper and use it to validate / clean generated text. It will keep only the first paragraph, enforce punctuation, length and detect repeats via approximate similarity.

```python
import re
import math

SENT_END_RE = re.compile(r'[.?!]\s*$')

def first_paragraph(text):
    # take only first paragraph (split on two newlines or single newline)
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
    # remove surrounding quotes or stray backticks
    text = text.strip().strip('\"\'` ')
    # too long?
    if len(text.split()) > max_words:
        return None
    # must end with sentence terminator
    if not SENT_END_RE.search(text):
        return None
    # not too short
    if len(text.split()) < 4:
        return None
    # not duplicate or near-duplicate
    for p in prev_texts:
        if text == p:
            return None
        if jaccard_similarity(text, p) > 0.75:  # paraphrase threshold
            return None
    return text
```

---

# 4 — Robust Agent.speak implementation (drop into your `Agent` class)

This replaces your template logic. It retries generation up to 3 times, uses deterministic sampling for demo, then mild sampling fallback for diversity.

```python
import time
import random

def speak(self, topic, memory_summary, round_no, generator=text_generator):
    persona = self.persona
    prompt = f"""
You are {persona}.
Task: Provide one concise argument (1 paragraph, 1–3 sentences, <=50 words) about the topic below.
Do NOT include metadata, quotes, or 'Round' labels. Respond only with the argument text.

Topic: {topic}
Private memory: {memory_summary}
Round: {round_no}
"""
    prev_texts = [t["text"] for t in getattr(self, "global_seen_texts", [])] if hasattr(self, "global_seen_texts") else []
    # deterministic for demo
    gen_params = dict(max_new_tokens=60, do_sample=False, temperature=0.0, return_full_text=False)
    # try deterministic first (2 attempts), then 1 sampled attempt
    for attempt in range(3):
        if attempt == 2:
            # last-resort: enable sampling for diversity
            gen_params.update({"do_sample": True, "temperature": 0.7, "top_k":50, "top_p":0.95})
        out = generator(prompt, **gen_params)
        raw = out[0].get("generated_text", "").strip()
        cleaned = clean_and_validate(raw, prev_texts + list(self.used_arguments) )
        if cleaned:
            # record used argument text (store minimal text)
            self.used_arguments.add(cleaned)
            # keep global seen if desired by main runner
            log_event("agent_speak", {"agent": self.id, "persona": persona, "round": round_no, "text": cleaned})
            return cleaned
        # small sleep to avoid hammering local resources
        time.sleep(0.2)
    # fallback deterministic template if all fails
    fallback = f"As a {persona}: concise evidence-based caution is necessary."
    log_event("agent_speak_fallback", {"agent": self.id, "round": round_no, "text": fallback})
    return fallback
```

Note: ensure `text_generator` is accessible in scope (imported or passed).

---

# 5 — Memory: structured 3-bullet summaries (improve `MemoryNode.update`)

When you update memory, produce a 3-line summary per agent: `- Claim: ...`, `- Rebuttal: ...`, `- Question: ...` — keep each short.

Example update logic (inside `MemoryNode.update` after appending transcript):

```python
def _make_bulleted_summary(self, agent_id):
    # collect last two statements by the agent and last opposing statement
    agent_msgs = [t["text"] for t in self.transcript if t["agent"] == agent_id]
    other_agent = "AgentB" if agent_id == "AgentA" else "AgentA"
    other_msgs = [t["text"] for t in self.transcript if t["agent"] == other_agent]
    claim = agent_msgs[-1] if agent_msgs else ""
    rebuttal = other_msgs[-1] if other_msgs else ""
    # create a short question or outstanding point (trim to 25 words)
    question = "Balance safety vs innovation?" if claim and rebuttal else ""
    # shortify helper
    def short(s, w=25):
        return " ".join(s.split()[:w])
    bullets = f"- Claim: {short(claim,25)}\n- Rebuttal: {short(rebuttal,25)}\n- Question: {question}"
    self.summaries[agent_id] = bullets
```

Pass that bullets string into `Agent.speak()`.

---

# 6 — Judge: numeric + deterministic LLM rationale (optional)

Keep your weighted heuristic for numeric scores. Then generate a 1–2 sentence rationale *deterministically*:

```python
def get_judge_rationale(scores, transcript, generator=text_generator):
    prompt = f"""
You are an impartial judge. Scores: AgentA={scores['AgentA']:.2f}, AgentB={scores['AgentB']:.2f}.
Transcript: {transcript}
Task: Provide a 1-2 sentence rationale (concise) explaining who won and why. Output only the rationale.
"""
    out = generator(prompt, max_new_tokens=100, do_sample=False, temperature=0.0, return_full_text=False)
    raw = out[0].get("generated_text", "").strip()
    # take first paragraph and limit to 2 sentences
    rp = first_paragraph(raw)
    # optionally trim to two sentences:
    sentences = re.split(r'(?<=[.?!])\s+', rp)
    rationale = " ".join(sentences[:2]).strip()
    return rationale
```

Log both numeric scores and rationale.

---

# 7 — Reproducible demo settings

When you record demo:

* Use `do_sample=False` and `temperature=0.0`.
* Save the entire `debate_log.txt` after the run.
* Re-run the same script once to verify same outputs.

---

# 8 — Small UX & logging polish

* Print only the cleaned text in CLI: `print(f"[Round {r}] {agent.persona}: {cleaned_text}")`
* Save `debate_log.txt` with full raw model output *and* cleaned text for audit.
* Keep the textual DAG output — it’s acceptable for the round-2 deliverable if Graphviz isn’t installed.

---

# 9 — Quick checklist to run now

1. Add global env vars snippet to `main.py`.
2. Replace pipeline init per snippet (set pad token).
3. Paste `clean_and_validate`, `first_paragraph`, `jaccard_similarity`.
4. Replace `Agent.speak` with the robust function above.
5. Improve `MemoryNode.update` to produce bullet summaries.
6. Re-run `python main.py "Should AI be regulated like medicine?"` with CPU (device=-1).
7. Verify each round prints a single short paragraph, ends with punctuation, and no extra paragraphs.

---

# Example of expected good output

```
[Round 1] Scientist: Evidence shows AI systems can produce harmful biased outcomes, so regulation similar to medicine would require rigorous testing and validation.
[Round 2] Philosopher: Regulating AI like medicine risks curbing autonomy and democratic choice; ethical frameworks should guide targeted safeguards instead.
...
[Judge] Scores: AgentA 7.5, AgentB 6.0
[Judge] Rationale: Scientist presented more evidence-based points about testing and bias, while Philosopher focused on values—so AgentA narrowly wins.
```

---

If you paste in your updated `nodes.py` now I’ll scan it and provide one short targeted change (no extra questions). Otherwise, tell me if you want the **exact full file** `nodes.py` ready-to-paste with all of these changes and I’ll produce it for you right now. Which do you want?
