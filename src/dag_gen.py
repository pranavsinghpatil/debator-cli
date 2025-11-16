# dag_gen.py
from src.state import DebateState
import asyncio
from mermaid_cli import render_mermaid

def generate_debate_artifacts(final_state: DebateState, output_path="debate_dag"):
    # Handle case where final_state might be incomplete or empty
    if not final_state or not final_state.get("transcript"):
        print(f"[Warning] No transcript found in final state. Cannot generate DAG.")
        return
    
    memory_transcript = final_state.get("transcript", [])
    winner = final_state.get("winner", "Tie")
    persona_a = final_state.get("persona_a", "AgentA")
    persona_b = final_state.get("persona_b", "AgentB")
    rationale = final_state.get("rationale", "No rationale provided.")
    topic = final_state.get("topic", "Unknown Topic")

    mermaid_code = "graph LR\n"
    mermaid_code += f'    Topic["Topic: {topic}"]\n'
    mermaid_code += f'    AgentA["{persona_a} (AgentA)"]\n'
    mermaid_code += f'    AgentB["{persona_b} (AgentB)"]\n'
    mermaid_code += f'    Judge["Judge"]\n'

    if winner == 'AgentA':
        mermaid_code += '    style AgentA fill:#8fbc8f,stroke:#333,stroke-width:4px\n'
    elif winner == 'AgentB':
        mermaid_code += '    style AgentB fill:#f0e68c,stroke:#333,stroke-width:4px\n'

    for i, turn in enumerate(memory_transcript):
        round_num = turn['round']
        agent_id = turn['agent']
        text = turn['text']
        persona = turn['persona']
        
        # Sanitize text for Mermaid
        sanitized_text = text.replace('"', "'").replace('\n', ' ').replace(';', ',')
        if len(sanitized_text) > 100:
            sanitized_text = sanitized_text[:97] + "..."

        arg_node_id = f'Arg_{round_num}_{agent_id}'
        mermaid_code += f'    {arg_node_id}["R{round_num} ({persona}): {sanitized_text}"]\n'
        mermaid_code += f'    {agent_id} --> {arg_node_id}\n'
        if i > 0:
            prev_turn = memory_transcript[i-1]
            prev_arg_node_id = f'Arg_{prev_turn["round"]}_{prev_turn["agent"]}'
            mermaid_code += f'    {prev_arg_node_id} --> {arg_node_id}\n'

    last_turn = memory_transcript[-1]
    mermaid_code += f'    Arg_{last_turn["round"]}_{last_turn["agent"]} --> Judge\n'

    try:
        # Render the Mermaid diagram
        async def render():
            _, _, png_data = await render_mermaid(
                definition=mermaid_code,
                output_format="png",
                mermaid_config={"scale": 2}
            )
            with open(f"{output_path}.png", "wb") as f:
                f.write(png_data)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(render())
        print(f"Data and logs recorded and saved to records folders.")
    except Exception as e:
        print(f"[Warning] DAG rendering skipped: {e}")

    # Save the debate flow and summary to a text file
    try:
        with open(f"{output_path}_dag.txt", "w") as f:
            f.write(f"Debate Topic: '{topic}'\n\n")
            f.write("--- Debate Flow ---\n")
            for turn in memory_transcript:
                f.write(f"[Round {turn['round']}] -> {turn['persona']} ({turn['agent']})\n")
                f.write(f"  '{turn['text']}'\n")
            f.write("\n--- Judgment ---\n")
            f.write(f"Winner: {winner}\n")
            f.write(f"Rationale: {rationale}\n")
    except Exception as e:
        print(f"[Warning] Debate flow saving failed: {e}")

