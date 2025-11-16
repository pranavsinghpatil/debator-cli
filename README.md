# ATG Multi-Agent Debate DAG (LangGraph Implementation)

## What’s included
- `main.py` — CLI debate runner (LangGraph implementation).
- `src/nodes.py` — Utility functions (clean_and_validate, hf_generate, gemini_generate, ValidationError).
- `src/logger_util.py` — Structured log writer (writes `global_debate_log.txt` and `debate_log.txt`).
- `src/dag_gen.py` — Generates debate flow diagram (`debate_dag.png`).
- `src/state.py` — Defines the `DebateState` TypedDict for LangGraph.
- `src/langgraph_debate.py` — Contains the LangGraph workflow definition and nodes.
- `sample_run.txt` — Example of debate output for demo script.

## Requirements
- Python 3.9+
- pip packages: `langgraph`, `langgraph-checkpoint`, `google-generativeai`, `python-dotenv`, `transformers`, `torch`, `rich`, `mermaid-cli`, `playwright`

Install:
```bash
pip install -r requirements.txt
# Ensure Playwright browsers are installed for mermaid-cli
playwright install
```

## How to Run

1.  **Set up your environment:**
    ```bash
    # Clone the repository
    git clone <repository_url>
    cd debator-cli

    # Create and activate a virtual environment
    python -m venv venv
    # On Windows
    .\venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate

    # Install dependencies
    pip install -r requirements.txt

    # Install Playwright browsers (required by mermaid-cli for DAG generation)
    playwright install
    ```

2.  **Configure Gemini API Key:**
    Create a `.env` file in the root directory of the project and add your Gemini API key:
    ```
    GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
    ```

3.  **Run the Debate:**
    ```bash
    python app.py
    ```
    The CLI will prompt you to enter a debate topic and personas.

## LangGraph Architecture

The debate system is built using LangGraph's `StateGraph` to manage the flow and state of the debate.

### State Schema (`src/state.py`)

The `DebateState` is a `TypedDict` that defines the structure of the state passed between nodes:

```python
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
```

### Graph Structure (`src/langgraph_debate.py`)

The `create_debate_graph` function defines the workflow with the following nodes and edges:

-   **Nodes:**
    -   `user_input`: Initializes the debate state with the topic and personas.
    -   `agent_a`: Generates an argument for Agent A.
    -   `agent_b`: Generates an argument for Agent B.
    -   `validator`: Validates the generated argument (checks for repeats, length).
    -   `judge`: Reviews the debate transcript, scores agents, and declares a winner with rationale.

-   **Edges:**
    -   `user_input` -> `agent_a`: Starts the debate with Agent A.
    -   `agent_a` -> `validator`: After Agent A speaks, validate the argument.
    -   `agent_b` -> `validator`: After Agent B speaks, validate the argument.
    -   **Conditional Edge from `validator`:**
        -   If `state["error"]` is present, the debate `END`s due to a validation error.
        -   If `state["round"] == 8`, the debate proceeds to the `judge` node.
        -   Otherwise, it alternates between `agent_a` and `agent_b` based on `state["current_agent"]`.
    -   `judge` -> `END`: The debate concludes after the judge's verdict.

The graph ensures 8 alternating rounds of arguments, followed by a judgment. A DAG visualization of the LangGraph architecture is generated at the end of each debate run.