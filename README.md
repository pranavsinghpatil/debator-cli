# ATG Multi-Agent Debate DAG (Round 2 deliverable)

Spec: Implemented to match the assignment uploaded by the candidate. :contentReference[oaicite:1]{index=1}

## What’s included
- `main.py` — CLI debate runner (fallback runnable implementation).
- `nodes.py` — Agent, Memory, Judge logic and validation.
- `logger_util.py` — Structured log writer (writes `debate_log.txt`).
- `dag_gen.py` — Generates DAG diagram (`debate_dag.png` and `.pdf`) via Graphviz.
- `langgraph_template.py` — Template + notes for LangGraph mapping.
- `sample_run.txt` — Example of debate output for demo script.

## Requirements (fallback implementation)
- Python 3.9+
- pip packages: `graphviz`
- system: Graphviz (dot) installed

Install:
```bash
pip install graphviz

