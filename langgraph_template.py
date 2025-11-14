# langgraph_template.py
"""
PSEUDO-TEMPLATE: depends on the LangGraph SDK import names.
This file explains where to place the actual node code if you re-implement with LangGraph.

- UserInputNode: takes CLI topic and emits to AgentA
- AgentANode, AgentBNode: wrap Agent.speak (call LLM)
- MemoryNode: wrap MemoryNode.update + get_memory_for
- ValidatorNode: call validate_turn
- JudgeNode: wrap JudgeNode.review

Each node should log via logger_util.log_event(...) and persist state in LangGraph memory store.
"""
# This file is a template only. Replace with real LangGraph node decorators / classes.
