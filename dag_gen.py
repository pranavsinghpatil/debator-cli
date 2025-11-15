# dag_gen.py
from graphviz import Digraph

def generate_dag(memory, winner, output_path="debate_dag"):
    dot = Digraph(comment="Debate DAG")
    dot.attr(rankdir='TB', splines='ortho')

    # Main nodes
    topic_text = memory.transcript[0]["text"].split(",")[0]
    if "On " in topic_text:
        topic_text = topic_text.split("On ")[1]
    dot.node('Topic', f'Topic: {topic_text}')
    dot.node('AgentA', 'AgentA (Scientist)', shape='box', style='rounded')
    dot.node('AgentB', 'AgentB (Philosopher)', shape='box', style='rounded')
    dot.node('Judge', 'Judge', shape='diamond')

    # Highlight winner
    if winner == 'AgentA':
        dot.node('AgentA', 'AgentA (Scientist)\\n**Winner**', style='filled', fillcolor='lightblue')
    elif winner == 'AgentB':
        dot.node('AgentB', 'AgentB (Philosopher)\\n**Winner**', style='filled', fillcolor='lightblue')

    # Argument nodes and edges
    with dot.subgraph(name='cluster_debate') as c:
        c.attr(label='Debate Rounds', style='rounded')
        for i, turn in enumerate(memory.transcript):
            round_num = turn['round']
            agent_id = turn['agent']
            text = turn['text']
            
            # Create a node for each argument
            arg_node_id = f'Arg_{round_num}'
            c.node(arg_node_id, f'R{round_num}: {text[len(agent_id)+4:]}', shape='note')
            
            # Edge from agent to argument
            dot.edge(agent_id, arg_node_id)
            
            # Edge from previous argument to current one to show flow
            if i > 0:
                prev_arg_node_id = f'Arg_{memory.transcript[i-1]["round"]}'
                dot.edge(prev_arg_node_id, arg_node_id)

    # Edges to Judge
    dot.edge(f'Arg_{memory.transcript[-1]["round"]}', 'Judge')

    try:
        for fmt in ['png', 'pdf']:
            dot.render(filename=output_path, format=fmt, cleanup=True, view=False)
        print(f"DAG rendered successfully: {output_path}.png / .pdf")
    except Exception as e:
        print(f"[Warning] DAG rendering skipped: {e}")
