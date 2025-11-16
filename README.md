# Multi-Agent Debate DAG using LangGraph

A sophisticated debate simulation system built with LangGraph where AI agents engage in structured arguments, complete with memory management, turn validation, and automated judging.

## 🎯 Project Overview

This system implements a technical assignment for creating a multi-agent debate workflow using LangGraph. Two AI agents with different professional personas engage in an 8-round structured debate on a user-defined topic, with comprehensive memory management and automated judgment.

## ✨ Key Features

- **Multi-Agent Architecture**: AgentA (Scientist) vs AgentB (Philosopher) with distinct personas
- **Structured Debate Flow**: Exactly 8 rounds with alternating turns (4 arguments per agent)
- **Memory Management**: Intelligent memory node that tracks and summarizes debate history
- **Turn Validation**: Ensures agents only speak in their assigned turns with no repeated arguments
- **Automated Judging**: Sophisticated JudgeNode that evaluates debate quality and declares winners
- **Comprehensive Logging**: Full state transitions and debate interactions logged
- **DAG Visualization**: Auto-generated Mermaid diagrams of the LangGraph architecture
- **CLI Interface**: Clean command-line interface for user interaction

## 🏗️ System Architecture

### Workflow Nodes

1. **UserInputNode**: Accepts debate topic at runtime
2. **AgentA**: Scientist persona - argues in odd rounds (1, 3, 5, 7)
3. **AgentB**: Philosopher persona - argues in even rounds (2, 4, 6, 8)
4. **MemoryNode**: Stores and summarizes debate transcript
5. **ValidatorNode**: Ensures turn compliance and argument uniqueness
6. **JudgeNode**: Reviews entire debate and declares winner with justification

### DAG Structure

```
__start__ → user_input → agent_a → agent_b → memory → validator
                                    ↓                    ↑
                                    agent_a ←-------------+
                                    ↓
                                  judge → __end__
```

## 🚀 Installation & Setup

### Prerequisites

- Python 3.9+
- Virtual environment (recommended)

### Dependencies

```bash
# Clone the repository
git clone <repository-url>
cd debator-cli

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (required by mermaid-cli for DAG generation)
playwright install
```

### Required Packages

- `langgraph>=0.2.0` - Core workflow orchestration
- `google-generativeai==0.5.4` - Gemini API integration
- `transformers==4.57.0` - Local model fallback
- `python-dotenv==1.0.1` - Environment configuration
- `mermaid-cli==0.1.2` - DAG diagram generation
- `rich==14.2.0` - Enhanced CLI output

### Environment Setup

Create a `.env` file with your Gemini API key:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

## 🎮 Usage

### Running the Application

```bash
python app.py
```

### Example CLI Interaction

```
Enter topic for debate (default: 'Should AI be regulated like medicine?'): Should AI be regulated like medicine?

Starting debate between Scientist and Philosopher...

──────────────────────────────────────────────── Round 1 ────────────────────────────────────────────────
╭────────────────────────────────────────────── Scientist ──────────────────────────────────────────────╮
│ AI must be regulated due to high-risk applications in healthcare and finance, where algorithmic      │
│ decisions directly impact human lives and safety.                                                    │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────╯

[... debate continues through 8 rounds ...]

──────────────────────────────────────────── Judge's Verdict ────────────────────────────────────────────
╭─────────────────────────────────────────── Judge's Summary ───────────────────────────────────────────╮
│ ┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │
│ ┃ Winner               ┃ Rationale                                                                  ┃ │
│ ┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩ │
│ │ Scientist (AgentA)   │ The Scientist presented more grounded, risk-based arguments aligned        │ │
│ │                      │ with public safety principles and practical regulatory frameworks.         │ │
│ └──────────────────────┴────────────────────────────────────────────────────────────────────────────┘ │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## 📁 Project Structure

```
debator-cli/
├── app.py                 # Main CLI application entry point
├── main.py                # Debate orchestration logic
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (API keys)
├── src/                   # Core implementation modules
│   ├── nodes.py          # Agent, Memory, and Judge node definitions
│   ├── langgraph_debate.py # LangGraph workflow construction
│   ├── dag_gen.py        # DAG diagram generation
│   ├── state.py          # State management schemas
│   └── logger_util.py    # Logging utilities
├── records/               # Generated debate artifacts
│   └── [topic]/          # Topic-specific outputs
│       ├── debate_log.txt    # Full JSON log of debate
│       ├── langgraph_dag.mmd # Mermaid DAG diagram
│       ├── langgraph_dag.png # Visual DAG representation
│       └── debate_dag_dag.txt# Debate flow summary
└── README.md             # This documentation
```

## 🧠 Core Components

### LangGraph State Management

The system uses LangGraph's `StateGraph` with a comprehensive `DebateState` TypedDict:

```python
class DebateState(TypedDict):
    topic: str                          # Debate topic
    persona_a: str                      # Persona for Agent A
    persona_b: str                      # Persona for Agent B
    round: int                          # Current round number (1-8)
    transcript: List[dict]              # Full transcript of all arguments
    seen_texts: List[str]               # Seen arguments for duplicate detection
    current_agent: str                  # "AgentA" or "AgentB"
    winner: Optional[str]               # Winner determined by judge
    rationale: Optional[str]            # Judge's rationale
    error: Optional[str]                # Error message
    last_speaker: Optional[str]         # Last agent who spoke
    last_text: Optional[str]            # Last argument text
```

### Agent Implementation

Each agent is implemented with:
- **Persona-specific prompts**: Scientist focuses on evidence and safety, Philosopher on ethics and values
- **Context awareness**: Access to previous arguments and memory summaries
- **Argument validation**: Ensures unique, coherent responses using Jaccard similarity
- **Fallback mechanisms**: Local model backup when API fails

### Memory Management

The `MemoryNode` provides:
- **Transcript storage**: Complete debate history with metadata
- **Intelligent summaries**: Periodic condensation of key points
- **Context provision**: Relevant memory for each agent's turn
- **State isolation**: Agents receive only necessary context

### Judge Logic

The `JudgeNode` implements:
- **Comprehensive evaluation**: Analyzes all arguments and interactions
- **Scoring system**: Weighted keyword analysis for relevance and persuasiveness
- **Winner determination**: Logic-based verdict with detailed rationale
- **Quality assessment**: Evaluates argument strength, coherence, and persuasiveness

### Validation System

The `ValidatorNode` ensures:
- **Turn compliance**: Agents only speak in assigned rounds
- **Argument uniqueness**: Prevents repetition using similarity analysis (>0.98 threshold)
- **Logical flow**: Maintains debate coherence
- **Error handling**: Graceful recovery from validation failures

## 📊 Output Artifacts

### Debate Logs
- **Comprehensive JSON logging**: All state transitions and node interactions
- **Timestamped events**: Complete audit trail of debate execution
- **Error tracking**: Detailed error reporting and recovery

### DAG Diagrams
- **Mermaid source**: Editable graph definitions showing node connections
- **PNG visualization**: High-quality diagram images
- **Flow documentation**: Clear workflow representation with conditional routing

### Debate Records
- **Topic-specific folders**: Organized by debate topic
- **Complete transcripts**: Full argument history with round metadata
- **Judgment summaries**: Winner declarations with detailed rationale

## 🔧 Technical Implementation

### LangGraph Integration

The system leverages LangGraph for:
- **State management**: Centralized state schema with type safety
- **Workflow orchestration**: Reliable node execution and transitions
- **Conditional routing**: Dynamic flow control based on debate state
- **Error handling**: Robust error recovery and logging
- **Checkpointing**: State persistence and recovery

### AI Model Integration

- **Primary: Gemini API**: Advanced reasoning capabilities with `gemini-2.0-flash`
- **Fallback: Local Transformers**: Offline capability with FLAN-T5 base model
- **Prompt engineering**: Optimized for debate-specific tasks with persona guidance
- **Response validation**: Quality filtering and coherence checks

### Memory Architecture

- **Structured state**: Pydantic models for type safety
- **Efficient storage**: Optimized transcript and summary management
- **Context extraction**: Intelligent memory retrieval for agents
- **Scalable design**: Handles extended debates efficiently

## 🎯 Task Objectives Completed

✅ **LangGraph DAG Correctness**: Fully functional StateGraph with proper state management and conditional routing  
✅ **Debate Round Control**: Exact 8-round structure with alternating turns (AgentA: 1,3,5,7; AgentB: 2,4,6,8)  
✅ **Memory Handling**: Comprehensive transcript and summary management with intelligent context provision  
✅ **Judge Logic**: Sophisticated evaluation with scoring system and detailed justification  
✅ **State Validation**: Turn compliance, argument uniqueness, and logical coherence enforcement  
✅ **CLI Interface**: Clean, user-friendly command-line interaction with rich formatting  
✅ **Comprehensive Logging**: Full JSON logging of all state transitions and node executions  
✅ **DAG Visualization**: Auto-generated Mermaid diagrams with PNG export capability  

## 🐛 Troubleshooting

### Common Issues

1. **API Key Errors**: Ensure GEMINI_API_KEY is properly set in `.env`
2. **Memory Issues**: Check available disk space for large debate logs
3. **Import Errors**: Verify all dependencies are installed correctly
4. **DAG Generation**: Ensure mermaid-cli is installed for diagram generation
5. **Syntax Errors**: Fixed f-string backslash issues in nodes.py

### Debug Mode

Enable verbose logging by setting environment variable:
```bash
export DEBUG=true
python app.py
```

## 📈 Performance Considerations

- **API Rate Limits**: Built-in retry mechanisms and exponential backoff
- **Memory Usage**: Efficient transcript storage with periodic cleanup
- **Response Time**: Optimized prompt engineering for faster AI responses
- **Error Recovery**: Robust fallback to local models when needed

## 🔮 Future Enhancements

- **Multi-persona support**: More than 2 debaters with different roles
- **Real-time interface**: Web-based debate visualization
- **Custom personas**: User-defined agent characteristics
- **Debate analytics**: Advanced metrics and insights
- **Tournament mode**: Multi-round debate competitions

## 📄 License

This project is submitted as a technical assignment and demonstrates advanced LangGraph implementation and AI agent orchestration capabilities.

## 🤝 Contributing

For issues, improvements, or questions regarding this implementation, please refer to the project documentation and code comments for detailed explanations of the architecture and design decisions.
