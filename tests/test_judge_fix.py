#!/usr/bin/env python3
"""
Test script to verify the judge rationale fix
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.langgraph_debate import judge_node
from src.state import DebateState

# Create a mock debate state
mock_state = {
    "topic": "Should AI be regulated like medicine?",
    "persona_a": "Scientist",
    "persona_b": "Philosopher",
    "round": 8,
    "transcript": [
        {"agent": "AgentA", "persona": "Scientist", "round": 1, "text": "AI, like medicine, poses significant risks if deployed improperly. Therefore, regulation is necessary to ensure safety, efficacy, and ethical use, preventing potential harm to individuals and society."},
        {"agent": "AgentB", "persona": "Philosopher", "round": 2, "text": "AI, like medicine, can profoundly impact human well-being; thus, regulation is warranted to mitigate risks and ensure responsible development and deployment for public safety."},
        {"agent": "AgentA", "persona": "Scientist", "round": 3, "text": "AI, similar to medicine, carries potential risks of misuse and harm. Regulation is essential to ensure its safe, ethical, and effective application, safeguarding individuals and society from unintended consequences."},
        {"agent": "AgentB", "persona": "Philosopher", "round": 4, "text": "AI, like medicine, presents both immense benefits and potential harms. Therefore, regulation is necessary to strike a balance between fostering innovation and ensuring public safety by mitigating risks."},
    ],
    "seen_texts": [],
    "current_agent": "AgentA",
    "winner": None,
    "rationale": None,
    "error": None
}

print("Testing judge node with mock data...")
print("=" * 50)

try:
    result = judge_node(mock_state)
    
    print(f"Winner: {result.get('winner')}")
    print(f"Rationale: {result.get('rationale')}")
    print(f"Summary: {result.get('summary')}")
    
    # Check if rationale is now populated
    if result.get('rationale') and result.get('rationale') is not None:
        print("\n✅ SUCCESS: Rationale is now populated!")
    else:
        print("\n❌ FAILED: Rationale is still null or empty")
        
    # Check if winner is determined
    if result.get('winner'):
        print(f"✅ Winner determined: {result.get('winner')}")
    else:
        print("❌ Winner not determined")
        
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
